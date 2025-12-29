"""
Logging Configuration Module

Provides structured JSON logging with different log levels,
file rotation, and request/response logging.
"""

import os
import sys
import json
import logging
import logging.config
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from functools import wraps
import threading

from ..core.config import get_settings


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs as JSON objects with consistent structure.
    """

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data") and self.include_extra:
            log_data["extra"] = record.extra_data

        # Add request context if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        return json.dumps(log_data, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Console formatter with colored output for development.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",   # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color."""
        color = self.COLORS.get(record.levelname, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


class RequestContextFilter(logging.Filter):
    """
    Logging filter that adds request context to log records.
    """

    def __init__(self):
        super().__init__()
        self._context: threading.local = threading.local()

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        if hasattr(self._context, "data"):
            record.request_id = getattr(self._context, "request_id", None)
            record.user_id = getattr(self._context, "user_id", None)

        return True

    def set_context(self, request_id: Optional[str] = None, user_id: Optional[int] = None):
        """Set context for current thread."""
        self._context.request_id = request_id
        self._context.user_id = user_id

    def clear_context(self):
        """Clear context for current thread."""
        self._context.request_id = None
        self._context.user_id = None


# Global context filter
_context_filter = RequestContextFilter()


class LoggerSetup:
    """
    Logger setup and configuration manager.
    """

    _instance: Optional['LoggerSetup'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._loggers: Dict[str, logging.Logger] = {}

    def setup(
        self,
        log_level: Optional[str] = None,
        log_file: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
        json_format: bool = True,
        include_extra: bool = True
    ) -> None:
        """
        Configure application logging.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            max_bytes: Maximum log file size before rotation
            backup_count: Number of backup files to keep
            json_format: Use JSON formatting (False for development)
            include_extra: Include extra fields in JSON output
        """
        settings = get_settings()
        level = log_level or settings.log_level
        log_format = settings.log_format

        # Convert string level to int
        numeric_level = getattr(logging, level.upper(), logging.INFO)

        # Create formatters
        if json_format:
            formatter = JSONFormatter(include_extra=include_extra)
        else:
            formatter = ColoredConsoleFormatter()

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(numeric_level)
        root_logger.addHandler(console_handler)

        # File handler with rotation
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(numeric_level)
            root_logger.addHandler(file_handler)

        # Add context filter to all handlers
        for handler in root_logger.handlers:
            handler.addFilter(_context_filter)

        # Suppress noisy loggers
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a named logger."""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]

    def set_request_context(self, request_id: Optional[str] = None, user_id: Optional[int] = None):
        """Set context for current request."""
        _context_filter.set_context(request_id=request_id, user_id=user_id)

    def clear_request_context(self):
        """Clear request context."""
        _context_filter.clear_context()


def setup_logging(**kwargs) -> None:
    """Setup application logging."""
    LoggerSetup().setup(**kwargs)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return LoggerSetup().get_logger(name)


def log_request(logger: logging.Logger):
    """
    Decorator to log function calls with arguments.

    Usage:
        @log_request(logger)
        def my_function(arg1, arg2):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"Entering {func_name} with args={args}, kwargs={kwargs}")

            try:
                result = await func(*args, **kwargs)
                logger.debug(f"Exiting {func_name} successfully")
                return result
            except Exception as e:
                logger.error(f"Exception in {func_name}: {str(e)}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"Entering {func_name} with args={args}, kwargs={kwargs}")

            try:
                result = func(*args, **kwargs)
                logger.debug(f"Exiting {func_name} successfully")
                return result
            except Exception as e:
                logger.error(f"Exception in {func_name}: {str(e)}")
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class RequestLogger:
    """
    Request/response logging middleware.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger("request")

    def log_request(
        self,
        request_id: str,
        method: str,
        path: str,
        user_id: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log incoming request."""
        self.logger.info(
            f"{method} {path}",
            extra={
                "event": "request",
                "request_id": request_id,
                "user_id": user_id,
                **(extra or {})
            }
        )

    def log_response(
        self,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log outgoing response."""
        level = logging.INFO if status_code < 400 else logging.WARNING

        self.logger.log(
            level,
            f"{method} {path} -> {status_code} ({duration_ms:.2f}ms)",
            extra={
                "event": "response",
                "request_id": request_id,
                "user_id": user_id,
                "status_code": status_code,
                "duration_ms": duration_ms,
                **(extra or {})
            }
        )


# Initialize logging on module import
def _initialize_logging():
    """Initialize default logging configuration."""
    settings = get_settings()
    log_format = settings.log_format if hasattr(settings, 'log_format') else "json"

    setup_logging(
        log_level=settings.log_level if hasattr(settings, 'log_level') else "INFO",
        log_file=None,  # Set to a file path if needed
        json_format=(log_format == "json")
    )


# Lazy initialization
_LoggerSetup = None


def get_logger_setup() -> LoggerSetup:
    """Get logger setup instance."""
    global _LoggerSetup
    if _LoggerSetup is None:
        _LoggerSetup = LoggerSetup()
    return _LoggerSetup
