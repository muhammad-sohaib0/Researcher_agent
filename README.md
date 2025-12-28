# Research Agent - AI-Powered Research Assistant

A comprehensive multi-agent AI system designed for researchers. Download papers, analyze research, generate citations, write literature reviews, and create professional outputs.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)

---

## Features

### Multi-Agent Architecture
| Agent | Role | Tools |
|-------|------|-------|
| **Head Agent** | Routes tasks to specialized agents | All sub-agents |
| **Web Researcher** | Downloads research papers from Google Scholar & Semantic Scholar | `semantic_scholar_search`, `google_scholar_search`, `download_pdf`, `batch_download_pdfs` |
| **Document Reader** | Reads PDF, Word, PowerPoint, Images, Audio files | `read_pdf`, `read_word`, `read_pptx`, `read_image`, `extract_text_from_audio` |
| **Research Analyst** | Analyzes papers, generates citations, compares research | `smart_summarize_paper`, `generate_citation`, `compare_papers`, `write_literature_review`, `refine_research_question`, `write_section` |
| **Output Generator** | Creates Word, PDF, PowerPoint, Audio files | `create_word_file`, `create_pdf`, `create_pptx`, `voice_output` |

### Research Analysis (NEW!)
- **Smart Summarization** - Multiple types:
  - Comprehensive (full analysis)
  - Abstract (2-3 sentences)
  - Key Points (bullet points)
  - Methodology (research methods focus)
  - Beginner-friendly (simple explanation)
- **Citation Generator** - Multiple formats:
  - BibTeX, APA, MLA, Harvard, Chicago, IEEE
- **Paper Comparison** - Analyze multiple papers:
  - Agreements & disagreements
  - Methodological differences
  - Research gaps
- **Literature Review Writer** - Auto-generate reviews:
  - Academic, concise, or detailed style
  - Proper citations included
- **Research Question Refiner** - Turn vague ideas into:
  - Clear research questions
  - Hypotheses
  - Variables & methodology suggestions
- **Section Writer** - Draft paper sections:
  - Abstract, Introduction, Methodology
  - Results, Discussion, Conclusion

### Document Reading
- **PDF** - Extract text with page numbers
- **Word (.docx)** - Read paragraphs and tables
- **PowerPoint (.pptx)** - Extract slide content
- **Images** - OCR using Groq Llama 4 Scout Vision
- **Audio** - Transcription using Groq Whisper Large V3 Turbo

### Document Generation
- **Word Document** - Formatted with headings and paragraphs
- **PDF Document** - Professional styling with custom themes
- **PowerPoint** - AI-structured slides with 5 professional themes:
  - Professional (Blue)
  - Modern (Dark)
  - Elegant (Purple)
  - Nature (Green)
  - Warm (Orange)
- **Audio/Voice** - Text-to-speech using Gemini TTS

### Research Capabilities
- Search Google Scholar and Semantic Scholar
- Download research papers automatically
- Rank papers by relevance
- Extract citations with page numbers
- Batch download multiple PDFs in parallel

---

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **OpenAI Agents SDK** - Multi-agent orchestration
- **Google Gemini 2.5 Flash** - LLM (via OpenAI-compatible API)
- **Groq** - Whisper (speech-to-text) & Llama Vision (OCR)
- **SQLite** - Database for users and chats
- **python-pptx** - PowerPoint generation
- **PyPDF2** - PDF reading
- **python-docx** - Word document handling
- **ReportLab** - PDF generation

### Frontend
- **Next.js 15** - React framework
- **TypeScript** - Type-safe JavaScript
- **CSS Modules** - Scoped styling

---

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- uv (Python package manager)

### 1. Clone Repository
```bash
git clone https://github.com/muhammad-sohaib0/Researcher_agent.git
cd Researcher_agent
```

### 2. Setup Environment Variables
Create `.env` file in root directory:
```env
# Gemini API Keys (get from https://makersuite.google.com/app/apikey)
GEMINI_API_KEY_1=your_key_here
GEMINI_API_KEY_2=your_key_here
GEMINI_API_KEY_3=your_key_here
GEMINI_API_KEY_4=your_key_here
GEMINI_API_KEY_5=your_key_here

# Groq API Key (get from https://console.groq.com)
groq_api_key=your_groq_key_here

# SerpAPI Key for Google Scholar (get from https://serpapi.com)
SERPAPI_KEY=your_serpapi_key_here

# JWT Secret (any random string)
SECRET_KEY=your_secret_key_here
```

### 3. Install Backend Dependencies
```bash
uv sync
```

### 4. Install Frontend Dependencies
```bash
cd frontend
npm install
```

---

## Running the Application

### Terminal 1 - Backend
```bash
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

### Access
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Usage

### 1. Authentication
- Go to http://localhost:3000
- Click "Get Started"
- Sign up or login

### 2. Chat Interface
- Create new chat
- Ask research questions
- Upload documents for analysis
- Download responses as Word/PDF/PPT/Audio

### 3. Example Queries
```
"What is machine learning? Give me research papers on this topic."

"Read this PDF and summarize it with page citations."

"Convert this text to a PowerPoint presentation."

"Download 5 papers on climate change from Google Scholar."
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/signup` | POST | Register new user |
| `/api/auth/login` | POST | Login and get JWT token |
| `/api/auth/me` | GET | Get current user info |
| `/api/chat/list` | GET | Get all user chats |
| `/api/chat/new` | POST | Create new chat |
| `/api/chat/{id}` | GET | Get chat with messages |
| `/api/chat/{id}` | DELETE | Delete a chat |
| `/api/chat/{id}/message` | POST | Send message (streaming) |
| `/api/files/upload` | POST | Upload file |
| `/api/files/download/{filename}` | GET | Download generated file |

---

## Project Structure

```
Researcher_agent/
├── backend/
│   ├── agent_engine.py      # Multi-agent setup
│   ├── api.py               # FastAPI app entry
│   ├── auth.py              # JWT authentication
│   ├── database.py          # SQLite database
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── routes/
│   │   ├── auth.py          # Auth endpoints
│   │   ├── chat.py          # Chat endpoints
│   │   └── files.py         # File endpoints
│   └── uploads/             # Uploaded files
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Landing page
│   │   ├── auth/page.tsx    # Login/Signup
│   │   └── chat/page.tsx    # Chat interface
│   └── package.json
├── main.py                  # All tool functions
├── downloads/               # Generated files
├── .env                     # Environment variables
├── pyproject.toml           # Python dependencies
└── README.md
```

---

## Tools Reference

### Research Tools
| Tool | Description |
|------|-------------|
| `semantic_scholar_search` | Search Semantic Scholar for research papers |
| `google_scholar_search` | Search Google Scholar for papers |
| `download_pdf` | Download PDF from URL |
| `batch_download_pdfs` | Download multiple PDFs in parallel |

### Reading Tools
| Tool | Description |
|------|-------------|
| `read_pdf` | Extract text from PDF with page numbers |
| `read_word` | Read Word document content |
| `read_pptx` | Extract PowerPoint slide content |
| `read_image` | OCR using Groq Llama Vision |
| `extract_text_from_audio` | Transcribe audio using Groq Whisper |
| `read_folder` | Read all documents in a folder |

### Analysis Tools (NEW!)
| Tool | Description |
|------|-------------|
| `smart_summarize_paper` | Generate summaries (comprehensive/abstract/key_points/methodology/beginner) |
| `generate_citation` | Create citations (BibTeX/APA/MLA/Harvard/Chicago/IEEE) |
| `compare_papers` | Compare multiple papers, find agreements/disagreements/gaps |
| `write_literature_review` | Generate literature review with proper citations |
| `refine_research_question` | Turn vague topics into clear research questions |
| `extract_paper_metadata` | Extract title, authors, abstract, keywords, etc. |
| `write_section` | Draft paper sections (abstract/intro/methodology/results/discussion/conclusion) |

### Output Tools
| Tool | Description |
|------|-------------|
| `create_word_file` | Generate Word document |
| `create_pdf` | Generate PDF document |
| `create_pptx` | Generate PowerPoint with AI-structured slides |
| `voice_output` | Generate audio using Gemini TTS |

---

## Screenshots

### Landing Page
Modern landing page with feature showcase and "Get Started" button.

### Chat Interface
- Sidebar with chat history
- File upload support
- "Show Thinking" expandable section
- Download buttons (Word/PDF/PPT/Voice)

### PowerPoint Themes
5 professional themes with dark backgrounds, accent colors, and auto-structured content.

---

## Author

**Muhammad Sohaib**
- GitHub: [@muhammad-sohaib0](https://github.com/muhammad-sohaib0)
- Email: sohaib0285@gmail.com

---

## Acknowledgments

- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- [Google Gemini](https://deepmind.google/technologies/gemini/)
- [Groq](https://groq.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
