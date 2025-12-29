"""
Background Tasks Service

Handles background processing of PDFs, file downloads, and notifications.
Uses asyncio for non-blocking operations.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a background task."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackgroundTask:
    """Represents a background task."""
    id: str
    task_type: str
    status: TaskStatus
    progress: float = 0.0
    message: str = ""
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class BackgroundTaskManager:
    """
    Manages background tasks with progress tracking.

    Provides a queue for PDF processing, file downloads, and notifications.
    """

    _instance: Optional['BackgroundTaskManager'] = None
    _tasks: Dict[str, BackgroundTask] = {}
    _task_queue: asyncio.Queue = asyncio.Queue()
    _worker_task: Optional[asyncio.Task] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tasks = {}
        self._task_queue = asyncio.Queue()
        self._worker_task = None

    def start(self) -> None:
        """Start the background task worker."""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._process_queue())
            logger.info("Background task worker started")

    def stop(self) -> None:
        """Stop the background task worker."""
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                self._worker_task.result()
            except asyncio.CancelledError:
                pass
            logger.info("Background task worker stopped")

    def submit_task(
        self,
        task_type: str,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Submit a task to the background queue.

        Args:
            task_type: Type of task (pdf_processing, file_download, email_notification)
            task_id: Optional custom task ID
            **kwargs: Task-specific parameters

        Returns:
            Task ID for tracking
        """
        import uuid
        task_id = task_id or f"{task_type}_{uuid.uuid4().hex[:8]}"

        task = BackgroundTask(
            id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            message="Task queued",
            created_at=datetime.utcnow()
        )
        self._tasks[task_id] = task

        # Add to queue
        self._task_queue.put_nowait({
            "task_id": task_id,
            "task_type": task_type,
            "kwargs": kwargs
        })

        return task_id

    async def _process_queue(self) -> None:
        """Process tasks from the queue."""
        while True:
            try:
                item = await self._task_queue.get()

                task_id = item["task_id"]
                task_type = item["task_type"]
                kwargs = item["kwargs"]

                task = self._tasks.get(task_id)
                if task:
                    task.status = TaskStatus.PROCESSING
                    task.message = f"Processing {task_type}"

                try:
                    result = await self._execute_task(task_type, kwargs)

                    task = self._tasks.get(task_id)
                    if task:
                        task.status = TaskStatus.COMPLETED
                        task.progress = 1.0
                        task.message = "Task completed"
                        task.result = result
                        task.completed_at = datetime.utcnow()

                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")

                    task = self._tasks.get(task_id)
                    if task:
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
                        task.message = f"Task failed: {str(e)}"

                self._task_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing task: {e}")

    async def _execute_task(self, task_type: str, kwargs: Dict) -> Any:
        """Execute a specific task type."""
        handlers = {
            "pdf_processing": self._process_pdf,
            "file_download": self._download_file,
            "email_notification": self._send_email,
        }

        handler = handlers.get(task_type)
        if not handler:
            raise ValueError(f"Unknown task type: {task_type}")

        return await handler(**kwargs)

    async def _process_pdf(self, file_path: str, callback: Optional[Callable] = None) -> str:
        """
        Process PDF file in background.

        Args:
            file_path: Path to PDF file
            callback: Optional progress callback

        Returns:
            Extracted text content
        """
        # Import here to avoid circular imports
        from tools import read_pdf_tool

        async def update_progress(progress: float, message: str):
            if callback:
                await callback(progress, message)

        await update_progress(0.1, "Opening PDF...")
        result = read_pdf_tool(file_path)
        await update_progress(1.0, "PDF processing complete")
        return result

    async def _download_file(
        self,
        url: str,
        destination: str,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Download file in background with progress tracking.

        Args:
            url: URL to download
            destination: Local destination path
            callback: Optional progress callback

        Returns:
            Local file path
        """
        import httpx

        async def update_progress(progress: float, message: str):
            if callback:
                await callback(progress, message)

        await update_progress(0.0, "Starting download...")

        async with httpx.AsyncClient(follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                destination_path = Path(destination)
                destination_path.parent.mkdir(parents=True, exist_ok=True)

                with open(destination_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = downloaded / total_size
                            await update_progress(progress, f"Downloading... {int(progress * 100)}%")

        await update_progress(1.0, "Download complete")
        return str(destination_path)

    async def _send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None
    ) -> bool:
        """
        Send email notification.

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            html: Optional HTML body

        Returns:
            True if sent successfully
        """
        # Email sending implementation
        # This is a placeholder - integrate with your email provider
        logger.info(f"Email notification to {to}: {subject}")
        return True

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list:
        """Get all tasks."""
        return list(self._tasks.values())

    def get_tasks_by_status(self, status: TaskStatus) -> list:
        """Get tasks by status."""
        return [t for t in self._tasks.values() if t.status == status]

    def clear_completed_tasks(self) -> int:
        """Clear completed/failed tasks older than 1 hour."""
        import time
        cutoff = time.time() - 3600  # 1 hour ago
        tasks_to_delete = [
            task_id for task_id, task in self._tasks.items()
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            and task.created_at.timestamp() < cutoff
        ]

        for task_id in tasks_to_delete:
            del self._tasks[task_id]

        return len(tasks_to_delete)

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop()
        self._tasks.clear()


# Global instance
_task_manager: Optional[BackgroundTaskManager] = None


def get_task_manager() -> BackgroundTaskManager:
    """Get global task manager instance."""
    global _task_manager
    if _task_manager is None:
        _task_manager = BackgroundTaskManager()
    return _task_manager


# Convenience functions for common tasks
async def process_pdf_background(
    file_path: str,
    callback: Optional[Callable] = None
) -> str:
    """
    Process PDF file in background.

    Args:
        file_path: Path to PDF file
        callback: Progress callback function

    Returns:
        Task ID for tracking
    """
    manager = get_task_manager()
    return manager.submit_task(
        "pdf_processing",
        file_path=file_path,
        callback=callback
    )


async def download_file_background(
    url: str,
    destination: str,
    callback: Optional[Callable] = None
) -> str:
    """
    Download file in background.

    Args:
        url: URL to download
        destination: Local destination path
        callback: Progress callback function

    Returns:
        Task ID for tracking
    """
    manager = get_task_manager()
    return manager.submit_task(
        "file_download",
        url=url,
        destination=destination,
        callback=callback
    )


async def send_notification_email(
    to: str,
    subject: str,
    body: str,
    html: Optional[str] = None
) -> str:
    """
    Send email notification in background.

    Args:
        to: Recipient email
        subject: Email subject
        body: Email body
        html: Optional HTML body

    Returns:
        Task ID for tracking
    """
    manager = get_task_manager()
    return manager.submit_task(
        "email_notification",
        to=to,
        subject=subject,
        body=body,
        html=html
    )
