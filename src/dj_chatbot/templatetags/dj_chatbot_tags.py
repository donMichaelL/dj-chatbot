from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django import template
from django.urls import reverse

if TYPE_CHECKING:
    from django.template import Context

register = template.Library()


@register.inclusion_tag("dj_chatbot/widget.html", takes_context=True)
def chatbot_widget(
    context: Context,
    url_name: str = "dj_chatbot_send",
    history_url_name: str = "dj_chatbot_history",
    title: str = "Chat",
    welcome_message: str = "",
) -> dict[str, Any]:
    return {
        "endpoint": reverse(url_name),
        "history_endpoint": reverse(history_url_name),
        "title": title,
        "welcome_message": welcome_message,
        "csrf_token": context.get("csrf_token", ""),
    }
