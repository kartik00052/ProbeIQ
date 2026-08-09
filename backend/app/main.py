from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.interview import router
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import ProbeIQError

APP_NAME = "ProbeIQ Interview API"


def _error_response(status_code: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": code, "detail": detail})


def _configure_cors(app: FastAPI) -> None:
    """Explicit, environment-configured CORS.

    Origins come from PROBEIQ_CORS_ALLOWED_ORIGINS (comma-separated). No
    wildcard: only the listed frontend origin(s) may call the API. Credentials
    are enabled because authentication uses an HTTP-only session cookie.
    """
    origins = settings.cors_origins
    if not origins:
        return
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
        max_age=86400,
    )


def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version="0.1.0")

    _configure_cors(app)
    init_db()

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(422, "invalid_request", "Request body is invalid or missing required fields.")

    @app.exception_handler(ProbeIQError)
    async def app_error_handler(request: Request, exc: ProbeIQError) -> JSONResponse:
        return _error_response(exc.status_code, exc.code, exc.detail)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(500, "internal_error", "An internal error occurred.")

    app.include_router(auth_router)
    app.include_router(router)
    return app


app = create_app()
