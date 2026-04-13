from __future__ import annotations

import pytest

from dj_chatbot.models import Conversation, Message


@pytest.fixture
def conversation():
    return Conversation.objects.create(thread_id="thread-1", title="Test Chat")


@pytest.fixture
def conversation_no_title():
    return Conversation.objects.create(thread_id="thread-2")


@pytest.fixture
def user_message(conversation):
    return Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content="Hello, how are you?",
    )


@pytest.fixture
def assistant_message(conversation):
    return Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content="I'm doing well, thanks for asking!",
    )


@pytest.mark.django_db
class TestConversation:
    def test_create(self, conversation):
        assert conversation.thread_id == "thread-1"
        assert conversation.title == "Test Chat"

    def test_str_with_title(self, conversation):
        assert str(conversation) == "Test Chat"

    def test_str_without_title(self, conversation_no_title):
        assert str(conversation_no_title) == f"Conversation {conversation_no_title.id}"

    def test_ordering(self, conversation, conversation_no_title):
        results = list(Conversation.objects.all())
        assert results[0].updated_at >= results[1].updated_at

    def test_default_title_is_empty(self, conversation_no_title):
        assert conversation_no_title.title == ""


@pytest.mark.django_db
class TestMessage:
    def test_create(self, user_message, conversation):
        assert user_message.conversation == conversation
        assert user_message.role == Message.Role.USER
        assert user_message.content == "Hello, how are you?"

    def test_str(self, user_message):
        assert str(user_message) == f"Message: {user_message.id}"

    def test_default_metadata(self, user_message):
        assert user_message.metadata == {}

    def test_ordering(self, user_message, assistant_message):
        messages = list(Message.objects.all())
        assert messages[0].created_at <= messages[1].created_at

    def test_role_choices_count(self):
        assert len(Message.Role.choices) == 4
