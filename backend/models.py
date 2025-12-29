# Database Models

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes for faster queries
    __table_args__ = (
        Index("ix_users_email_created", "email", "created_at"),
    )

    # Relationships
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_shared = Column(Boolean, default=False)
    share_token = Column(String(64), nullable=True, unique=True, index=True)

    # Indexes for faster queries
    __table_args__ = (
        Index("ix_chats_user_updated", "user_id", "updated_at"),
        Index("ix_chats_user_created", "user_id", "created_at"),
    )

    # Relationships
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    tool_outputs = Column(Text, nullable=True)  # JSON string of tool outputs for "Show Thinking"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes for faster queries
    __table_args__ = (
        Index("ix_messages_chat_created", "chat_id", "created_at"),
        Index("ix_messages_role_created", "role", "created_at"),
    )

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    files = relationship("UploadedFile", back_populates="message", cascade="all, delete-orphan")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, word, audio, image, pptx
    file_path = Column(String(500), nullable=False)
    extracted_text = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_uploaded_files_message", "message_id"),
        Index("ix_uploaded_files_type", "file_type"),
    )

    # Relationships
    message = relationship("Message", back_populates="files")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paper_title = Column(String(500), nullable=False)
    paper_url = Column(String(1000), nullable=True)
    paper_doi = Column(String(100), nullable=True)
    paper_authors = Column(Text, nullable=True)  # JSON array of authors
    paper_abstract = Column(Text, nullable=True)
    paper_year = Column(Integer, nullable=True)
    paper_citations = Column(Integer, default=0)
    paper_source = Column(String(50), nullable=True)  # semantic_scholar, arxiv, pubmed, doi
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # Comma-separated tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_bookmarks_user_created", "user_id", "created_at"),
        Index("ix_bookmarks_user_tags", "user_id", "tags"),
        Index("ix_bookmarks_doi", "paper_doi"),
    )

    # Relationships
    user = relationship("User", back_populates="bookmarks")


class ResearchNote(Base):
    __tablename__ = "research_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default="general")  # general, key_finding, methodology, limitation, idea, question
    tags = Column(Text, nullable=True)  # Comma-separated tags
    page_reference = Column(Text, nullable=True)  # Reference to specific page/position
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_notes_user_created", "user_id", "created_at"),
        Index("ix_notes_user_type", "user_id", "note_type"),
        Index("ix_notes_chat", "chat_id"),
    )
