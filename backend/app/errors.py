# backend/app/errors.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

def _payload(request: Request, code: str, message):
    rid = getattr(request.state, "request_id", None)
    return {"request_id": rid, "error": {"code": code, "message": message}}

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=_payload(request, code=f"http_{exc.status_code}", message=exc.detail),
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=_payload(request, code="validation_error", message=exc.errors()),
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=_payload(request, code="internal_error", message="Unexpected server error"),
    )