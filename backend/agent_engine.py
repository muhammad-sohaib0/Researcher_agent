# Agent Engine for API
# This module runs the agent with streaming support

import asyncio
import json
import sys
from pathlib import Path
from typing import AsyncGenerator, Tuple, List, Dict
import os
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

load_dotenv(Path(__file__).parent.parent / ".env")

# Import agent components
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, ItemHelpers, TResponseInputItem

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

# Import tools from parent main.py (the agent code)
import importlib.util
parent_main_path = Path(__file__).parent.parent / "main.py"
spec = importlib.util.spec_from_file_location("agent_main", parent_main_path)
agent_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_main)

# Get tools from parent main.py
read_pdf = agent_main.read_pdf
read_word = agent_main.read_word
read_pptx = agent_main.read_pptx
read_image = agent_main.read_image
extract_text_from_audio = agent_main.extract_text_from_audio
read_folder = agent_main.read_folder
list_files_in_folder = agent_main.list_files_in_folder
create_word_file = agent_main.create_word_file
create_pdf = agent_main.create_pdf
create_pptx = agent_main.create_pptx
voice_output = agent_main.voice_output
download_pdf = agent_main.download_pdf
semantic_scholar_search = agent_main.semantic_scholar_search
google_scholar_search = agent_main.google_scholar_search
batch_download_pdfs = agent_main.batch_download_pdfs

# Create a simple delete function without the problematic parameter
from agents import function_tool
from pathlib import Path
import os

@function_tool
def delete_file(filename: str) -> str:
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
        tools=[semantic_scholar_search, google_scholar_search, download_pdf, read_pdf, delete_file]
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
   - Audio → extract_text_from_audio(file_path)
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
        tools=[read_pdf, read_word, read_pptx, read_folder, list_files_in_folder, extract_text_from_audio, read_image]
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
        instructions="""You are a Research Assistant AI that helps with research papers.

TASK ROUTING:

1. PERSONAL QUESTIONS (answer directly):
   - "who are you?", "what do you do?"
   - Answer: "I am a Research Assistant that can download papers, read documents, create audio/PDF/Word/PowerPoint, and provide answers with citations."

2. FILE CONVERSION (use output_generator_agent):
   When user wants to convert text to audio/PDF/Word/PowerPoint:
   - Detect: "Convert this to an audio file", "Convert this to a PDF", "Convert this to a Word document", "Convert this to a PowerPoint"
   - Action: Call output_generator_agent with the FULL message including format type and text content
   - The sub-agent will create the file and return [FILE] and [DOWNLOAD_LINK] tags
   - Copy these tags EXACTLY in your response

3. RESEARCH QUESTIONS (use web_research_agent):
   - "what is machine learning?", "explain neural networks"
   - Call web_research_agent → downloads papers → returns answer with citations

4. USER UPLOADED FILE (use file_reader_agent):
   - User attached PDF/Word/Image/PowerPoint/Audio
   - Call file_reader_agent with the file path

HOW TO CALL output_generator_agent:
Pass the COMPLETE conversion request as input:
- Audio: "Convert this to an audio file and give me download link:\n\n[text]"
- PDF: "Convert this to a PDF and give me download link:\n\n[text]"
- Word: "Convert this to a Word document and give me download link:\n\n[text]"
- PowerPoint: "Convert this to a PowerPoint and give me download link:\n\n[text]"

The agent returns [FILE] and [DOWNLOAD_LINK] tags - copy them EXACTLY to your response.

EXAMPLES:
User: "who are you?"
→ Direct answer

User: "Convert this to an audio file and give me download link:\n\nHello world"
→ Call output_generator_agent with full message
→ Response includes: "[FILE]: output.wav\n[DOWNLOAD_LINK]: /api/files/download/output.wav"

User: "Convert this to a PowerPoint and give me download link:\n\nMachine learning..."
→ Call output_generator_agent with full message
→ Response includes: "[FILE]: output.pptx\n[DOWNLOAD_LINK]: /api/files/download/output.pptx"

User: "what is deep learning?"
→ Call web_research_agent""",
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
