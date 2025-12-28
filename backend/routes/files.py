# File Upload Routes

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models import User, UploadedFile
from schemas import FileUploadResponse
from auth import get_current_user
from pathlib import Path
import uuid
import os
import shutil

router = APIRouter()

# Upload directory
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# Lazy load tools to avoid slow startup
def get_tools():
    from tools import read_pdf_tool, read_word_tool, read_pptx_tool, read_image_tool, extract_audio_tool
    return {
        "pdf": read_pdf_tool,
        "word": read_word_tool,
        "pptx": read_pptx_tool,
        "image": read_image_tool,
        "audio": extract_audio_tool
    }


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process a file with validation."""

    # FILE SIZE LIMIT: 100 MB
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is 100 MB. Your file: {file_size / (1024*1024):.1f} MB")

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Validate file type
    valid_types = ["pdf", "word", "audio", "image", "pptx"]
    if file_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Must be one of: {valid_types}")

    # Validate file extension
    allowed_extensions = {
        "pdf": [".pdf"],
        "word": [".doc", ".docx"],
        "audio": [".mp3", ".wav", ".m4a", ".ogg"],
        "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
        "pptx": [".ppt", ".pptx"]
    }

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions.get(file_type, []):
        raise HTTPException(status_code=400, detail=f"Invalid file extension for {file_type}. Allowed: {allowed_extensions[file_type]}")

    # Sanitize filename - prevent path traversal
    import re
    safe_original_name = re.sub(r'[^\w\s.-]', '_', file.filename)

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Extract text based on file type (lazy load)
    extracted_text = ""
    try:
        tools = get_tools()
        if file_type in tools:
            extracted_text = tools[file_type](str(file_path))
    except Exception as e:
        extracted_text = f"Error extracting text: {str(e)}"
    
    # Save to database
    uploaded_file = UploadedFile(
        filename=unique_filename,
        original_filename=file.filename,
        file_type=file_type,
        file_path=str(file_path),
        extracted_text=extracted_text,
        file_size=os.path.getsize(file_path)
    )
    
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)
    
    return uploaded_file


@router.get("/{file_id}", response_model=FileUploadResponse)
async def get_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file info."""
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a file."""
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete physical file
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception:
        pass
    
    # Delete from database
    db.delete(file)
    db.commit()
    
    return {"message": "File deleted"}


@router.get("/download/{filename:path}")
async def download_research_file(filename: str):
    """
    Download a research paper from project downloads folder.
    """
    from fastapi.responses import FileResponse

    # Project downloads folder (where agent saves files)
    downloads_folder = Path(__file__).parent.parent.parent / "downloads"

    # Clean filename - remove any path traversal attempts
    safe_filename = Path(filename).name
    file_path = downloads_folder / safe_filename

    # Check if file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {safe_filename}")

    # Determine media type
    media_type = "application/octet-stream"
    if safe_filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif safe_filename.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif safe_filename.endswith(".pptx"):
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    elif safe_filename.endswith(".wav"):
        media_type = "audio/wav"
    elif safe_filename.endswith(".mp3"):
        media_type = "audio/mpeg"

    # Return file for download
    return FileResponse(
        path=str(file_path),
        filename=safe_filename,
        media_type=media_type
    )


@router.get("/list")
async def list_downloaded_files():
    """List all downloaded research papers."""
    downloads_folder = Path(__file__).parent.parent.parent / "downloads"
    downloads_folder.mkdir(exist_ok=True)

    files = []
    for f in downloads_folder.iterdir():
        if f.is_file():
            files.append({
                "filename": f.name,
                "size": f.stat().st_size,
                "download_link": f"/api/files/download/{f.name}"
            })

    return {"files": files}

