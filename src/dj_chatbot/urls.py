from __future__ import annotations

from django.urls import path

from dj_chatbot.views import ChatHistoryView, ChatView

urlpatterns = [
    path("send/", ChatView.as_view(), name="dj_chatbot_send"),
    path("history/", ChatHistoryView.as_view(), name="dj_chatbot_history"),
]
