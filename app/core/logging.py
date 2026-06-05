"""Structured JSON logging powered by *structlog*.

Call ``setup_logging()`` once at application startup.  Then obtain loggers
via ``get_logger(__name__)`` in any module.

Every log entry automatically includes the bound ``request_id`` when one
has been set on the context (see ``RequestIDMiddleware``).
"""

from __future__ import annotations

import logging
import sys

import structlog


def setup_logging(*, log_level: str = "INFO", json_output: bool = True) -> None:
    """Configure *structlog* and the stdlib root logger.

    Parameters
    ----------
    log_level:
        Minimum severity (``DEBUG``, ``INFO``, ``WARNING``, …).
    json_output:
        When ``True`` (default, production), renders logs as JSON lines.
        Set to ``False`` for coloured human-readable output during
        local development.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Quieten noisy third-party loggers
    for noisy in ("uvicorn.access", "httpcore", "httpx", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a *structlog* bound logger for the given module name.

    Usage::

        logger = get_logger(__name__)
        logger.info("user_logged_in", user_id=user.id)
    """
    return structlog.get_logger(name)


def bind_request_id(request_id: str) -> None:
    """Bind a ``request_id`` into the structlog context-vars so that
    every subsequent log line in the same async task includes it.

    Typically called from ``RequestIDMiddleware``.
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
