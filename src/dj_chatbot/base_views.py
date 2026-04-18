from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from django.http import HttpResponseBadRequest, StreamingHttpResponse
from django.views import View

from dj_chatbot.mixins import ChatMixin

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from django.http import HttpRequest
    from django.http.response import HttpResponseBase

    from dj_chatbot.forms import MessageForm

logger = logging.getLogger("dj_chatbot")


class BaseChatView(ChatMixin, View):
    """Async base view that streams agent responses as SSE."""

    async def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """Validate the form and dispatch to `form_valid` or return a 400."""
        form = self.get_form(request)
        if form.is_valid():
            return await self.form_valid(form, request)
        return HttpResponseBadRequest("Invalid message")

    async def form_valid(self, form: MessageForm, request: HttpRequest) -> StreamingHttpResponse:
        """Handle a valid form submission."""
        return await self.stream_response(form, request)

    async def stream_response(self, form: MessageForm, request: HttpRequest) -> StreamingHttpResponse:
        """Build the SSE response wrapping the agent's streamed output."""
        thread_id = self.get_thread_id(request)
        user_message = form.cleaned_data["message"]

        agent = self.get_agent()
        agent_input = self.get_agent_input(form)
        config = {"configurable": {"thread_id": thread_id}}

        response = StreamingHttpResponse(
            self._stream(agent, agent_input, config, request, thread_id, user_message),
            content_type="text/event-stream",
        )
        self.persist_thread_id(request, response, thread_id)
        return response

    async def _stream(
        self,
        agent: Any,
        agent_input: dict[str, Any],
        config: dict[str, Any],
        request: HttpRequest,
        thread_id: str,
        user_message: str,
    ) -> AsyncIterator[str]:
        """Yield SSE frames for each token and persist the final messages."""
        full_response: list[str] = []
        try:
            async for chunk, _ in agent.astream(agent_input, config, stream_mode="messages"):
                if hasattr(chunk, "content") and chunk.content:
                    full_response.append(chunk.content)
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"
        except Exception:
            logger.exception("Agent streaming error")
            yield f"data: {json.dumps({'error': 'Something went wrong. Please try again later.'})}\n\n"
        yield "data: [DONE]\n\n"

        if full_response:
            conversation = await sync_to_async(self.get_or_create_conversation)(request, thread_id)
            await sync_to_async(self.create_message)(conversation, "user", user_message)
            await sync_to_async(self.create_message)(conversation, "assistant", "".join(full_response))
