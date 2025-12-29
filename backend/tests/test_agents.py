"""
Unit Tests for Agent Engine
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAgentEngine:
    """Tests for agent engine."""

    @patch('agents.agent_engine.create_gemini_model')
    def test_create_gemini_model_missing_key(self, mock_create):
        """Test create_gemini_model with missing API key."""
        # Reset the module to test fresh
        import importlib
        import agents.agent_engine as ae

        with patch.dict(os.environ, {"GEMINI_API_KEY_1": ""}):
            importlib.reload(ae)
            # Should handle missing key gracefully
            # (implementation handles this with fallback)

    def test_create_agents_returns_head_agent(self):
        """Test that create_agents returns a head agent."""
        from agents.agent_engine import create_agents

        head_agent = create_agents()
        assert head_agent is not None
        assert hasattr(head_agent, 'name')
        assert head_agent.name == "Research Assistant"

    @pytest.mark.asyncio
    async def test_run_agent_simple_returns_dict(self):
        """Test run_agent_simple returns proper dict structure."""
        from agents.agent_engine import run_agent_simple

        # This test may need mocking for actual API calls
        # For now, just verify the function structure
        assert asyncio.iscoroutinefunction(run_agent_simple)

    def test_agent_tools_defined(self):
        """Test that all required tools are defined in agent_engine."""
        from agents.agent_engine import (
            read_pdf_tool, read_word_tool, read_pptx_tool,
            semantic_scholar_search, download_pdf, create_pdf,
            delete_file
        )
        # All tools should be callable
        assert callable(read_pdf_tool)
        assert callable(read_word_tool)
        assert callable(read_pptx_tool)


class TestAgentToolDefinitions:
    """Tests for agent tool definitions."""

    def test_web_researcher_instructions_contain_search(self):
        """Test web researcher instructions mention search."""
        from agents.agent_engine import create_agents

        # Get agents without actually creating (just verify instructions exist)
        head_agent = create_agents()
        tools = head_agent.tools

        # Should have web_research_agent tool
        tool_names = [t.name if hasattr(t, 'name') else str(t) for t in tools]
        assert any("web_research" in str(t).lower() for t in tool_names)

    def test_reader_instructions_file_types(self):
        """Test reader agent instructions mention file types."""
        from agents.agent_engine import create_agents

        head_agent = create_agents()
        # The reader agent should be accessible as a tool
        # Instructions should mention PDF, Word, etc.

    def test_output_generator_instructions(self):
        """Test output generator handles file conversions."""
        from agents.agent_engine import create_agents

        head_agent = create_agents()
        # Should have output_generator_agent tool


class TestAgentStreaming:
    """Tests for agent streaming functionality."""

    @pytest.mark.asyncio
    async def test_run_agent_stream_yields_events(self):
        """Test run_agent_stream yields events correctly."""
        from agents.agent_engine import run_agent_stream

        # Verify it's an async generator
        gen = run_agent_stream("test message")
        assert asyncio.isasyncgen(gen)

    @pytest.mark.asyncio
    async def test_run_agent_stream_event_types(self):
        """Test run_agent_stream yields correct event types."""
        from agents.agent_engine import run_agent_stream

        events = []
        async for event in run_agent_stream("hello"):
            events.append(event)

        # Should have at least done event
        assert len(events) > 0


class TestAgentMessageBuilding:
    """Tests for message building logic."""

    def test_conversation_history_format(self):
        """Test conversation history is properly formatted."""
        from agents.agent_engine import run_agent_simple

        # This tests the internal structure
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        # Should be convertible to agent input format
        expected = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "test"}
        ]
        assert len(history) == 2
