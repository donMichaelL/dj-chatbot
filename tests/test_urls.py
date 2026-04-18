from __future__ import annotations

from django.urls import resolve, reverse

from dj_chatbot.views import ChatHistoryView, ChatView


class TestUrls:
    def test_send_url_resolves_to_chatview(self):
        """Test that /chat/send/ resolves to ChatView."""
        match = resolve("/chat/send/")
        assert match.func.view_class is ChatView  # type: ignore[attr-defined]

    def test_history_url_resolves_to_history_view(self):
        """Test that /chat/history/ resolves to ChatHistoryView."""
        match = resolve("/chat/history/")
        assert match.func.view_class is ChatHistoryView  # type: ignore[attr-defined]

    def test_send_url_reverses_by_name(self):
        """Test that dj_chatbot_send URL name reverses back to the send path."""
        assert reverse("dj_chatbot_send") == "/chat/send/"

    def test_history_url_reverses_by_name(self):
        """Test that dj_chatbot_history URL name reverses back to the history path."""
        assert reverse("dj_chatbot_history") == "/chat/history/"
