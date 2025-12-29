# Backend FastAPI Application
# Modular architecture with organized structure

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from database import engine, Base
from core.config import get_settings
from core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("main")

# Import routers
from routes import auth, chat, files
from routes import bookmarks, share

# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Research Agent API...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    yield
    # Shutdown
    logger.info("Shutting down Research Agent API...")

app = FastAPI(
    title="Research Agent API",
    description="AI-powered research assistant with document processing, paper search, and research tools",
    version="2.0.0",
    lifespan=lifespan
)

# Get settings for CORS
settings = get_settings()
allowed_origins = settings.allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(bookmarks.router, prefix="/api", tags=["Bookmarks & Notes"])
app.include_router(share.router, prefix="/api", tags=["Sharing"])


@app.get("/")
async def root():
    return {
        "message": "Research Agent API",
        "status": "running",
        "version": "2.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check database connection
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy",
        "database": db_status
    }


@app.get("/api/chat/search")
async def search_chat_messages(
    q: str,
    chat_id: int = None,
    current_user = None
):
    """
    Search through chat messages.

    Args:
        q: Search query
        chat_id: Optional specific chat to search in
        current_user: Authenticated user

    Returns:
        Matching messages with highlighted content
    """
    from database import get_db
    from models import Chat, Message

    db = next(get_db())
    try:
        # Build query
        query = db.query(Message).join(Chat).filter(
            Chat.user_id == current_user.id
        )

        if chat_id:
            query = query.filter(Message.chat_id == chat_id)

        # Search in content
        messages = query.filter(
            Message.content.ilike(f"%{q}%")
        ).order_by(Message.created_at.desc()).limit(50).all()

        results = []
        for msg in messages:
            # Get chat title
            chat = db.query(Chat).filter(Chat.id == msg.chat_id).first()

            # Simple highlighting (in production, use more sophisticated highlighting)
            highlighted = msg.content.replace(
                q, f"<mark>{q}</mark>"
            )

            results.append({
                "message_id": msg.id,
                "chat_id": msg.chat_id,
                "chat_title": chat.title if chat else "Unknown",
                "role": msg.role,
                "content": msg.content,
                "highlighted_content": highlighted,
                "created_at": msg.created_at.isoformat()
            })

        return {
            "query": q,
            "total_results": len(results),
            "results": results
        }

    finally:
        db.close()
