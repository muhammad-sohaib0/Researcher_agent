# Pydantic Schemas

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


# ============ Auth Schemas ============
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ============ Chat Schemas ============
class ChatCreate(BaseModel):
    title: Optional[str] = "New Chat"


class ChatResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatListResponse(BaseModel):
    chats: List[ChatResponse]


# ============ Message Schemas ============
class MessageCreate(BaseModel):
    content: str
    file_ids: Optional[List[int]] = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    tool_outputs: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatWithMessages(BaseModel):
    id: int
    title: str
    messages: List[MessageResponse]
    
    class Config:
        from_attributes = True


# ============ File Schemas ============
class FileUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    extracted_text: Optional[str] = None
    
    class Config:
        from_attributes = True
