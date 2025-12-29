"""
Tools Module

Provides standalone functions for file reading without agent SDK dependencies.
"""

from .document_tools import (
    read_pdf_tool,
    read_word_tool,
    read_pptx_tool,
    read_image_tool,
    extract_audio_tool
)

from .research_tools import (
    semantic_scholar_search,
    google_scholar_search,
    download_pdf,
    smart_summarize_paper,
    generate_citation,
    compare_papers,
    write_literature_review,
    refine_research_question,
    extract_paper_metadata,
    write_section,
    import_paper_from_doi,
    import_paper_from_arxiv,
    import_paper_from_pubmed,
    advanced_paper_search,
    get_paper_recommendations,
    create_research_note,
    list_research_notes
)

from .file_tools import (
    create_word_file,
    create_pdf,
    create_pptx,
    voice_output,
    read_folder,
    list_files_in_folder,
    delete_file
)

__all__ = [
    # Document tools
    "read_pdf_tool",
    "read_word_tool",
    "read_pptx_tool",
    "read_image_tool",
    "extract_audio_tool",
    # Research tools
    "semantic_scholar_search",
    "google_scholar_search",
    "download_pdf",
    "smart_summarize_paper",
    "generate_citation",
    "compare_papers",
    "write_literature_review",
    "refine_research_question",
    "extract_paper_metadata",
    "write_section",
    "import_paper_from_doi",
    "import_paper_from_arxiv",
    "import_paper_from_pubmed",
    "advanced_paper_search",
    "get_paper_recommendations",
    "create_research_note",
    "list_research_notes",
    # File tools
    "create_word_file",
    "create_pdf",
    "create_pptx",
    "voice_output",
    "read_folder",
    "list_files_in_folder",
    "delete_file"
]
