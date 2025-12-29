"""Core module exports."""

from .config import get_settings, Settings
from .cache import get_cache, get_paper_cache, get_search_cache, cached
from .rate_limit import get_rate_limiter, rate_limit_dependency, UserRateLimit
from .logging import setup_logging, get_logger, RequestLogger

__all__ = [
    "get_settings",
    "Settings",
    "get_cache",
    "get_paper_cache",
    "get_search_cache",
    "cached",
    "get_rate_limiter",
    "rate_limit_dependency",
    "UserRateLimit",
    "setup_logging",
    "get_logger",
    "RequestLogger"
]
