from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory
from langchain_core.messages import HumanMessage

from dj_chatbot.mixins import ChatMixin
from dj_chatbot.models import Conversation, Message


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="alice", password="pw")  # noqa: S106


@pytest.fixture
def anonymous_request(factory):
    request = factory.get("/")
    request.user = MagicMock(is_authenticated=False)
    return request


@pytest.fixture
def authenticated_request(factory, user):
    request = factory.get("/")
    request.user = user
    return request


@pytest.fixture
def mixin():
    return ChatMixin()


class TestGetThreadId:
    def test_authenticated_uses_user_pk(self, mixin, authenticated_request, user):
        """Test that authenticated users get a thread ID derived from their pk."""
        assert mixin.get_thread_id(authenticated_request) == f"user-{user.pk}"

    def test_anonymous_generates_uuid_when_no_cookie(self, mixin, anonymous_request):
        """Test that anonymous users without a cookie get a fresh anon-<uuid> thread ID."""
        thread_id = mixin.get_thread_id(anonymous_request)
        assert thread_id.startswith("anon-")

    def test_anonymous_reuses_cookie(self, mixin, factory):
        """Test that anonymous users reuse the thread ID stored in their cookie."""
        request = factory.get("/")
        request.user = MagicMock(is_authenticated=False)
        request.COOKIES["dj_chatbot_thread"] = "anon-existing"
        assert mixin.get_thread_id(request) == "anon-existing"


class TestPersistThreadId:
    def test_skips_authenticated_user(self, mixin, authenticated_request):
        """Test that authenticated users don't get a cookie written."""
        response = HttpResponse()
        mixin.persist_thread_id(authenticated_request, response, "user-1")
        assert "dj_chatbot_thread" not in response.cookies

    def test_sets_cookie_for_anonymous(self, mixin, anonymous_request):
        """Test that anonymous users get the thread ID set as a cookie."""
        response = HttpResponse()
        mixin.persist_thread_id(anonymous_request, response, "anon-abc")
        assert response.cookies["dj_chatbot_thread"].value == "anon-abc"

    def test_skips_if_cookie_already_set(self, mixin, factory):
        """Test that the cookie is not overwritten if it already exists on the request."""
        request = factory.get("/")
        request.user = MagicMock(is_authenticated=False)
        request.COOKIES["dj_chatbot_thread"] = "anon-existing"
        response = HttpResponse()
        mixin.persist_thread_id(request, response, "anon-new")
        assert "dj_chatbot_thread" not in response.cookies


@pytest.mark.django_db
class TestGetOrCreateConversation:
    def test_creates_new_for_anonymous(self, mixin, anonymous_request):
        """Test that a new conversation is created for a fresh thread_id with no user."""
        conversation = mixin.get_or_create_conversation(anonymous_request, "anon-1")
        assert conversation.thread_id == "anon-1"
        assert conversation.user is None

    def test_creates_new_for_authenticated(self, mixin, authenticated_request, user):
        """Test that a new conversation is created with the user FK set for authenticated users."""
        conversation = mixin.get_or_create_conversation(authenticated_request, "user-42")
        assert conversation.user == user

    def test_returns_existing(self, mixin, anonymous_request):
        """Test that an existing conversation is reused for the same thread_id."""
        existing = Conversation.objects.create(thread_id="anon-1")
        conversation = mixin.get_or_create_conversation(anonymous_request, "anon-1")
        assert conversation.pk == existing.pk


@pytest.mark.django_db
class TestCreateMessage:
    def test_persists_message(self, mixin):
        """Test that create_message persists a new Message with the given fields."""
        conversation = Conversation.objects.create(thread_id="t-1")
        message = mixin.create_message(conversation, Message.Role.USER, "hello", {"token_count": 5})
        assert message.content == "hello"
        assert message.role == Message.Role.USER
        assert message.metadata == {"token_count": 5}

    def test_defaults_metadata_to_empty_dict(self, mixin):
        """Test that metadata defaults to an empty dict when not provided."""
        conversation = Conversation.objects.create(thread_id="t-2")
        message = mixin.create_message(conversation, Message.Role.ASSISTANT, "hi")
        assert message.metadata == {}


@pytest.mark.django_db
class TestGetMessages:
    def test_returns_user_and_assistant_only(self, mixin):
        """Test that get_messages returns user/assistant messages but excludes system/tool."""
        conversation = Conversation.objects.create(thread_id="t-3")
        Message.objects.create(conversation=conversation, role=Message.Role.USER, content="hi")
        Message.objects.create(conversation=conversation, role=Message.Role.ASSISTANT, content="hello")
        Message.objects.create(conversation=conversation, role=Message.Role.SYSTEM, content="sys")
        Message.objects.create(conversation=conversation, role=Message.Role.TOOL, content="tool")

        messages = mixin.get_messages("t-3")
        assert len(messages) == 2
        assert {m["role"] for m in messages} == {"user", "assistant"}

    def test_empty_for_unknown_thread(self, mixin):
        """Test that get_messages returns an empty list for an unknown thread_id."""
        assert mixin.get_messages("does-not-exist") == []


class TestBuildAgent:
    def test_raises_not_implemented(self, mixin):
        """Test that the base ChatMixin raises NotImplementedError for build_agent."""
        with pytest.raises(NotImplementedError):
            mixin.build_agent()


class TestGetAgent:
    def test_caches_agent(self):
        """Test that get_agent calls build_agent only once and caches the result."""

        class StubMixin(ChatMixin):
            build_count = 0

            def build_agent(self):
                StubMixin.build_count += 1
                return MagicMock(name="runnable")

        instance = StubMixin()
        first = instance.get_agent()
        second = instance.get_agent()
        assert first is second
        assert StubMixin.build_count == 1
        StubMixin._agent = None


class TestGetAgentInput:
    def test_wraps_message_as_human_message(self, mixin):
        """Test that get_agent_input wraps the form message in a HumanMessage list."""
        form = MagicMock()
        form.cleaned_data = {"message": "hello"}
        payload = mixin.get_agent_input(form)
        assert "messages" in payload
        assert len(payload["messages"]) == 1
        assert isinstance(payload["messages"][0], HumanMessage)
        assert payload["messages"][0].content == "hello"
