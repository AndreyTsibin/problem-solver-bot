"""
Production-ready logging configuration using structlog.

Features:
- JSON logging in production, pretty console in development
- Automatic log rotation (10MB per file, 5 backups)
- Separate logs: app.log (INFO+), error.log (ERROR+), debug.log (DEBUG, dev only)
- Structured logging with user context via contextvars
- SQLAlchemy query logging control per environment
"""

import sys
import logging.config
from pathlib import Path
import structlog
from bot.config import ENVIRONMENT, LOG_LEVEL


def setup_logging():
    """
    Configure production-ready logging system.

    Dev mode:
        - Colored console output (human-readable)
        - Debug file with all logs
        - SQLAlchemy queries visible

    Production mode:
        - JSON format for machine parsing
        - Rotating file handlers (max 50MB total)
        - Minimal SQLAlchemy logging
    """

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    is_dev = ENVIRONMENT == "development"

    # Timestamper for structured logs
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    # Pre-chain processors for foreign (non-structlog) logs
    pre_chain = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.ExtraAdder(),
        timestamper,
    ]

    # Configure Python's standard logging
    handlers_config = {
        "console": {
            "level": "DEBUG" if is_dev else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "console",
            "stream": sys.stdout,
        },
        "app_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/app.log",
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "json" if not is_dev else "console",
            "encoding": "utf-8",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/error.log",
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 3,
            "formatter": "json",
            "encoding": "utf-8",
        },
    }

    # Add debug file handler only in development
    if is_dev:
        handlers_config["debug_file"] = {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "logs/debug.log",
            "formatter": "console",
            "encoding": "utf-8",
        }

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(),
                ],
                "foreign_pre_chain": pre_chain,
            },
            "console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=True),
                ],
                "foreign_pre_chain": pre_chain,
            },
        },

        "handlers": handlers_config,

        "loggers": {
            # Bot application logs
            "bot": {
                "handlers": ["console", "app_file", "error_file"] + (["debug_file"] if is_dev else []),
                "level": LOG_LEVEL,
                "propagate": False,
            },
            # SQLAlchemy logs (reduce noise in production)
            "sqlalchemy.engine": {
                "handlers": ["error_file"] if not is_dev else ["console", "debug_file"],
                "level": "WARNING" if is_dev else "ERROR",
                "propagate": False,
            },
            # Aiogram logs
            "aiogram": {
                "handlers": ["console", "app_file", "error_file"],
                "level": "INFO",
                "propagate": False,
            },
        },

        "root": {
            "handlers": ["console", "app_file", "error_file"],
            "level": "WARNING",
        },
    })

    # Configure structlog
    structlog.configure(
        processors=[
            # Merge thread-local context (user_id, session_id, etc.)
            structlog.contextvars.merge_contextvars,
            # Filter by log level early
            structlog.stdlib.filter_by_level,
            # Add log level name
            structlog.stdlib.add_log_level,
            # Add logger name
            structlog.stdlib.add_logger_name,
            # Support %-style formatting
            structlog.stdlib.PositionalArgumentsFormatter(),
            # Render stack traces
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.processors.format_exc_info,
            # Decode bytes to unicode
            structlog.processors.UnicodeDecoder(),
            # Add timestamp
            timestamper,
            # Prepare for ProcessorFormatter
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.INFO if not is_dev else logging.DEBUG
        ),
        cache_logger_on_first_use=True,
    )
