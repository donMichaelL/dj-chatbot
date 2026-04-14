from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from dj_chatbot.admin import ConversationAdmin, MessageAdmin
from dj_chatbot.models import Conversation, Message


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",  # noqa: S106
    )


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client


@pytest.fixture
def conversation(db):
    return Conversation.objects.create(thread_id="thread-1", title="Test Chat")


@pytest.fixture
def short_message(conversation):
    return Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content="Short message",
    )


@pytest.fixture
def long_message(conversation):
    return Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content="a" * 200,
    )


@pytest.mark.django_db
class TestConversationAdmin:
    def test_changelist_loads(self, admin_client, conversation):
        """Test that the conversation changelist renders and shows existing records."""
        url = reverse("admin:dj_chatbot_conversation_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert b"Test Chat" in response.content

    def test_change_view_loads(self, admin_client, conversation, short_message):
        """Test that the conversation change page renders with inline messages visible."""
        url = reverse("admin:dj_chatbot_conversation_change", args=[conversation.id])
        response = admin_client.get(url)
        assert response.status_code == 200
        assert b"Short message" in response.content

    def test_search(self, admin_client, conversation):
        """Test that searching by thread_id returns the matching conversation."""
        url = reverse("admin:dj_chatbot_conversation_changelist")
        response = admin_client.get(url, {"q": "thread-1"})
        assert response.status_code == 200
        assert b"Test Chat" in response.content


@pytest.mark.django_db
class TestMessageAdmin:
    def test_changelist_loads(self, admin_client, short_message):
        """Test that the message changelist renders and shows existing records."""
        url = reverse("admin:dj_chatbot_message_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert b"Short message" in response.content

    def test_change_view_loads(self, admin_client, short_message):
        """Test that the message change page renders for a single message."""
        url = reverse("admin:dj_chatbot_message_change", args=[short_message.id])
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_short_content_truncates(self, long_message):
        """Test that content longer than 80 chars is truncated to exactly 80 by short_content."""
        admin_instance = MessageAdmin(Message, None)  # type: ignore[arg-type]
        assert len(admin_instance.short_content(long_message)) == 80

    def test_short_content_empty(self, conversation):
        """Test that empty content returns an empty string instead of raising."""
        empty = Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content="",
        )
        admin_instance = MessageAdmin(Message, None)  # type: ignore[arg-type]
        assert admin_instance.short_content(empty) == ""

    def test_conversation_link(self, short_message):
        """Test that conversation_link renders an anchor pointing to the parent conversation."""
        admin_instance = MessageAdmin(Message, None)  # type: ignore[arg-type]
        html = admin_instance.conversation_link(short_message)
        assert str(short_message.conversation_id) in html
        assert "<a href=" in html

    def test_filter_by_role(self, admin_client, short_message, long_message):
        """Test that filtering the changelist by role returns the matching messages."""
        url = reverse("admin:dj_chatbot_message_changelist")
        response = admin_client.get(url, {"role__exact": "user"})
        assert response.status_code == 200
        assert b"Short message" in response.content


@pytest.mark.django_db
class TestAdminRegistration:
    def test_conversation_registered(self):
        """Test that Conversation is registered with ConversationAdmin on the default site."""
        from django.contrib import admin as django_admin

        assert django_admin.site.is_registered(Conversation)
        assert isinstance(django_admin.site._registry[Conversation], ConversationAdmin)

    def test_message_registered(self):
        """Test that Message is registered with MessageAdmin on the default site."""
        from django.contrib import admin as django_admin

        assert django_admin.site.is_registered(Message)
        assert isinstance(django_admin.site._registry[Message], MessageAdmin)
