# Research Agent - AI-Powered Research Assistant

A comprehensive multi-agent AI system designed for researchers. Download papers, analyze research, generate citations, write literature reviews, and create professional outputs.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.125+-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)
![React](https://img.shields.io/badge/React-19.2-blue)

---

## Features

### Multi-Agent Architecture

| Agent | Role | Tools |
|-------|------|-------|
| **Head Agent** | Routes tasks to specialized agents | All sub-agents |
| **Web Researcher** | Downloads research papers from Google Scholar & Semantic Scholar | `semantic_scholar_search`, `google_scholar_search`, `download_pdf`, `batch_download_pdfs` |
| **Document Reader** | Reads PDF, Word, PowerPoint, Images, Audio files | `read_pdf`, `read_word`, `read_pptx`, `read_image`, `extract_text_from_audio` |
| **Research Analyst** | Analyzes papers, generates citations, compares research | `smart_summarize_paper`, `generate_citation`, `compare_papers`, `write_literature_review`, `refine_research_question`, `write_section` |
| **Paper Importer** | Imports papers from DOI/arXiv/PubMed, advanced search, recommendations | `import_paper_from_doi`, `import_paper_from_arxiv`, `import_paper_from_pubmed`, `advanced_paper_search`, `get_paper_recommendations`, `create_research_note` |
| **Output Generator** | Creates Word, PDF, PowerPoint, Audio files | `create_word_file`, `create_pdf`, `create_pptx`, `voice_output` |

### Paper Import & Discovery
- **DOI Import** - Import any paper using its DOI
  - Fetches metadata from CrossRef
  - Auto-generates APA, BibTeX citations
  - Shows citation count, abstract
- **arXiv Import** - Import papers from arXiv
  - Direct PDF download link
  - Categories and publication date
- **PubMed Import** - Import medical/biomedical papers
  - MeSH keywords
  - Journal information
- **Advanced Search** - Semantic search with filters:
  - Year range (e.g., 2020-2024)
  - Minimum citations (e.g., 100+)
  - Fields of study
  - Open access only
- **Paper Recommendations** - AI-powered suggestions:
  - Based on uploaded paper content
  - Based on research topic
- **Research Notes** - Knowledge management:
  - Types: key_finding, methodology, limitation, idea, question
  - Tags for organization
  - Linked to papers

### Research Analysis
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
- **SQLAlchemy 2.0** - ORM database
- **python-pptx** - PowerPoint generation
- **PyPDF2 & PyMuPDF** - PDF reading
- **python-docx** - Word document handling
- **ReportLab** - PDF generation

### Frontend
- **Next.js 15** - React framework with App Router
- **React 19** - UI library
- **TypeScript 5** - Type-safe JavaScript
- **CSS Modules** - Scoped styling
- **Dark/Light Theme** - Theme toggle support

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
JWT_SECRET_KEY=your_secret_key_here
```

### 3. Install Backend Dependencies
```bash
cd backend
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

"Import this paper by DOI: 10.1038/s41586-020-2649-2"

"Write a literature review on transformer models"
```

---

## API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/signup` | POST | Register new user |
| `/api/auth/login` | POST | Login and get JWT token |
| `/api/auth/me` | GET | Get current user info |

### Chat
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/list` | GET | Get all user chats |
| `/api/chat/new` | POST | Create new chat |
| `/api/chat/{id}` | GET | Get chat with messages |
| `/api/chat/{id}` | DELETE | Delete a chat |
| `/api/chat/{id}/message` | POST | Send message (streaming) |

### Files
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/files/upload` | POST | Upload and process file |
| `/api/files/download/{filename}` | GET | Download generated file |
| `/api/files/list` | GET | List all downloaded files |

---

## Project Structure

```
Researcher_agent/
├── backend/
│   ├── main.py                  # FastAPI application entry
│   ├── agent_engine.py          # Multi-agent orchestration setup
│   ├── auth.py                  # JWT authentication
│   ├── database.py              # SQLite database connection
│   ├── models.py                # SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic schemas
│   ├── tools.py                 # File reading utilities
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── chat.py              # Chat endpoints with streaming
│   │   └── files.py             # File upload/download endpoints
│   ├── uploads/                 # User uploaded files
│   └── research_agent.db        # SQLite database
├── frontend/
│   ├── app/
│   │   ├── layout.tsx           # Root layout with theme toggle
│   │   ├── page.tsx             # Landing page
│   │   └── auth/
│   │       └── page.tsx         # Login/Signup page
│   │   └── chat/
│   │       └── page.tsx         # Chat interface
│   ├── public/                  # Static assets
│   ├── package.json             # NPM dependencies
│   ├── tsconfig.json            # TypeScript configuration
│   ├── next.config.ts           # Next.js configuration
│   └── .env.local               # Frontend environment
├── main.py                      # All tool functions (5,700+ lines)
├── pyproject.toml               # Python dependencies
├── .env                         # Environment variables
├── .env.example                 # Environment template
├── .gitignore
├── README.md
└── downloads/                   # Generated output files
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

### Analysis Tools
| Tool | Description |
|------|-------------|
| `smart_summarize_paper` | Generate summaries (comprehensive/abstract/key_points/methodology/beginner) |
| `generate_citation` | Create citations (BibTeX/APA/MLA/Harvard/Chicago/IEEE) |
| `compare_papers` | Compare multiple papers, find agreements/disagreements/gaps |
| `write_literature_review` | Generate literature review with proper citations |
| `refine_research_question` | Turn vague topics into clear research questions |
| `extract_paper_metadata` | Extract title, authors, abstract, keywords, etc. |
| `write_section` | Draft paper sections (abstract/intro/methodology/results/discussion/conclusion) |

### Import & Discovery Tools
| Tool | Description |
|------|-------------|
| `import_paper_from_doi` | Import paper metadata from DOI (CrossRef API) |
| `import_paper_from_arxiv` | Import paper from arXiv with PDF link |
| `import_paper_from_pubmed` | Import paper from PubMed with MeSH keywords |
| `advanced_paper_search` | Search with filters: year, citations, field, open access |
| `get_paper_recommendations` | AI-powered paper recommendations based on content |
| `create_research_note` | Create structured research notes with tags |
| `list_research_notes` | List and filter research notes |

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

## Database Schema

### Users Table
- `id` - Primary key
- `email` - Unique email
- `password_hash` - Bcrypt hashed password
- `name` - User name
- `created_at` - Registration timestamp

### Chats Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `title` - Chat title
- `created_at` - Chat creation timestamp
- `updated_at` - Last update timestamp

### Messages Table
- `id` - Primary key
- `chat_id` - Foreign key to chats
- `role` - 'user' or 'assistant'
- `content` - Message content
- `tool_outputs` - JSON of tool execution results
- `created_at` - Message timestamp

### UploadedFiles Table
- `id` - Primary key
- `filename` - Original filename
- `file_type` - MIME type
- `file_size` - File size in bytes
- `extracted_text` - Extracted content
- `user_id` - Foreign key
- `created_at` - Upload timestamp

---

## Security Features

- **JWT Authentication** - 7-day token expiry
- **Bcrypt Password Hashing** - Secure password storage
- **CORS Protection** - Configurable allowed origins
- **File Upload Validation** - Max 100MB, allowed types only
- **Filename Sanitization** - Prevents path traversal attacks

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
- [Semantic Scholar API](https://www.semanticscholar.org/product/api)
- [arXiv API](https://arxiv.org/help/api)
- [CrossRef API](https://www.crossref.org/services/metadata-delivery/rest-api/)
- [PubMed API](https://www.ncbi.nlm.nih.gov/home/develop/api.shtml)
