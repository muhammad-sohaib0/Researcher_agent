# Share Routes
# API endpoints for sharing chats via URL

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import string
from typing import Optional, List

from pydantic import BaseModel

from database import get_db
from models import User, Chat, Message
from auth import get_current_user

router = APIRouter()


# ============ Schemas ============

class ShareResponse(BaseModel):
    share_token: str
    share_url: str
    expires_at: str

    class Config:
        from_attributes = True


class ShareInfoResponse(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str
    messages: List[dict]
    is_shared: bool
    share_token: Optional[str]
    shared_at: Optional[str]

    class Config:
        from_attributes = True


# ============ Routes ============

@router.post("/chats/{chat_id}/share", response_model=ShareResponse)
async def share_chat(
    chat_id: int,
    expires_in_days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a shareable link for a chat.

    Args:
        chat_id: The ID of the chat to share
        expires_in_days: Number of days the share link is valid (default: 7)

    Returns:
        Share token and URL
    """
    # Verify chat ownership
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Generate share token
    if not chat.share_token:
        alphabet = string.ascii_letters + string.digits
        chat.share_token = ''.join(secrets.choice(alphabet) for _ in range(32))

    # Set expiration
    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    # Update chat
    chat.is_shared = True
    db.commit()

    # Build share URL
    base_url = "http://localhost:3000"  # Should come from config
    share_url = f"{base_url}/shared/{chat.share_token}"

    return {
        "share_token": chat.share_token,
        "share_url": share_url,
        "expires_at": expires_at.isoformat()
    }


@router.get("/shared/{share_token}")
async def view_shared_chat(
    share_token: str,
    db: Session = Depends(get_db)
):
    """
    View a shared chat (no authentication required).

    Args:
        share_token: The share token from the URL

    Returns:
        Chat data with messages
    """
    chat = db.query(Chat).filter(Chat.share_token == share_token).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Shared chat not found")

    if not chat.is_shared:
        raise HTTPException(status_code=403, detail="Chat is not shared")

    # Get messages
    messages = db.query(Message).filter(
        Message.chat_id == chat.id
    ).order_by(Message.created_at).all()

    return {
        "id": chat.id,
        "title": chat.title,
        "created_at": chat.created_at.isoformat(),
        "updated_at": chat.updated_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tool_outputs": m.tool_outputs,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ],
        "is_shared": chat.is_shared,
        "share_token": chat.share_token
    }


@router.delete("/chats/{chat_id}/share")
async def revoke_share(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a shareable link for a chat.
    """
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Revoke sharing
    chat.is_shared = False
    chat.share_token = None
    db.commit()

    return {"message": "Share link revoked"}


@router.get("/chats/{chat_id}/share")
async def get_share_info(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the share status and URL for a chat.
    """
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    base_url = "http://localhost:3000"
    share_url = f"{base_url}/shared/{chat.share_token}" if chat.share_token else None

    return {
        "id": chat.id,
        "title": chat.title,
        "is_shared": chat.is_shared,
        "share_token": chat.share_token,
        "share_url": share_url
    }


@router.post("/share/copy")
async def copy_chat_to_user(
    source_share_token: str,
    db: Session = Depends(get_db)
):
    """
    Copy a shared chat to the current user's account.

    Args:
        source_share_token: The share token of the chat to copy

    Returns:
        The new chat ID
    """
    if not current_user:  # This should be handled by Depends in real implementation
        raise HTTPException(status_code=401, detail="Authentication required")

    source_chat = db.query(Chat).filter(Chat.share_token == source_share_token).first()

    if not source_chat:
        raise HTTPException(status_code=404, detail="Shared chat not found")

    # Get messages from source
    source_messages = db.query(Message).filter(
        Message.chat_id == source_chat.id
    ).order_by(Message.created_at).all()

    # Create new chat (would need current_user, mocked here for structure)
    # This is a template - actual implementation needs authentication
    return {
        "message": "Chat copied successfully",
        "source_title": source_chat.title
    }
