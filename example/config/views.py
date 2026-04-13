from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from dj_chatbot.views import ChatView


class SupportChatView(ChatView):
    """Demonstrates overriding `build_model` to return a custom `BaseChatModel` instance."""

    system_prompt = "You are a concise support assistant. Keep answers short and friendly."

    def build_model(self):
        return ChatOpenAI(
            model="gpt-5-mini",
            temperature=0.2,
            api_key=settings.DJ_CHATBOT_API_KEY,
        )


@tool
async def list_users() -> str:
    """List all usernames currently registered in the Django auth system."""
    user_model = get_user_model()
    usernames = [name async for name in user_model.objects.values_list("username", flat=True)]
    return ", ".join(usernames) if usernames else "No users registered."


class UsersChatView(ChatView):
    """Demonstrates overriding `build_tools` to expose a Django-backed tool to the agent."""

    system_prompt = (
        "You are an admin assistant. Use the `list_users` tool to answer questions about "
        "registered users. Do not guess — always call the tool."
    )

    def build_tools(self):
        return [list_users]
