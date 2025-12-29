"""
Unit Tests for Tools Module
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDocumentTools:
    """Tests for document reading tools."""

    def test_read_word_tool_file_not_found(self):
        """Test read_word_tool returns error for non-existent file."""
        from tools.document_tools import read_word_tool

        result = read_word_tool("/nonexistent/path.docx")
        assert "Error: File not found" in result

    def test_read_pptx_tool_file_not_found(self):
        """Test read_pptx_tool returns error for non-existent file."""
        from tools.document_tools import read_pptx_tool

        result = read_pptx_tool("/nonexistent/path.pptx")
        assert "Error: File not found" in result

    def test_read_image_tool_file_not_found(self):
        """Test read_image_tool returns error for non-existent file."""
        from tools.document_tools import read_image_tool

        result = read_image_tool("/nonexistent/path.png")
        assert "Error: File not found" in result

    def test_extract_audio_tool_file_not_found(self):
        """Test extract_audio_tool returns error for non-existent file."""
        from tools.document_tools import extract_audio_tool

        result = extract_audio_tool("/nonexistent/path.wav")
        assert "Error: File not found" in result

    @patch('tools.document_tools.os.getenv')
    def test_read_pdf_tool_missing_api_key(self, mock_getenv):
        """Test read_pdf_tool returns error when API key is missing."""
        mock_getenv.return_value = None

        from tools.document_tools import read_pdf_tool

        result = read_pdf_tool("/some/file.pdf")
        assert "groq_api_key not found" in result


class TestResearchTools:
    """Tests for research tools."""

    def test_advanced_paper_search_missing_query(self):
        """Test advanced_paper_search handles missing query gracefully."""
        from tools.research_tools import advanced_paper_search

        # Should not raise an exception
        result = advanced_paper_search("")
        assert "Advanced Search" in result

    def test_refine_research_question_empty_topic(self):
        """Test refine_research_question handles empty topic."""
        from tools.research_tools import refine_research_question

        result = refine_research_question("")
        assert "Refined Research Questions" in result

    def test_create_research_note(self):
        """Test create_research_note returns correct format."""
        from tools.research_tools import create_research_note

        result = create_research_note(
            title="Test Note",
            content="Test content",
            note_type="key_finding",
            tags="test,important"
        )
        assert "Research Note Created" in result
        assert "Test Note" in result

    def test_list_research_notes(self):
        """Test list_research_notes returns expected format."""
        from tools.research_tools import list_research_notes

        result = list_research_notes()
        assert "Research Notes" in result


class TestFileTools:
    """Tests for file tools."""

    def test_delete_file_not_found(self):
        """Test delete_file returns error for non-existent file."""
        from tools.file_tools import delete_file

        result = delete_file("nonexistent_file.pdf")
        assert "File not found" in result

    def test_list_files_in_folder_not_found(self):
        """Test list_files_in_folder returns error for non-existent folder."""
        from tools.file_tools import list_files_in_folder

        result = list_files_in_folder("/nonexistent/folder")
        assert "Folder not found" in result

    def test_read_folder_not_found(self):
        """Test read_folder returns error for non-existent path."""
        from tools.file_tools import read_folder

        result = read_folder("/nonexistent/folder")
        assert "not found" in result


class TestToolsIntegration:
    """Integration tests for tools module."""

    def test_tools_module_exports(self):
        """Test that all expected tools are exported."""
        from tools import (
            read_pdf_tool, read_word_tool, read_pptx_tool,
            read_image_tool, extract_audio_tool,
            semantic_scholar_search, google_scholar_search,
            create_word_file, create_pdf, create_pptx,
            delete_file, list_files_in_folder
        )
        # If no exception is raised, all imports succeeded
        assert True

    def test_document_tools_signature(self):
        """Test that document tools have correct signatures."""
        import inspect
        from tools.document_tools import read_pdf_tool, read_word_tool

        sig = inspect.signature(read_pdf_tool)
        assert 'file_path' in sig.parameters

        sig = inspect.signature(read_word_tool)
        assert 'file_path' in sig.parameters
