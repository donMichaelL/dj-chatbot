from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from dj_chatbot.base_views import BaseChatView
from dj_chatbot.models import Conversation, Message
from dj_chatbot.views import ChatHistoryView


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def anonymous_request(factory):
    request = factory.post("/chat/send/", {"message": "hello"})
    request.user = MagicMock(is_authenticated=False)
    return request


@pytest.fixture
def invalid_request(factory):
    request = factory.post("/chat/send/", {"message": ""})
    request.user = MagicMock(is_authenticated=False)
    return request


@pytest.fixture
def history_request(factory):
    request = factory.get("/chat/history/")
    request.user = MagicMock(is_authenticated=False)
    return request


@pytest.fixture
async def conversation_with_messages(db):
    user = await get_user_model().objects.acreate(username="bob", password="x")  # noqa: S106
    conversation = await Conversation.objects.acreate(thread_id=f"user-{user.pk}")
    await Message.objects.acreate(conversation=conversation, role=Message.Role.USER, content="hi")
    await Message.objects.acreate(conversation=conversation, role=Message.Role.ASSISTANT, content="hello")
    return user, conversation


@pytest.fixture
def fake_agent():
    """An agent whose astream yields two token chunks then stops."""

    async def astream(*args, **kwargs):
        for content in ["Hello", " world"]:
            chunk = MagicMock(content=content)
            yield chunk, None

    agent = MagicMock()
    agent.astream = astream
    return agent


class ConcreteView(BaseChatView):
    """Minimal subclass for testing — bypasses build_agent."""

    def __init__(self, agent: object, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._preset_agent = agent

    def get_agent(self) -> object:
        return self._preset_agent


@pytest.mark.django_db(transaction=True)
class TestBaseChatViewPost:
    async def test_invalid_form_returns_400(self, invalid_request, fake_agent):
        """Test that an empty message returns HTTP 400."""
        view = ConcreteView(agent=fake_agent)
        response = await view.post(invalid_request)
        assert response.status_code == 400

    async def test_valid_form_returns_streaming_response(self, anonymous_request, fake_agent):
        """Test that a valid form produces a StreamingHttpResponse with text/event-stream."""
        view = ConcreteView(agent=fake_agent)
        response = await view.post(anonymous_request)
        assert response.status_code == 200
        assert response["Content-Type"] == "text/event-stream"

    async def test_streams_tokens_as_sse_frames(self, anonymous_request, fake_agent):
        """Test that streamed tokens arrive as SSE frames ending with [DONE]."""
        view = ConcreteView(agent=fake_agent)
        response = await view.post(anonymous_request)

        body = b""
        async for chunk in response.streaming_content:  # type: ignore[attr-defined]
            body += chunk
        text = body.decode()

        assert 'data: {"token": "Hello"}' in text
        assert 'data: {"token": " world"}' in text
        assert "data: [DONE]" in text

    async def test_persists_user_and_assistant_messages(self, anonymous_request, fake_agent):
        """Test that both the user message and the assembled assistant reply are saved to the DB."""
        view = ConcreteView(agent=fake_agent)
        response = await view.post(anonymous_request)

        async for _ in response.streaming_content:  # type: ignore[attr-defined]
            pass

        messages = [{"role": m.role, "content": m.content} async for m in Message.objects.order_by("created_at")]
        assert messages == [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "Hello world"},
        ]

    async def test_handles_agent_exception_with_error_chunk(self, anonymous_request):
        """Test that exceptions from the agent produce a single error SSE frame."""

        async def failing_astream(*args, **kwargs):
            yield MagicMock(content="partial"), None
            raise RuntimeError("boom")

        agent = MagicMock()
        agent.astream = failing_astream
        view = ConcreteView(agent=agent)

        response = await view.post(anonymous_request)
        body = b""
        async for chunk in response.streaming_content:  # type: ignore[attr-defined]
            body += chunk
        text = body.decode()

        assert "error" in text
        assert "[DONE]" in text


@pytest.mark.django_db(transaction=True)
class TestChatHistoryView:
    async def test_empty_when_no_messages(self, history_request):
        """Test that an empty thread returns an empty messages list."""
        view = ChatHistoryView()
        response = await view.get(history_request)
        assert response.status_code == 200
        assert json.loads(response.content) == {"messages": []}

    async def test_returns_persisted_messages(self, factory, conversation_with_messages):
        """Test that persisted messages for the current thread are returned."""
        user, _ = conversation_with_messages
        request = factory.get("/chat/history/")
        request.user = user

        view = ChatHistoryView()
        response = await view.get(request)
        assert json.loads(response.content) == {
            "messages": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ]
        }
