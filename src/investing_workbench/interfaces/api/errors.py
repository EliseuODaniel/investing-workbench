"""Helpers for translating application errors into HTTP responses."""

from __future__ import annotations

import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def to_http_exception(exc: Exception) -> HTTPException:
    """Translate application exceptions into a consistent HTTP response."""
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, NotImplementedError):
        return HTTPException(status_code=501, detail=str(exc))

    logger.exception("Unhandled application error", exc_info=exc)
    return HTTPException(status_code=500, detail="Internal server error")
