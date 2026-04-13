# dj-chatbot example

Minimal Django project showing three ways to use [`dj-chatbot`](https://pypi.org/project/dj-chatbot/).

## Pages

| Path        | View                                  | Demonstrates                                             |
| ----------- | ------------------------------------- | -------------------------------------------------------- |
| `/`         | `dj_chatbot.views.ChatView`           | Wiring via settings only                                 |
| `/models/`  | `config.views.SupportChatView`        | Custom `build_model` (returns a `ChatOpenAI` instance)   |
| `/tools/`   | `config.views.UsersChatView`          | Custom `build_tools` (exposes a `list_users` tool)       |

## Run locally

**1. Create a virtual environment and install dependencies**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Set your OpenAI API key**

```bash
export OPENAI_API_KEY="sk-..."
```

**3. Migrate and start the server**

```bash
python manage.py migrate
python manage.py runserver
```

Visit **<http://127.0.0.1:8000/>**.

---

> **Note:** `daphne` is listed first in `INSTALLED_APPS` so `runserver` auto-upgrades to ASGI — required for streaming token-by-token responses.
