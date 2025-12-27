# Research Agent Web Application - Startup Guide

## Quick Start

### 1. Start Backend (Terminal 1)
```powershell
cd d:\project2\project\backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend (Terminal 2)
```powershell
cd d:\project2\project\frontend
npm run dev
```

### 3. Open Browser
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Features

### 🏠 Landing Page (http://localhost:3000)
- Hero section with AI capabilities
- Features showcase
- "Get Started" button → Auth page

### 🔐 Authentication (http://localhost:3000/auth)
- Login/Signup toggle
- JWT-based authentication
- Redirects to chat on success

### 💬 Chat Interface (http://localhost:3000/chat)
- Sidebar with chat history
- New chat button
- Text input with file upload (➕ button)
- "Show Thinking" expandable for tool outputs
- Download options (Word/PDF/Voice)

### 📤 File Upload
Supports: PDF, Word, PowerPoint, Images, Audio

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/signup` | POST | Register new user |
| `/api/auth/login` | POST | Login and get token |
| `/api/auth/me` | GET | Get current user |
| `/api/chat/list` | GET | Get all chats |
| `/api/chat/new` | POST | Create new chat |
| `/api/chat/{id}` | GET | Get chat with messages |
| `/api/chat/{id}/message` | POST | Send message (streaming) |
| `/api/files/upload` | POST | Upload and process file |
