from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
import logging
import uuid
from typing import Union, List, Any

# Configurar logger
logger = logging.getLogger("sonqobase.errors")

def create_error_response(
    status_code: int,
    message: str,
    code: str = "ERROR",
    details: Union[List[str], Any] = None,
    path: str = ""
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
                "path": path,
                "request_id": str(uuid.uuid4()) # En producción, usar ID real del request
            }
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    """Manejador para errores no controlados (500)"""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Internal Server Error",
        code="INTERNAL_ERROR",
        path=request.url.path
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Manejador para HTTPExceptions (400, 401, 403, 404, etc)"""
    return create_error_response(
        status_code=exc.status_code,
        message=exc.detail,
        code=f"HTTP_{exc.status_code}",
        path=request.url.path
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejador para errores de validación de Pydantic (422)"""
    details = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"])
        msg = error["msg"]
        details.append(f"{field}: {msg}")

    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation Error",
        code="VALIDATION_ERROR",
        details=details,
        path=request.url.path
    )
