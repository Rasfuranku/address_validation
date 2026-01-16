from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from app.schemas import APIResponse, ErrorDetail
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.api.v1.router import api_router
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield

app = FastAPI(
    title="Address Validation Service",
    description="Microservice to validate and standardize US addresses.",
    version="0.1.0",
    lifespan=lifespan
)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse[None](
            success=False,
            error=ErrorDetail(code=exc.status_code, message=exc.message, type=exc.error_code)
        ).model_dump()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=APIResponse[None](
            success=False,
            error=ErrorDetail(code=422, message="Validation Error", type="validation_error")
        ).model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled Exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content=APIResponse[None](
            success=False,
            error=ErrorDetail(code=500, message="Internal Server Error", type="server_error")
        ).model_dump()
    )

app.include_router(api_router, prefix="/v1")
