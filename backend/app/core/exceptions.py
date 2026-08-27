"""Custom exception hierarchy for ArthSaathi.

All domain exceptions extend ArthSaathiError and carry:
- ``code``: a machine-readable string error code (used in API error responses).
- ``message``: a human-readable description.
- ``http_status``: the HTTP status code the FastAPI exception handler should return.

Route handlers raise these domain exceptions; they do NOT construct HTTPException
directly (except for straightforward input-validation / 422 cases). The mapping
to HTTP responses is centralised in app/main.py's exception handler.
"""

from __future__ import annotations


class ArthSaathiError(Exception):
    """Base class for all ArthSaathi domain exceptions."""

    code: str = "INTERNAL_ERROR"
    http_status: int = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# ─── Auth & tenant ────────────────────────────────────────────────────────────


class AuthenticationError(ArthSaathiError):
    """Invalid or missing credentials."""

    code = "AUTHENTICATION_ERROR"
    http_status = 401


class AuthorizationError(ArthSaathiError):
    """Authenticated user lacks the required role."""

    code = "AUTHORIZATION_ERROR"
    http_status = 403


class TenantIsolationError(ArthSaathiError):
    """Attempted cross-tenant data access — treated as 404 to avoid leaking existence."""

    code = "NOT_FOUND"
    http_status = 404


# ─── Resource ─────────────────────────────────────────────────────────────────


class NotFoundError(ArthSaathiError):
    """Requested resource does not exist (or is not visible to this tenant)."""

    code = "NOT_FOUND"
    http_status = 404


class ConflictError(ArthSaathiError):
    """Uniqueness constraint violated (e.g., duplicate phone_number on register)."""

    code = "CONFLICT"
    http_status = 409


class ValidationError(ArthSaathiError):
    """Business-rule validation failed (distinct from Pydantic/422 input validation)."""

    code = "VALIDATION_ERROR"
    http_status = 422


# ─── File upload ──────────────────────────────────────────────────────────────


class FileTooLargeError(ArthSaathiError):
    """Uploaded file exceeds the 5 MB limit."""

    code = "FILE_TOO_LARGE"
    http_status = 413


class UnsupportedMediaTypeError(ArthSaathiError):
    """Uploaded file MIME type is not PDF, JPEG, or PNG."""

    code = "UNSUPPORTED_MEDIA_TYPE"
    http_status = 415


class OcrIllegibleError(ArthSaathiError):
    """Tesseract returned no usable text from the uploaded document."""

    code = "OCR_ILLEGIBLE"
    http_status = 422


# ─── Agent execution ──────────────────────────────────────────────────────────


class AgentExecutionError(ArthSaathiError):
    """A LangGraph agent graph raised an unrecoverable error during execution."""

    code = "AGENT_EXECUTION_ERROR"
    http_status = 500


class RateLimitError(ArthSaathiError):
    """Rate limit exceeded (e.g., too many login attempts)."""

    code = "RATE_LIMIT_EXCEEDED"
    http_status = 429
