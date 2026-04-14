from __future__ import annotations

from django import forms


class MessageForm(forms.Form):
    """Validates a single chat message submitted by the user.

    This is the default form used by the chatbot views.

    Attributes:
        message: The user's text input. Stripped of surrounding whitespace,
            required, and limited to 10,000 characters.
    """

    message = forms.CharField(max_length=10000, strip=True, required=True)
