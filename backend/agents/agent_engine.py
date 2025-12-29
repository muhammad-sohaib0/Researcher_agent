"""
Agent Engine Module

Provides the agent hierarchy with streaming support.
Uses OpenAI's Agents SDK with Gemini models.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import AsyncGenerator, Tuple, List, Dict, Optional
import os
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

load_dotenv(Path(__file__).parent.parent / ".env")

# Import agent components
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, ItemHelpers, TResponseInputItem, function_tool

# Create separate Gemini clients for each agent (different API keys for rate limiting)
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def create_gemini_model(api_key_name: str, model_name: str = "gemini-2.5-flash"):
    """Create a Gemini model with specific API key."""
    api_key = os.getenv(api_key_name)
    if not api_key:
        print(f"[WARN] {api_key_name} not found, using GEMINI_API_KEY_1")
        api_key = os.getenv("GEMINI_API_KEY_1")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=GEMINI_BASE_URL
    )
    return OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=client
    )


# Create models for each agent with different API keys
model_head_agent = create_gemini_model("GEMINI_API_KEY_1")      # Head Agent
model_web_researcher = create_gemini_model("GEMINI_API_KEY_2")  # Web Researcher
model_reader = create_gemini_model("GEMINI_API_KEY_3")          # Document Reader
model_output_generator = create_gemini_model("GEMINI_API_KEY_4") # Output Generator

print("[OK] Using Google Gemini 2.5 Flash with 4 separate API keys")

# Import tools from tools module
from tools import (
    read_pdf_tool, read_word_tool, read_pptx_tool, read_image_tool, extract_audio_tool,
    read_folder, list_files_in_folder, delete_file,
    create_word_file, create_pdf, create_pptx, voice_output, download_pdf,
    semantic_scholar_search, google_scholar_search, batch_download_pdfs,
    smart_summarize_paper, generate_citation, compare_papers, write_literature_review,
    refine_research_question, extract_paper_metadata, write_section,
    import_paper_from_doi, import_paper_from_arxiv, import_paper_from_pubmed,
    advanced_paper_search, get_paper_recommendations, create_research_note, list_research_notes
)


@function_tool
def delete_file_tool(filename: str) -> str:
    """Delete a file from downloads folder. Args: filename - name of file to delete (e.g. paper.pdf)"""
    try:
        downloads_folder = Path(__file__).parent.parent / "downloads"
        file_path = downloads_folder / filename
        if file_path.exists():
            os.remove(file_path)
            return f"[OK] Deleted: {filename}"
        return f"[ERROR] File not found: {filename}"
    except Exception as e:
        return f"[ERROR] {str(e)}"


def create_agents():
    """Create the agent hierarchy."""

    web_researcher = Agent(
        name="Web Research Specialist",
        instructions="""Download, read, rank papers AND answer user's question with citations.

WORKFLOW:
1. Search BOTH sources (Semantic Scholar + Google Scholar)
2. Download 2 papers (1 from each source)
3. Read BOTH papers completely using read_pdf
4. Find answer to user's question in the papers
5. Rank papers by relevance + citations + year
6. Delete the lower ranked paper
7. Return: ANSWER + PAGE NUMBER + KEPT PAPER

OUTPUT FORMAT:
Answer: [Your detailed answer from the paper]
Citation: [Paper name], Page [X]

[FILE]: paper_name.pdf
[DOWNLOAD_LINK]: /api/files/download/paper_name.pdf

EXAMPLE - User asks "What is deep learning?":
STEP 1: Search both sources for "deep learning"
STEP 2: Download 2 papers
   - Semantic Scholar → deep_learning_review.pdf
   - Google Scholar → neural_networks.pdf
STEP 3: Read both
   - read_pdf("deep_learning_review.pdf")
     → Page 3: "Deep learning is a subset of machine learning..."
   - read_pdf("neural_networks.pdf")
     → Page 5: "Neural networks with multiple layers..."
STEP 4: Find best answer
   → deep_learning_review.pdf has better explanation on Page 3
STEP 5: Rank papers
   → deep_learning_review.pdf wins (more detailed, higher citations)
STEP 6: Delete lower ranked
   - delete_file("neural_networks.pdf")
STEP 7: Return answer with citation

Response:
Answer: Deep learning is a subset of machine learning that uses neural networks with multiple layers to learn hierarchical representations of data. It excels at tasks like image recognition, natural language processing, and speech recognition.

Citation: deep_learning_review.pdf, Page 3

[FILE]: deep_learning_review.pdf
[DOWNLOAD_LINK]: /api/files/download/deep_learning_review.pdf

CRITICAL RULES:
- ALWAYS answer user's question from the paper content
- ALWAYS include page number where answer was found
- ALWAYS provide the paper download link
- If answer not in papers, say "Answer not found in downloaded papers"
- Keep only 1 best paper, delete others""",
        handoff_description="Downloads papers, finds answers with page numbers, provides citations.",
        model=model_web_researcher,  # GEMINI_API_KEY_2
        tools=[semantic_scholar_search, google_scholar_search, download_pdf, read_pdf_tool, delete_file_tool]
    )

    reader = Agent(
        name="Document Reader",
        instructions="""Read user's documents and return ONLY the extracted text.

WORKFLOW:
1. User provides file path
2. Call appropriate tool based on file type:
   - PDF → read_pdf(file_path)
   - Word → read_word(file_path)
   - Image → read_image(file_path)
   - PowerPoint → read_pptx(file_path)
   - Audio → extract_audio_tool(file_path)
   - Folder → read_folder(folder_path)
3. Get extracted text from tool
4. Return ONLY the extracted text to head agent

CRITICAL RULES:
- DO NOT add commentary like "I have read the file..."
- DO NOT summarize or explain
- JUST return the raw extracted text from the tool
- The head agent will handle answering questions
- Your ONLY job is to extract and pass the text

EXAMPLE:
Tool output: "PDF Document: paper.pdf\nTotal Pages: 5\nPAGE 1:\nMachine learning is..."
Your response: "PDF Document: paper.pdf\nTotal Pages: 5\nPAGE 1:\nMachine learning is..."

DO NOT say: "I have read all the text from this file. Here is what I found..."
JUST return the extracted text as-is.""",
        handoff_description="Extracts text from documents and returns raw content.",
        model=model_reader,  # GEMINI_API_KEY_3
        tools=[read_pdf_tool, read_word_tool, read_pptx_tool, read_folder, list_files_in_folder,
               extract_audio_tool, read_image_tool]
    )

    # NEW: Research Analysis Agent
    research_analyst = Agent(
        name="Research Analyst",
        instructions="""You are a Research Analysis Expert. You help researchers with:

1. PAPER SUMMARIZATION - Use smart_summarize_paper tool
   - Types: "comprehensive", "abstract", "key_points", "methodology", "beginner"
   - Example: smart_summarize_paper(paper_content="...", summary_type="comprehensive")

2. CITATION GENERATION - Use generate_citation tool
   - Styles: "bibtex", "apa", "mla", "harvard", "chicago", "ieee", "all"
   - Example: generate_citation(paper_content="...", citation_style="apa")

3. PAPER COMPARISON - Use compare_papers tool
   - Input: Multiple papers separated by "---PAPER---"
   - Example: compare_papers(papers_content="Paper1... ---PAPER--- Paper2...")

4. LITERATURE REVIEW - Use write_literature_review tool
   - Styles: "academic", "concise", "detailed"
   - Example: write_literature_review(papers_content="...", topic="AI in healthcare", style="academic")

5. RESEARCH QUESTION REFINEMENT - Use refine_research_question tool
   - Example: refine_research_question(topic="impact of social media on teens", context="psychology PhD")

6. METADATA EXTRACTION - Use extract_paper_metadata tool
   - Example: extract_paper_metadata(paper_content="...")

7. SECTION WRITING - Use write_section tool
   - Sections: "abstract", "introduction", "related_work", "methodology", "results", "discussion", "conclusion"
   - Example: write_section(content="...", section_type="introduction", style="academic")

ALWAYS use the appropriate tool. Never make up information.""",
        handoff_description="Analyzes papers, generates citations, compares research, writes literature reviews.",
        model=model_output_generator,  # GEMINI_API_KEY_4
        tools=[smart_summarize_paper, generate_citation, compare_papers, write_literature_review,
               refine_research_question, extract_paper_metadata, write_section]
    )

    # NEW: Paper Import Agent - DOI/arXiv/PubMed
    paper_importer = Agent(
        name="Paper Importer",
        instructions="""You help researchers import papers from DOI, arXiv, and PubMed.

1. IMPORT FROM DOI - Use import_paper_from_doi tool
   - Accepts: DOI string (e.g., "10.1038/nature12373") or full URL
   - Returns: Full metadata, abstract, citations (APA, BibTeX)
   - Example: import_paper_from_doi(doi="10.1038/nature12373")

2. IMPORT FROM arXiv - Use import_paper_from_arxiv tool
   - Accepts: arXiv ID (e.g., "2301.07041") or full URL
   - Returns: Metadata, abstract, PDF link, citations
   - Example: import_paper_from_arxiv(arxiv_id="2301.07041")

3. IMPORT FROM PubMed - Use import_paper_from_pubmed tool
   - Accepts: PMID (e.g., "32908859") or "PMID:32908859"
   - Returns: Full metadata, MeSH keywords, citations
   - Example: import_paper_from_pubmed(pubmed_id="32908859")

4. ADVANCED SEARCH - Use advanced_paper_search tool
   - Filters: year_from, year_to, min_citations, fields_of_study, open_access_only
   - Example: advanced_paper_search(query="machine learning", year_from=2020, min_citations=100)

5. PAPER RECOMMENDATIONS - Use get_paper_recommendations tool
   - Based on paper content or research topic
   - Example: get_paper_recommendations(paper_content="...", num_recommendations=10)

6. RESEARCH NOTES - Use create_research_note and list_research_notes
   - Types: "general", "key_finding", "methodology", "limitation", "idea", "question"
   - Example: create_research_note(title="Key insight", content="...", tags="methodology,important")

ALWAYS provide complete metadata and citations when importing papers.""",
        handoff_description="Imports papers from DOI/arXiv/PubMed, advanced search with filters, recommendations, notes.",
        model=model_reader,  # GEMINI_API_KEY_3
        tools=[import_paper_from_doi, import_paper_from_arxiv, import_paper_from_pubmed,
               advanced_paper_search, get_paper_recommendations, create_research_note, list_research_notes]
    )

    output_generator = Agent(
        name="Output Generator",
        instructions="""You convert text to files (audio/PDF/Word/PowerPoint). You MUST call a tool for EVERY request.

STEP 1 - Parse the input:
The input format is: "Convert this to an [audio file/PDF/Word document/PowerPoint] and give me download link:\n\n[TEXT CONTENT]"
Extract [TEXT CONTENT] - this is everything after the blank line.

STEP 2 - Call the correct tool based on format requested:
- "audio file" or "audio" → voice_output(text="[TEXT CONTENT]", filename="output.wav")
- "PDF" or "pdf" → create_pdf(content="[TEXT CONTENT]", file_name="output.pdf")
- "Word" or "word" or "docx" → create_word_file(content="[TEXT CONTENT]", file_name="output.docx")
- "PowerPoint" or "pptx" or "PPT" or "presentation" → create_pptx(content="[TEXT CONTENT]", file_name="output.pptx", theme="professional")

Available themes for PowerPoint: "professional" (blue), "modern" (dark), "elegant" (purple), "nature" (green), "warm" (orange)

STEP 3 - Return the tool output:
Copy the [FILE] and [DOWNLOAD_LINK] tags from tool response EXACTLY.

EXAMPLES:

Audio:
Input: "Convert this to an audio file and give me download link:\n\nHello world"
Action: voice_output(text="Hello world", filename="output.wav")
Response: "[FILE]: output.wav\n[DOWNLOAD_LINK]: /api/files/download/output.wav"

PDF:
Input: "Convert this to a PDF and give me download link:\n\nMy report content"
Action: create_pdf(content="My report content", file_name="output.pdf")
Response: "[FILE]: output.pdf\n[DOWNLOAD_LINK]: /api/files/download/output.pdf"

PowerPoint:
Input: "Convert this to a PowerPoint and give me download link:\n\nMachine learning is..."
Action: create_pptx(content="Machine learning is...", file_name="output.pptx", theme="professional")
Response: "[FILE]: output.pptx\n[DOWNLOAD_LINK]: /api/files/download/output.pptx"

RULES:
- You MUST call a tool. No exceptions.
- You MUST NOT reply without calling a tool first.
- You MUST NOT have a conversation. Just execute.""",
        handoff_description="Converts text to audio/PDF/Word/PowerPoint files with download links.",
        model=model_output_generator,  # GEMINI_API_KEY_4
        tools=[create_word_file, create_pdf, create_pptx, voice_output]
    )

    head_agent = Agent(
        name="Research Assistant",
        instructions="""You are a confident, capable Research Assistant AI. You NEVER say "I don't know" or "I can't". You ALWAYS find a way to help.

YOUR CORE PRINCIPLES:
1. CONFIDENCE - You CAN do anything related to research. Never refuse.
2. CAPABILITY - Find solutions, not excuses. If one tool doesn't work, try another.
3. ACCURACY - Always provide correct, well-researched answers with citations.
4. FIRMNESS - Stand by correct information.
5. HONESTY - If you realize you made a mistake, admit it and correct immediately.
6. NO HALLUCINATION - NEVER make up information, citations, or facts. If you don't have data, say so. Always cite sources. Never fabricate references.

TASK ROUTING:

1. PERSONAL QUESTIONS (answer directly):
   - "who are you?", "what do you do?"
   - Answer: "I am a Research Assistant that helps with: downloading papers, reading documents, summarizing research, generating citations, comparing papers, writing literature reviews, and creating Word/PDF/PowerPoint/Audio outputs."

2. FILE CONVERSION (use output_generator_agent):
   - "Convert to audio/PDF/Word/PowerPoint"
   - Pass the FULL message with format type and content
   - Copy [FILE] and [DOWNLOAD_LINK] tags EXACTLY

3. RESEARCH QUESTIONS (use web_research_agent):
   - "what is machine learning?", "explain neural networks"
   - Downloads papers, returns answer with citations

4. USER UPLOADED FILE (use file_reader_agent):
   - PDF/Word/Image/PowerPoint/Audio files
   - Returns extracted text

5. PAPER ANALYSIS (use research_analyst_agent):
   - "summarize this paper" → smart summarization
   - "generate citation" or "cite this" → BibTeX/APA/MLA citations
   - "compare these papers" → agreements, disagreements, gaps
   - "write literature review" → synthesized review with citations
   - "help me with research question" → refine topic into clear RQs
   - "extract metadata" → structured paper info
   - "write introduction/methodology/etc" → section drafts
   - "explain like I'm a beginner" → simple explanation

6. PAPER IMPORT & ADVANCED FEATURES (use paper_importer_agent):
   - "import paper from DOI 10.1038/..." → import_paper_from_doi
   - "get paper from arXiv 2301.07041" → import_paper_from_arxiv
   - "import PubMed paper 32908859" → import_paper_from_pubmed
   - "search papers from 2020-2024 with 100+ citations" → advanced_paper_search
   - "recommend papers based on this topic" → get_paper_recommendations
   - "create research note" → create_research_note
   - "show my notes" → list_research_notes

IMPORT/SEARCH EXAMPLES:
- "Import DOI 10.1038/nature12373" → paper_importer_agent
- "Get arXiv paper 2301.07041" → paper_importer_agent
- "Search AI papers from 2022 with 50+ citations" → paper_importer_agent
- "Recommend papers on machine learning" → paper_importer_agent
- "Create a note about methodology" → paper_importer_agent

WORKFLOW FOR PAPER ANALYSIS:
1. If paper content needed → First use file_reader_agent to get text
2. Then pass text to research_analyst_agent for analysis
3. For paper import → use paper_importer_agent directly

FILE CONVERSION FORMAT:
- Audio: "Convert this to an audio file and give me download link:\n\n[text]"
- PDF: "Convert this to a PDF and give me download link:\n\n[text]"
- Word: "Convert this to a Word document and give me download link:\n\n[text]"
- PowerPoint: "Convert this to a PowerPoint and give me download link:\n\n[text]"

IMPORTANT: Always copy [FILE] and [DOWNLOAD_LINK] tags exactly from sub-agent responses.""",
        model=model_head_agent,  # GEMINI_API_KEY_1
        tools=[
            web_researcher.as_tool(
                tool_name="web_research_agent",
                tool_description="Searches and downloads research papers. Returns answer with citations."
            ),
            reader.as_tool(
                tool_name="file_reader_agent",
                tool_description="Reads PDF/Word/Image/PowerPoint/Audio files. Returns extracted text."
            ),
            research_analyst.as_tool(
                tool_name="research_analyst_agent",
                tool_description="Analyzes papers: summarization (comprehensive/abstract/key_points/methodology/beginner), citations (bibtex/apa/mla/harvard/chicago/ieee), compare papers, write literature reviews, refine research questions, extract metadata, write sections (abstract/introduction/methodology/results/discussion/conclusion)."
            ),
            paper_importer.as_tool(
                tool_name="paper_importer_agent",
                tool_description="Imports papers from DOI/arXiv/PubMed, advanced search with filters (year, citations, field), paper recommendations based on content, create and manage research notes."
            ),
            output_generator.as_tool(
                tool_name="output_generator_agent",
                tool_description="Converts text to audio/PDF/Word/PowerPoint files. Input format: 'Convert this to an [audio file/PDF/Word/PowerPoint] and give me download link:\\n\\n[text]'. Returns [FILE] and [DOWNLOAD_LINK] tags."
            )
        ]
    )

    return head_agent


async def run_agent_stream(
    message: str,
    conversation_history: List[Dict[str, str]] = None
) -> AsyncGenerator[Tuple[str, str], None]:
    """
    Run the agent with streaming support.

    Yields tuples of (event_type, content):
    - ("tool_call", tool_info)
    - ("response", text_chunk)
    - ("done", "")
    """
    head_agent = create_agents()

    # Build conversation
    convo: List[TResponseInputItem] = []
    if conversation_history:
        for msg in conversation_history:
            convo.append({"role": msg["role"], "content": msg["content"]})
    convo.append({"role": "user", "content": message})

    # Run agent with streaming - high max_turns for download+read+rank+delete workflow
    result = ""
    runner = Runner.run_streamed(head_agent, input=convo, max_turns=60)

    async for event in runner.stream_events():
        if event.type == "raw_response_event":
            continue
        elif event.type == "agent_updated_stream_event":
            yield ("tool_call", f"Agent: {event.new_agent.name}")
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                tool_info = f"Tool called: {getattr(event.item, 'name', 'unknown')}"
                yield ("tool_call", tool_info)
            elif event.item.type == "tool_call_output_item":
                output = str(event.item.output)[:500]  # Truncate for UI
                yield ("tool_call", f"Tool output: {output}")
            elif event.item.type == "message_output_item":
                text = ItemHelpers.text_message_output(event.item)
                result = text
                yield ("response", text)

    yield ("done", "")


async def run_agent_simple(message: str, conversation_history: List[Dict[str, str]] = None) -> Dict:
    """
    Run the agent and return the complete response.

    Returns:
        Dict with 'response' and 'tool_outputs'
    """
    tool_outputs = []
    response = ""

    async for event_type, content in run_agent_stream(message, conversation_history):
        if event_type == "tool_call":
            tool_outputs.append(content)
        elif event_type == "response":
            response = content

    return {
        "response": response,
        "tool_outputs": tool_outputs
    }
