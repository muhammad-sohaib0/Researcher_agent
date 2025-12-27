# Chat Routes

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import User, Chat, Message, UploadedFile
from schemas import ChatCreate, ChatResponse, ChatListResponse, MessageCreate, MessageResponse, ChatWithMessages
from auth import get_current_user
from typing import List
import json

# Lazy import for agent_engine (heavy module)
def get_agent_stream():
    from agent_engine import run_agent_stream
    return run_agent_stream

router = APIRouter()


@router.get("/list", response_model=ChatListResponse)
async def get_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chats for current user."""
    chats = db.query(Chat).filter(Chat.user_id == current_user.id).order_by(desc(Chat.updated_at)).all()
    return ChatListResponse(chats=chats)


@router.post("/new", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat."""
    new_chat = Chat(
        user_id=current_user.id,
        title=chat_data.title or "New Chat"
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat


@router.get("/{chat_id}", response_model=ChatWithMessages)
async def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a chat with all messages."""
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat."""
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    db.delete(chat)
    db.commit()
    return {"message": "Chat deleted"}


@router.post("/{chat_id}/message")
async def send_message(
    chat_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get streaming response."""
    # Verify chat ownership
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get uploaded files if attached
    uploaded_file_paths = []
    if message_data.file_ids:
        files = db.query(UploadedFile).filter(UploadedFile.id.in_(message_data.file_ids)).all()
        for f in files:
            uploaded_file_paths.append({
                "filename": f.original_filename,
                "path": f.file_path,
                "type": f.file_type
            })

    # Build full message content with file instructions
    full_content = message_data.content
    if uploaded_file_paths:
        file_instructions = []
        for file_info in uploaded_file_paths:
            file_instructions.append(f"User uploaded a {file_info['type']} file: {file_info['filename']}")
            file_instructions.append(f"File path: {file_info['path']}")

        full_content = "\n".join(file_instructions) + "\n\n" + message_data.content

        # If no explicit question, auto-generate one
        if not message_data.content or message_data.content.strip() == "":
            full_content = "\n".join(file_instructions) + "\n\nPlease read and summarize this file."
    
    # Save user message
    user_message = Message(
        chat_id=chat_id,
        role="user",
        content=message_data.content
    )
    db.add(user_message)
    db.commit()
    
    # Link files to message
    if message_data.file_ids:
        db.query(UploadedFile).filter(UploadedFile.id.in_(message_data.file_ids)).update(
            {"message_id": user_message.id}, synchronize_session=False
        )
        db.commit()
    
    # Update chat title if first message
    messages_count = db.query(Message).filter(Message.chat_id == chat_id).count()
    if messages_count == 1:
        # Set title from first message
        title = message_data.content[:50] + "..." if len(message_data.content) > 50 else message_data.content
        chat.title = title
        db.commit()
    
    # Get FULL chat history for context (all previous messages)
    history = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at).all()
    # Include all messages except the current one we just added
    previous_messages = history[:-1] if len(history) > 0 else []
    conversation = [{"role": msg.role, "content": msg.content} for msg in previous_messages]
    
    # Stream response
    async def generate():
        tool_outputs = []
        final_response = ""
        
        async for event_type, content in get_agent_stream()(full_content, conversation):
            if event_type == "tool_call":
                tool_outputs.append(content)
                yield f"data: {json.dumps({'type': 'tool', 'content': content})}\n\n"
            elif event_type == "response":
                final_response += content
                yield f"data: {json.dumps({'type': 'response', 'content': content})}\n\n"
            elif event_type == "done":
                # Save assistant message
                assistant_message = Message(
                    chat_id=chat_id,
                    role="assistant",
                    content=final_response,
                    tool_outputs=json.dumps(tool_outputs) if tool_outputs else None
                )
                db.add(assistant_message)
                db.commit()
                yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.put("/{chat_id}/title")
async def update_chat_title(
    chat_id: int,
    title: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update chat title."""
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat.title = title
    db.commit()
    return {"message": "Title updated"}
