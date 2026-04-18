from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, ClassVar

from langchain_core.messages import HumanMessage

from dj_chatbot.forms import MessageForm
from dj_chatbot.models import Conversation, Message

if TYPE_CHECKING:
    from django.http import HttpRequest
    from django.http.response import HttpResponseBase
    from langchain_core.runnables import Runnable


class ChatMixin:
    """Building blocks for wiring an agent into a Django view.

    A *thread* here means a **conversation thread** — the chronological
    exchange of messages between one user and the agent. It has nothing to
    do with OS threads or async concurrency. Each thread is identified by
    a `thread_id` string that groups its messages together across requests.

    The mixin provides ready-to-use helpers for the common chatbot plumbing:

    - Conversation thread identification for authenticated and anonymous users
    - Cookie persistence of the conversation thread ID for anonymous visitors
    - Conversation and Message persistence
    - Form validation and agent input shaping
    - Class-level caching of the built agent

    Attributes:
        form_class: Form used to validate incoming messages.
        _agent: Class-level cache for the built agent. Shared across all
            requests of the same view class.
    """

    form_class: ClassVar[type[MessageForm]] = MessageForm
    _agent: ClassVar[Runnable[Any, Any] | None] = None

    def build_agent(self) -> Runnable[Any, Any]:
        """Build and return the agent used by this view.

        This is the primary hook subclasses must implement. The returned
        Runnable is cached on the class on first call, so building is a
        one-time cost per view class.

        Raises:
            NotImplementedError: Always, unless overridden by a subclass.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement build_agent()")

    def get_agent(self) -> Runnable[Any, Any]:
        """Return the cached agent, calling `build_agent` on first access."""
        cls = type(self)
        if cls._agent is None:
            cls._agent = self.build_agent()
        return cls._agent

    def get_thread_id(self, request: HttpRequest) -> str:
        """Return the thread ID for the current request.

        For authenticated users, the ID is derived from their primary key
        so conversations persist across browsers and devices. For anonymous
        users, the ID is read from the `dj_chatbot_thread` cookie or
        generated fresh.
        """
        if request.user.is_authenticated:
            return f"user-{request.user.pk}"
        return request.COOKIES.get("dj_chatbot_thread") or f"anon-{uuid.uuid4()}"

    def persist_thread_id(self, request: HttpRequest, response: HttpResponseBase, thread_id: str) -> None:
        """Write the thread ID cookie on the response for anonymous users.

        Authenticated users are skipped since their thread ID is tied to
        their user primary key and doesn't need a cookie.
        """
        if request.user.is_authenticated:
            return
        if "dj_chatbot_thread" not in request.COOKIES:
            response.set_cookie("dj_chatbot_thread", thread_id)

    def get_or_create_conversation(self, request: HttpRequest, thread_id: str) -> Conversation:
        """Return the Conversation for `thread_id`, creating it if missing."""
        user = request.user if request.user.is_authenticated else None
        conversation, _ = Conversation.objects.get_or_create(
            thread_id=thread_id,
            defaults={"user": user},
        )
        return conversation

    def create_message(
        self,
        conversation: Conversation,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """Persist a new Message on the given conversation."""
        return Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            metadata=metadata or {},
        )

    def get_messages(self, thread_id: str) -> list[dict[str, Any]]:
        """Return the user/assistant message history for a thread as dicts.

        System and tool messages are filtered out — this method is intended
        for rendering the chat UI, not for agent state reconstruction.
        """
        return [
            dict(row)
            for row in Message.objects.filter(
                conversation__thread_id=thread_id,
                role__in=[Message.Role.USER, Message.Role.ASSISTANT],
            ).values("role", "content")
        ]

    def get_form(self, request: HttpRequest) -> MessageForm:
        """Return a bound form instance for the current request."""
        return self.form_class(request.POST)

    def get_agent_input(self, form: MessageForm) -> dict[str, Any]:
        """Build the input dict passed to the agent's invoke/stream call."""
        return {"messages": [HumanMessage(content=form.cleaned_data["message"])]}
