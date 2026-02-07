import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Healthcare RAG MVP"
    API_V1_STR: str = "/api/v1"
    
    OPENAI_API_KEY: str
    CHROMA_PERSIST_DIRECTORY: str = "./data/vector_db"
    DOCS_DIRECTORY: str = "./data/docs"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_MODEL: str = "gpt-4-turbo-preview"

    # Observability
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = "ls__..."  # Placeholder
    LANGCHAIN_PROJECT: str = "healthcare-rag-mvp"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
