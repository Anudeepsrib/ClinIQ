from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api import routes

app = FastAPI(
    title="Healthcare RAG MVP",
    description="Secure, explainable RAG for healthcare policies and guidelines",
    version="1.0.0"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
