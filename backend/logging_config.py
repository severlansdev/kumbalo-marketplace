"""
KUMBALO Structured Logging Configuration
Provides JSON-formatted logging for all backend operations.
"""
import logging
import sys
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured log output."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        # Add extra fields
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "endpoint"):
            log_entry["endpoint"] = record.endpoint
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level=logging.INFO):
    """Configure structured JSON logging for the application."""
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(JSONFormatter())
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []
    root_logger.addHandler(console_handler)

    # Reduce noise from external libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return root_logger


# Application logger
logger = setup_logging()


def log_request(method: str, path: str, status: int, duration_ms: float, user_id: int = None):
    """Log an API request with structured data."""
    extra = {
        "endpoint": f"{method} {path}",
        "status_code": status,
        "duration_ms": round(duration_ms, 2),
    }
    if user_id:
        extra["user_id"] = user_id
    
    logger.info(
        f"{method} {path} → {status} ({duration_ms:.0f}ms)",
        extra=extra
    )


def log_error(message: str, exception=None, **extra_fields):
    """Log an error with optional exception and extra context."""
    logger.error(message, exc_info=exception, extra=extra_fields)


def log_event(event_name: str, **data):
    """Log a business event (e.g., user_registered, moto_published)."""
    logger.info(f"EVENT: {event_name} | {json.dumps(data, ensure_ascii=False)}")
