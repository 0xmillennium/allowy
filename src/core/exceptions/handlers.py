"""FastAPI exception handlers that convert exceptions to JSON error responses."""

import logging

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from src.core.exceptions.exceptions import AppError

logger = logging.getLogger(__name__)


async def handle_request_validation_error(
    request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    logger.error(
        "Request validation error",
        extra={
            "errors": errors,
            "method": request.method,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "msg": "Request validation failed",
            "type": "validation_error",
            "details": [
                {
                    "loc": list(e["loc"]),
                    "msg": e["msg"],
                    "type": e["type"],
                    "input": e.get("input"),
                }
                for e in errors
            ],
        },
    )


async def handle_validation_error(request, exc: ValidationError) -> JSONResponse:
    errors = exc.errors()
    logger.error(
        "Validation error",
        extra={
            "errors": errors,
            "method": request.method,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "msg": "Validation failed",
            "type": "validation_error",
            "details": [
                {
                    "loc": list(e["loc"]),
                    "msg": e["msg"],
                    "type": e["type"],
                    "input": e.get("input"),
                }
                for e in errors
            ],
        },
    )


async def handle_sqlalchemy_error(request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error(
        "Database error",
        extra={
            "error": str(exc),
            "method": request.method,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "msg": "A database error occurred",  # intentionally vague — security
            "type": "database_error",
        },
    )


async def handle_http_exception(request, exc: HTTPException) -> JSONResponse:
    logger.error(
        "HTTP error",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "method": request.method,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "code": exc.status_code,
            "msg": exc.detail,
            "type": "http_error",
        },
    )


async def handle_app_exception(request, exc: AppError) -> JSONResponse:
    logger.error(
        "Application error",
        extra={
            "error_type": exc.type,
            "error_msg": exc.msg,
            "method": request.method,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=exc.code,
        content={
            "code": exc.code,
            "msg": exc.msg,
            "type": exc.type,
        },
    )


async def handle_generic_error(request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unexpected error",
        extra={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "method": request.method,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "msg": "An unexpected error occurred",
            "type": "internal_error",
        },
    )


EXCEPTION_HANDLERS = {
    AppError: handle_app_exception,
    RequestValidationError: handle_request_validation_error,
    ValidationError: handle_validation_error,
    HTTPException: handle_http_exception,
    SQLAlchemyError: handle_sqlalchemy_error,
    Exception: handle_generic_error,
}
