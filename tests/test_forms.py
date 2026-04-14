from __future__ import annotations

import pytest

from dj_chatbot.forms import MessageForm


@pytest.fixture
def valid_data():
    return {"message": "Hello, chatbot!"}


class TestMessageForm:
    def test_valid(self, valid_data):
        """Test that a form with a normal message is valid."""
        form = MessageForm(data=valid_data)
        assert form.is_valid()
        assert form.cleaned_data["message"] == "Hello, chatbot!"

    def test_empty_is_invalid(self):
        """Test that an empty message is rejected."""
        form = MessageForm(data={"message": ""})
        assert not form.is_valid()
        assert "message" in form.errors

    def test_whitespace_only_is_invalid(self):
        """Test that a whitespace-only message is stripped and rejected."""
        form = MessageForm(data={"message": "   "})
        assert not form.is_valid()

    def test_strips_leading_and_trailing_whitespace(self):
        """Test that leading/trailing whitespace is stripped from the cleaned value."""
        form = MessageForm(data={"message": "  hi  "})
        assert form.is_valid()
        assert form.cleaned_data["message"] == "hi"

    def test_rejects_too_long_message(self):
        """Test that a message over max_length is rejected."""
        form = MessageForm(data={"message": "a" * 10001})
        assert not form.is_valid()
        assert "message" in form.errors
