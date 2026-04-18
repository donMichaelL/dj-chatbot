from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from dj_chatbot.views import ChatView


@pytest.fixture
def view():
    return ChatView()


class TestGetSystemPrompt:
    def test_uses_class_attribute_when_set(self, view):
        """Test that the class attribute takes precedence over settings."""
        view.system_prompt = "class-level prompt"
        assert view.get_system_prompt() == "class-level prompt"

    @override_settings(DJ_CHATBOT_SYSTEM_PROMPT="settings-level prompt")
    def test_falls_back_to_setting(self, view):
        """Test that settings are used when no class attribute is set."""
        assert view.get_system_prompt() == "settings-level prompt"

    def test_default_when_neither_set(self, view):
        """Test that a hardcoded default is returned when neither source is set."""
        assert view.get_system_prompt() == "You are a helpful assistant."


class TestGetModel:
    def test_uses_class_attribute_when_set(self, view):
        """Test that the class attribute takes precedence over settings."""
        view.model = "openai:gpt-4o"
        assert view.get_model() == "openai:gpt-4o"

    @override_settings(DJ_CHATBOT_MODEL="anthropic:claude-haiku")
    def test_falls_back_to_setting(self, view):
        """Test that settings are used when no class attribute is set."""
        assert view.get_model() == "anthropic:claude-haiku"


class TestBuildHooks:
    def test_build_tools_defaults_to_empty(self, view):
        """Test that build_tools returns an empty list by default."""
        assert view.build_tools() == []

    def test_build_middleware_defaults_to_empty(self, view):
        """Test that build_middleware returns an empty list by default."""
        assert view.build_middleware() == []

    def test_build_memory_returns_memorysaver(self, view):
        """Test that build_memory returns a MemorySaver instance by default."""
        from langgraph.checkpoint.memory import MemorySaver

        assert isinstance(view.build_memory(), MemorySaver)


class TestBuildAgent:
    @override_settings(DJ_CHATBOT_MODEL="openai:gpt-4o-mini", DJ_CHATBOT_API_KEY="sk-test")
    def test_composes_create_agent_with_hooks(self, view):
        """Test that build_agent calls create_agent with values from the build_* hooks."""
        with (
            patch("dj_chatbot.views.create_agent") as mock_create_agent,
            patch("dj_chatbot.views.init_chat_model") as mock_init,
        ):
            mock_init.return_value = MagicMock(name="model")
            mock_create_agent.return_value = MagicMock(name="agent")

            view.build_agent()

            mock_init.assert_called_once_with(model="openai:gpt-4o-mini", api_key="sk-test")
            kwargs = mock_create_agent.call_args.kwargs
            assert kwargs["tools"] == []
            assert kwargs["middleware"] == []
            assert kwargs["system_prompt"] == "You are a helpful assistant."
            assert kwargs["checkpointer"] is not None
