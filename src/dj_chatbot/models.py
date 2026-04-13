from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """A chat conversation grouping related messages exchanged with the agent.

    Each conversation holds an ordered sequence of [`Message`][dj_chatbot.models.Message]
    records and is identified by a stable `thread_id` used to persist and resume state
    across requests. Optionally, a conversation can be linked to a Django user.

    Attributes:
        id: Primary key. Auto-generated UUID.
        thread_id: Stable identifier used to group messages and resume agent state across requests.
        user: Optional owner of the conversation. `None` for anonymous sessions.
        title: Human-readable title. Empty by default; can be set to summarize the conversation.
        created_at: Timestamp when the conversation was first created.
        updated_at: Timestamp of the last change. Used as the default ordering key.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread_id = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="dj_chatbot_conversations",
    )
    title = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title or f"Conversation {self.id}"


class Message(models.Model):
    """A single message belonging to a [`Conversation`][dj_chatbot.models.Conversation].

    Messages capture every turn in the exchange: user input, assistant replies,
    system instructions, and tool calls. The `role` field identifies the author and
    `metadata` can store structured provider-specific payloads (token usage, tool
    arguments, etc.) without changing the schema.

    Attributes:
        id: Primary key. Auto-generated UUID.
        conversation: The conversation this message belongs to. Cascades on delete.
        role: Who authored the message — see [`Role`][dj_chatbot.models.Message.Role].
        content: Plain-text content of the message. May be empty for tool-only turns.
        metadata: Free-form JSON for provider-specific data (tool calls, token usage, etc.).
        created_at: Timestamp when the message was stored. Used for chronological ordering.
    """

    class Role(models.TextChoices):
        """Author of the message."""

        USER = "user"
        ASSISTANT = "assistant"
        SYSTEM = "system"
        TOOL = "tool"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Message: {self.id}"
