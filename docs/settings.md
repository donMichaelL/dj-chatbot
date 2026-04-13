# Settings

`dj_chatbot` settings that are declared in your Django project's `settings.py`.

## `DJ_CHATBOT_API_KEY`

**Required.** API key for the configured provider. Keep it secret and never commit the key to version control.

- **Type:** `str`
- **Default:** *(none — raises `ImproperlyConfigured` if unset)*

```python
DJ_CHATBOT_API_KEY = "...."
```

## `DJ_CHATBOT_MODEL`

Identifier passed to LangChain's [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model), in the form `"<provider>:<model-name>"`.

- **Type:** `str`
- **Default:** *(none — raises `ImproperlyConfigured` if unset)*
- **Override per view:** set [`model`](api/views.md#dj_chatbot.views.ChatView.model) on your [`ChatView`](api/views.md#dj_chatbot.views.ChatView) subclass.

```python
DJ_CHATBOT_MODEL = "openai:gpt-4o-mini"
```


## `DJ_CHATBOT_SYSTEM_PROMPT`

System prompt prepended to every conversation.

- **Type:** `str`
- **Default:** `"You are a helpful assistant."`
- **Override per view:** set [`system_prompt`](api/views.md#dj_chatbot.views.ChatView.system_prompt) on your [`ChatView`](api/views.md#dj_chatbot.views.ChatView) subclass.

```python
DJ_CHATBOT_SYSTEM_PROMPT = "You are a support assistant for ...."
```
