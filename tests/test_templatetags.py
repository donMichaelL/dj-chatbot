from __future__ import annotations

from django.template import Context, Template


def render(template_source: str, context: dict[str, object] | None = None) -> str:
    return Template(template_source).render(Context(context or {}))


class TestChatbotWidget:
    def test_renders_default_endpoints(self):
        """Test that the widget renders the default send/history URLs as data attributes."""
        html = render("{% load dj_chatbot_tags %}{% chatbot_widget %}")
        assert 'data-endpoint="/chat/send/"' in html
        assert 'data-history="/chat/history/"' in html

    def test_renders_csrf_hidden_input(self):
        """Test that the CSRF token from context is rendered as a hidden input."""
        html = render(
            "{% load dj_chatbot_tags %}{% chatbot_widget %}",
            {"csrf_token": "fake-csrf-token"},
        )
        assert 'name="csrfmiddlewaretoken"' in html
        assert "fake-csrf-token" in html

    def test_default_title(self):
        """Test that the default title renders when no kwarg is passed."""
        html = render("{% load dj_chatbot_tags %}{% chatbot_widget %}")
        assert '<span id="dj-chatbot-title">Chat</span>' in html

    def test_custom_title(self):
        """Test that a custom title kwarg appears in the header."""
        html = render('{% load dj_chatbot_tags %}{% chatbot_widget title="Support" %}')
        assert '<span id="dj-chatbot-title">Support</span>' in html

    def test_welcome_message_is_passed_to_data_attribute(self):
        """Test that welcome_message is exposed via data-welcome for the JS to read."""
        html = render('{% load dj_chatbot_tags %}{% chatbot_widget welcome_message="Hi there" %}')
        assert 'data-welcome="Hi there"' in html

    def test_static_assets_referenced(self):
        """Test that the namespaced static CSS and JS paths are in the output."""
        html = render("{% load dj_chatbot_tags %}{% chatbot_widget %}")
        assert "dj_chatbot/css/widget.css" in html
        assert "dj_chatbot/js/widget.js" in html
