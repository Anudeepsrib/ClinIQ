import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Healthcare RAG MVP"
    API_V1_STR: str = "/api/v1"

    OPENAI_API_KEY: str
    CHROMA_PERSIST_DIRECTORY: str = "./data/vector_db"
    DOCS_DIRECTORY: str = "./data/docs"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_MODEL: str = "gpt-4o"

    # --- JWT / Auth ---
    JWT_SECRET_KEY: str = "change-me-in-production-use-openssl-rand"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 480  # 8-hour workday
    USERS_DB_PATH: str = "./data/users.db"

    # --- Hospital departments (configurable per deployment) ---
    HOSPITAL_DEPARTMENTS: str = (
        "radiology,pharmacy,administration,nursing,laboratory,"
        "emergency,cardiology,oncology,orthopedics,pediatrics,general"
    )

    # Observability
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = "ls__..."  # Placeholder
    LANGCHAIN_PROJECT: str = "ClinIQ-Hospital-Beta"

    # --- RAG pipeline ---
    MAX_QUERY_RETRIES: int = 3

    @property
    def departments_list(self) -> List[str]:
        """Returns the hospital departments as a cleaned list."""
        return [d.strip().lower() for d in self.HOSPITAL_DEPARTMENTS.split(",") if d.strip()]

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
