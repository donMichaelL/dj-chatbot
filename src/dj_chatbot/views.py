from __future__ import annotations

from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver

from dj_chatbot.base_views import BaseChatView
from dj_chatbot.mixins import ChatMixin

if TYPE_CHECKING:
    from django.http import HttpRequest
    from langchain.agents.middleware import AgentMiddleware
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph


class ChatView(BaseChatView):
    """Default chat view. Reads config from class attributes or settings."""

    system_prompt: str | None = None
    model: str | None = None

    def get_system_prompt(self) -> str:
        """Return the system prompt for the agent."""
        if self.system_prompt is not None:
            return self.system_prompt
        return getattr(settings, "DJ_CHATBOT_SYSTEM_PROMPT", "You are a helpful assistant.")

    def get_model(self) -> str:
        """Return the model identifier passed to `init_chat_model`.

        Format is `"<provider>:<model>"` — e.g. `openai:gpt-4o-mini` or
        `anthropic:claude-3-5-sonnet-latest`.

        See Also:
            [Available chat providers](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model).
        """
        if self.model is not None:
            return self.model
        return settings.DJ_CHATBOT_MODEL  # type: ignore[misc,no-any-return]

    def build_model(self) -> BaseChatModel:
        """Instantiate the chat model via `init_chat_model`.

        Override to return a custom provider instance (e.g. `ChatOpenAI`,
        `ChatAnthropic`). Must return a subclass of `BaseChatModel`.

        See Also:
            [Chat Model Integrations](https://docs.langchain.com/oss/python/integrations/chat).
        """
        return init_chat_model(
            model=self.get_model(),
            api_key=settings.DJ_CHATBOT_API_KEY,  # type: ignore[misc]
        )

    def build_tools(self) -> list[BaseTool]:
        """Return the tools the agent can call.

        Each item must be an instance of `BaseTool` — use the `@tool`
        decorator or subclass `BaseTool` directly. Returns an empty list by
        default.

        See Also:
            [Custom tools](https://docs.langchain.com/oss/python/langchain/tools).
        """
        return []

    def build_memory(self) -> BaseCheckpointSaver | None:
        """Return the checkpointer that persists agent state between turns.

        Defaults to an in-process `MemorySaver` (lost on restart). For
        production, override with a persistent backend such as `PostgresSaver`
        or `SqliteSaver`.

        See Also:
            [LangGraph persistence](https://docs.langchain.com/oss/python/langchain/short-term-memory).
        """
        return MemorySaver()

    def build_middleware(self) -> list[AgentMiddleware]:
        """Return LangChain agent middleware (not Django middleware).

        Middleware hooks into the agent loop to trim messages, enforce call
        limits, summarize history, etc. Empty by default.

        See Also:
            [Agent middleware](https://docs.langchain.com/oss/python/langchain/middleware/overview).
        """
        return []

    def build_agent(self) -> CompiledStateGraph:
        """Compose the LangGraph agent from the `build_*` hooks.

        Returns a `CompiledStateGraph` ready to be invoked via `astream`.
        Override to replace `create_agent` entirely (e.g. to build a custom
        graph with `StateGraph`).

        See Also:
            [Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
        """
        return create_agent(
            model=self.build_model(),
            tools=self.build_tools(),
            system_prompt=self.get_system_prompt(),
            checkpointer=self.build_memory(),
            middleware=self.build_middleware(),
        )


class ChatHistoryView(ChatMixin, View):
    """Return the current thread's message history as JSON."""

    async def get(self, request: HttpRequest, *args: object, **kwargs: object) -> JsonResponse:
        """Handle GET requests by returning the persisted messages for the thread."""
        thread_id = self.get_thread_id(request)
        messages = await sync_to_async(self.get_messages)(thread_id)
        return JsonResponse({"messages": messages})
