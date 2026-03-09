from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.limiter import limiter
from app.api import routes

app = FastAPI(
    title="Healthcare RAG MVP",
    description="Secure, explainable RAG for healthcare policies and guidelines",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Allow all origins for demo purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(routes.router, prefix="/api/v1")

# Serve index.html at root
from fastapi.responses import FileResponse
@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/ready")
async def readiness_check():
    """Check if the service is ready to receive traffic."""
    try:
        from app.retrieval.vectorstore.ChromaWrapper import get_chroma_collections
        collections = get_chroma_collections()
        return {"status": "ready", "collections": len(collections)}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
