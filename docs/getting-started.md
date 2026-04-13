# Getting Started

## Requirements

- Python 3.12+
- Django 4.2+
- An [ASGI](https://docs.djangoproject.com/en/stable/howto/deployment/asgi/) server such as [Daphne](https://github.com/django/daphne), [Uvicorn](https://www.uvicorn.org/), or [Hypercorn](https://github.com/pgjones/hypercorn)

!!! info "Why ASGI?"

    `dj_chatbot` streams tokens to the browser with Django's async [`StreamingHttpResponse`](https://docs.djangoproject.com/en/stable/ref/request-response/#streaminghttpresponse-objects), which only streams properly under ASGI. On a WSGI server the reply arrives in one chunk instead of token-by-token, and you'll see this warning on every POST:

    ```
    Warning: StreamingHttpResponse must consume asynchronous iterators in order to serve them synchronously. Use a synchronous iterator instead.
    ```

## Installation

Install from PyPI:

```bash
pip install dj_chatbot
```

Or with uv:

```bash
uv add dj_chatbot
```

## Configuration

Add `dj_chatbot` to your Django project's `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "dj_chatbot",
]
```

Configure the chat model used by the agent. `DJ_CHATBOT_MODEL` accepts any identifier supported by LangChain's [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model), in the form `"<provider>:<model-name>"`:

```python
DJ_CHATBOT_MODEL = "openai:gpt-4o-mini"
DJ_CHATBOT_API_KEY = "..."
```

!!! note "Install your LLM provider SDK"

    `dj_chatbot` does not pull in any LLM provider SDK by default — install the one matching your `DJ_CHATBOT_MODEL` provider:

    ```bash
    pip install langchain-openai        # for "openai:..."
    pip install langchain-anthropic     # for "anthropic:..."
    pip install langchain-google-genai  # for "google_genai:..."
    ```

    See the [Chat Models integration](https://docs.langchain.com/oss/python/integrations/chat) for the full list of providers and their packages.

Run migrations to create the [`Conversation`](api/models.md#dj_chatbot.models.Conversation) and [`Message`](api/models.md#dj_chatbot.models.Message) tables:

```bash
python manage.py migrate
```

## Usage

Include the `dj_chatbot` URLs in your project's `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("chatbot/", include("dj_chatbot.urls")),
]
```

Render the widget in any template with the `chatbot_widget` template tag:

```django
{% load dj_chatbot_tags %}

<div>
    {% chatbot_widget title="Support Bot" welcome_message="Hi! How can I help?" %}
</div>
```

## Example project

A minimal Django project using `dj_chatbot` lives in the [`example/`](https://github.com/donMichaelL/dj-chatbot/tree/master/example) as a reference integration.
