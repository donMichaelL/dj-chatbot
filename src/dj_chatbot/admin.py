from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Conversation, Message

if TYPE_CHECKING:
    from django.utils.safestring import SafeString


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ["role", "content", "created_at"]
    readonly_fields = ["role", "content", "created_at"]
    ordering = ["created_at"]
    show_change_link = True


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["__str__", "thread_id", "user", "created_at", "updated_at"]
    list_filter = ["created_at", "user"]
    search_fields = ["thread_id", "title"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["role", "short_content", "conversation_link", "created_at"]
    list_filter = [
        ("conversation", admin.RelatedOnlyFieldListFilter),
        "role",
        "created_at",
    ]
    search_fields = ["content", "conversation__thread_id"]
    readonly_fields = ["id", "created_at"]

    @admin.display(description="Content")
    def short_content(self, obj: Message) -> str:
        return obj.content[:80] if obj.content else ""

    @admin.display(description="Conversation", ordering="conversation__id")
    def conversation_link(self, obj: Message) -> SafeString:
        url = reverse("admin:dj_chatbot_conversation_change", args=[obj.conversation_id])
        return format_html('<a href="{}">{}</a>', url, obj.conversation_id)
