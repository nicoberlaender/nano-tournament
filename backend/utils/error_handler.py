from fastapi import HTTPException
from typing import Type, Optional
import httpx
from openai import OpenAIError


class DocumentationError(Exception):
    """Base class for documentation processing errors"""

    pass


class FetchError(DocumentationError):
    """Error when fetching documentation"""

    pass


class ProcessingError(DocumentationError):
    """Error when processing documentation"""

    pass


def handle_error(error: Exception) -> HTTPException:
    """Convert various exceptions to appropriate HTTP responses"""
    if isinstance(error, httpx.HTTPError):
        return HTTPException(
            status_code=503,
            detail="Failed to fetch documentation. Please check the URL and try again.",
        )
    elif isinstance(error, DocumentationError):
        return HTTPException(status_code=422, detail=str(error))
    elif isinstance(error, OpenAIError):
        return HTTPException(
            status_code=503,
            detail="Failed to generate explanation. Please try again later.",
        )
    else:
        return HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(error)}"
        )
