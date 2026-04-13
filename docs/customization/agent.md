# Customizing the Agent

[`ChatView`](../api/views.md#dj_chatbot.views.ChatView) is focused on the agentic part of the view and is meant to be subclassed for customization. It inherits from [`BaseChatView`](../api/base_views.md#dj_chatbot.base_views.BaseChatView), which handles response streaming and delegates conversation plumbing to [`ChatMixin`](../api/mixins.md#dj_chatbot.mixins.ChatMixin). Each agent's building block — the model, the tools, the system prompt, the memory backend, and the middleware — can be overridden. The default agent is built with LangChain's [`create_agent`](https://reference.langchain.com/python/langchain/agents/create_agent), but even that can be replaced entirely with a more complex [`graph`](https://docs.langchain.com/oss/python/langgraph/workflows-agents).

Simple usage:
```python
# myapp/views.py
from dj_chatbot.views import ChatView


class SupportChatView(ChatView):
    system_prompt = "You are a support assistant. Keep answers concise, friendly, and focused on the user's question."
    model = "anthropic:claude-3-5-sonnet-latest"
```

Register your view in `urls.py`:

```python
# urls.py
from django.urls import path
from myapp.views import SupportChatView

urlpatterns = [
    path("support/send/", SupportChatView.as_view(), name="support_send"),
]
```

Point the widget to the correct url:

```django
{% load dj_chatbot_tags %}
{% chatbot_widget url_name="support_send" %}
```

!!! note "Agent is cached per class"

    The agent and all its building blocks are created **once** and reused on every request — so all the build hooks below are called only once. Don't read request state inside them.

## System prompt

Set [`system_prompt`](../api/views.md#dj_chatbot.views.ChatView.system_prompt).

```python
class SupportChatView(ChatView):
    system_prompt = "You are a support assistant. Keep answers concise, friendly, and focused on the user's question."
```

## Model

Set [`model`](../api/views.md#dj_chatbot.views.ChatView.model) to any identifier accepted by LangChain's [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model). To bypass `init_chat_model` entirely and return your own [`BaseChatModel`](https://reference.langchain.com/python/langchain_core/language_models/chat_models/BaseChatModel) instance, override [`build_model`](../api/views.md#dj_chatbot.views.ChatView.build_model):

```python
from langchain_openai import ChatOpenAI


class SupportChatView(ChatView):
    def build_model(self):
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
```

## Tools

Override [`build_tools`](../api/views.md#dj_chatbot.views.ChatView.build_tools) to return a list of LangChain [`BaseTool`](https://reference.langchain.com/python/langchain_core/tools/BaseTool) instances.

```python
from langchain_core.tools import tool


@tool
def get_order_status(order_id: str) -> str:
    """Look up an order by ID."""
    return f"Order {order_id} is in transit."


class SupportChatView(ChatView):
    def build_tools(self):
        return [get_order_status]
```

See [LangChain's custom tools guide](https://docs.langchain.com/oss/python/langchain/tools) for more patterns.

## Memory

Override [`build_memory`](../api/views.md#dj_chatbot.views.ChatView.build_memory) to swap the checkpointer. The default [`MemorySaver`](https://reference.langchain.com/python/langgraph/checkpoint/memory/MemorySaver) is in-process and lost on restart — use a persistent backend in production:

```python
from langgraph.checkpoint.postgres import PostgresSaver


class SupportChatView(ChatView):
    def build_memory(self):
        return PostgresSaver.from_conn_string("postgresql://...")
```

Return `None` to run without persistence at all. See [LangGraph persistence](https://docs.langchain.com/oss/python/langchain/short-term-memory) for the full list of checkpointer backends.

## Middleware

Override [`build_middleware`](../api/views.md#dj_chatbot.views.ChatView.build_middleware) to return a list of LangChain agent middleware (not Django middleware) — hooks into the agent loop to trim messages, enforce call limits, summarize history, etc:

```python
from langchain.agents.middleware import SummarizationMiddleware


class SupportChatView(ChatView):
    def build_middleware(self):
        return [SummarizationMiddleware(max_tokens=4000)]
```

See [Agent middleware](https://docs.langchain.com/oss/python/langchain/middleware/overview) for the full list of built-in middleware.

## Replacing the agent entirely

For full control, override [`build_agent`](../api/views.md#dj_chatbot.views.ChatView.build_agent) and return any [`CompiledStateGraph`](https://reference.langchain.com/python/langgraph/graph/state/CompiledStateGraph) — useful when you want a custom [`StateGraph`](https://reference.langchain.com/python/langgraph/graph/state/StateGraph) instead of [`create_agent`](https://reference.langchain.com/python/langchain/agents/create_agent):

```python
from langgraph.graph import StateGraph


class CustomChatView(ChatView):
    def build_agent(self):
        graph = StateGraph(...)
        # ... add nodes, edges, etc.
        return graph.compile(checkpointer=self.build_memory())
```

See [Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) for the graph-building patterns.
