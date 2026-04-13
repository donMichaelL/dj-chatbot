# Customizing the Widget

The chat UI is rendered by the `chatbot_widget` template tag, which itself renders `dj_chatbot/widget.html`. You can customize the widget in three ways:

- Pass arguments to the tag
- Tweak its CSS variables
- Override the template entirely

## Template tag arguments

```django
{% load dj_chatbot_tags %}

{% chatbot_widget
    title="Support Bot"
    welcome_message="Hi! How can I help?"
    url_name="dj_chatbot_send"
    history_url_name="dj_chatbot_history"
%}
```

| Argument            | Type  | Default                  | Purpose                                                                 |
|---------------------|-------|--------------------------|-------------------------------------------------------------------------|
| `title`             | `str` | `"Chat"`                 | Heading shown in the widget header.                                     |
| `welcome_message`   | `str` | `""`                     | Message shown before the user sends anything.                           |
| `url_name`          | `str` | `"dj_chatbot_send"`      | Named URL of the `POST` endpoint that streams replies.                  |
| `history_url_name`  | `str` | `"dj_chatbot_history"`   | Named URL of the `GET` endpoint that returns the current thread.        |


## Styling with CSS variables

The widget exposes a set of CSS custom properties on the `.dj-chatbot` root element. Override them in your own stylesheet — loaded **after** the widget's CSS — to restyle customize.

```css
/* yourproject/static/css/overrides.css */
.dj-chatbot {
    --dj-chatbot-primary: #16a34a;
    --dj-chatbot-primary-hover: #15803d;
    --dj-chatbot-window-width: 420px;
    --dj-chatbot-window-height: 600px;
    --dj-chatbot-font-size: 1rem;
}
```

Available variables:

| Variable                           | Default                           | Purpose                                              |
|------------------------------------|-----------------------------------|------------------------------------------------------|
| `--dj-chatbot-primary`             | `#2563eb`                         | Accent color (toggle button, header, user bubble).   |
| `--dj-chatbot-primary-hover`       | `#1d4ed8`                         | Hover state for the toggle button.                   |
| `--dj-chatbot-bg`                  | `#fff`                            | Background of the chat window.                       |
| `--dj-chatbot-text`                | `#1e293b`                         | Default text color.                                  |
| `--dj-chatbot-msg-user-bg`         | `var(--dj-chatbot-primary)`       | User message bubble background.                      |
| `--dj-chatbot-msg-user-text`       | `#fff`                            | User message text color.                             |
| `--dj-chatbot-msg-assistant-bg`    | `#f1f5f9`                         | Assistant message bubble background.                 |
| `--dj-chatbot-msg-assistant-text`  | `var(--dj-chatbot-text)`          | Assistant message text color.                        |
| `--dj-chatbot-border`              | `#e2e8f0`                         | Border color used throughout the widget.             |
| `--dj-chatbot-toggle-size`         | `56px`                            | Diameter of the floating toggle button.              |
| `--dj-chatbot-font-family`         | `inherit`                         | Font family for messages.                            |
| `--dj-chatbot-font-size`           | `0.875rem`                        | Font size for messages.                              |
| `--dj-chatbot-window-width`        | `360px`                           | Width of the open chat window.                       |
| `--dj-chatbot-window-height`       | `500px`                           | Height of the open chat window.                      |

Dark mode defaults are applied automatically via `prefers-color-scheme: dark` — override the same variables inside your own `@media (prefers-color-scheme: dark)` block if you want different dark colors.

## Overriding the template

Django's template loader resolves `dj_chatbot/widget.html`. To replace the widget markup, create a file with the same path in one of your own apps (listed **before** `dj_chatbot` in `INSTALLED_APPS`) or in a project-level templates directory:

```
myproject/
└── templates/
    └── dj_chatbot/
        └── widget.html
```

The template receives the following context:

| Variable            | Type  | Description                                                 |
|---------------------|-------|-------------------------------------------------------------|
| `endpoint`          | `str` | Resolved URL for the send endpoint.                         |
| `history_endpoint`  | `str` | Resolved URL for the history endpoint.                      |
| `title`             | `str` | Widget title.                                               |
| `welcome_message`   | `str` | Welcome text shown before the first message.                |
| `csrf_token`        | `str` | CSRF token from the rendering request context.              |
