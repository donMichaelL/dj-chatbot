<div align="center">

# DJ Chatbot

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)


*A Django package for adding AI-powered chatbot widgets to your project.*

📚 **[Documentation](https://donmichaell.github.io/dj-chatbot/)**

![DJ Chatbot Demo](docs/demo.gif)

</div>

## Installation

```bash
pip install dj_chatbot
```

## Configuration

Add `dj_chatbot` to your `INSTALLED_APPS` and configure the model:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "dj_chatbot",
]

DJ_CHATBOT_MODEL = "openai:gpt-4o-mini"
DJ_CHATBOT_API_KEY = "..."
```

> **Note:** `dj_chatbot` does not pull in any LLM provider SDK by default — install the matching `langchain-<provider>` package for your model (e.g. `pip install langchain-openai`).

Include the URLs and run migrations:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("chatbot/", include("dj_chatbot.urls")),
]
```

```bash
python manage.py migrate
```

Render the widget in any template:

```django
{% load dj_chatbot_tags %}

{% chatbot_widget title="Support Bot" welcome_message="Hi! How can I help?" %}
```

## Documentation

Read the full docs **[here](https://donmichaell.github.io/dj-chatbot/)**.

## Example project

A minimal Django project using `dj_chatbot` lives in [`example/`](example/) as a reference integration.
