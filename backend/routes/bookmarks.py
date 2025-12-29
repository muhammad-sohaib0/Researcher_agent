# Bookmark Routes
# API endpoints for paper bookmarking

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from database import get_db
from models import User, Bookmark, ResearchNote
from schemas import BaseModel
from auth import get_current_user

router = APIRouter()


# ============ Schemas ============

class BookmarkCreate(BaseModel):
    paper_title: str
    paper_url: Optional[str] = None
    paper_doi: Optional[str] = None
    paper_authors: Optional[str] = None
    paper_abstract: Optional[str] = None
    paper_year: Optional[int] = None
    paper_citations: Optional[int] = 0
    paper_source: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class BookmarkResponse(BaseModel):
    id: int
    paper_title: str
    paper_url: Optional[str]
    paper_doi: Optional[str]
    paper_authors: Optional[str]
    paper_abstract: Optional[str]
    paper_year: Optional[int]
    paper_citations: Optional[int]
    paper_source: Optional[str]
    notes: Optional[str]
    tags: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class BookmarkUpdate(BaseModel):
    notes: Optional[str] = None
    tags: Optional[str] = None


class ResearchNoteCreate(BaseModel):
    title: str
    content: str
    note_type: str = "general"
    tags: Optional[str] = None
    page_reference: Optional[str] = None
    chat_id: Optional[int] = None


class ResearchNoteResponse(BaseModel):
    id: int
    title: str
    content: str
    note_type: str
    tags: Optional[str]
    page_reference: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


# ============ Routes ============

@router.get("/bookmarks", response_model=List[BookmarkResponse])
async def get_bookmarks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tag: Optional[str] = None
):
    """Get all bookmarks for current user."""
    query = db.query(Bookmark).filter(Bookmark.user_id == current_user.id)

    if tag:
        # Filter by tag (tags are comma-separated)
        query = query.filter(Bookmark.tags.contains(tag))

    bookmarks = query.order_by(Bookmark.created_at.desc()).all()
    return bookmarks


@router.post("/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new bookmark."""
    # Check if already bookmarked
    if bookmark_data.paper_doi:
        existing = db.query(Bookmark).filter(
            Bookmark.user_id == current_user.id,
            Bookmark.paper_doi == bookmark_data.paper_doi
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paper already bookmarked"
            )

    bookmark = Bookmark(
        user_id=current_user.id,
        **bookmark_data.model_dump()
    )

    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)

    return bookmark


@router.get("/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(
    bookmark_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific bookmark."""
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == current_user.id
    ).first()

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    return bookmark


@router.put("/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: int,
    update_data: BookmarkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a bookmark."""
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == current_user.id
    ).first()

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    if update_data.notes is not None:
        bookmark.notes = update_data.notes
    if update_data.tags is not None:
        bookmark.tags = update_data.tags

    db.commit()
    db.refresh(bookmark)

    return bookmark


@router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a bookmark."""
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == current_user.id
    ).first()

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    db.delete(bookmark)
    db.commit()

    return {"message": "Bookmark deleted"}


@router.get("/bookmarks/search")
async def search_bookmarks(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search bookmarks by title or notes."""
    results = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id
    ).filter(
        (Bookmark.paper_title.ilike(f"%{query}%")) |
        (Bookmark.notes.ilike(f"%{query}%")) |
        (Bookmark.paper_abstract.ilike(f"%{query}%"))
    ).all()

    return {"results": results}


# ============ Research Notes Routes ============

@router.get("/notes", response_model=List[ResearchNoteResponse])
async def get_notes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    note_type: Optional[str] = None,
    chat_id: Optional[int] = None
):
    """Get all research notes for current user."""
    query = db.query(ResearchNote).filter(ResearchNote.user_id == current_user.id)

    if note_type:
        query = query.filter(ResearchNote.note_type == note_type)
    if chat_id:
        query = query.filter(ResearchNote.chat_id == chat_id)

    notes = query.order_by(ResearchNote.created_at.desc()).all()
    return notes


@router.post("/notes", response_model=ResearchNoteResponse)
async def create_note(
    note_data: ResearchNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new research note."""
    note = ResearchNote(
        user_id=current_user.id,
        **note_data.model_dump()
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a research note."""
    note = db.query(ResearchNote).filter(
        ResearchNote.id == note_id,
        ResearchNote.user_id == current_user.id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(note)
    db.commit()

    return {"message": "Note deleted"}
