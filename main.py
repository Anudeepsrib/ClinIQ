import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import routes
from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import configure_logging, redact_text

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Hospital policy RAG reference app with HIPAA-aware control patterns; "
        "not certified compliance software"
    ),
    version="1.0.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(routes.router, prefix="/api/v1")


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    if settings.SECURITY_HEADERS_ENABLED:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:3000 http://127.0.0.1:3000 "
            "http://localhost:8000 http://127.0.0.1:8000",
        )
        if settings.is_production:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled request error on %s: %s", request.url.path, redact_text(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "external_tracing": settings.ENABLE_EXTERNAL_TRACING,
    }


@app.get("/ready")
async def readiness_check():
    """Check if the service is ready to receive traffic."""
    checks = {
        "api": "ready",
        "azure_search": "disabled" if not settings.AZURE_SEARCH_ENABLED else "configured",
        "chat_history": "disabled" if not settings.CHAT_HISTORY_ENABLED else "configured",
    }
    return {"status": "ready", "checks": checks}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1" if not settings.is_production else "0.0.0.0",
        port=8000,
        reload=not settings.is_production,
    )
