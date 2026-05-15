import os
from typing import List, Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ClinIQ"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"
    DEBUG: bool = False

    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    CHROMA_PERSIST_DIRECTORY: str = "./data/vector_db"
    DOCS_DIRECTORY: str = "./data/docs"
    EMBEDDING_MODEL: str = "multimodal-embedding-002"  # Gemini 2 Stable or text-embedding-3-small
    EMBEDDING_PROVIDER: str = "gemini"  # "gemini" | "openai"
    EMBEDDING_DIMENSIONS: int = 3072  # Gemini 2 / OpenAI Large (MRL: 3072/1536/768)

    # --- LLM Provider Selection ---
    LLM_PROVIDER: str = "azure_openai"  # "azure_openai" | "ollama" | "vllm"
    LLM_MODEL: str = "gpt-4o"
    LOCAL_LLM_MODEL: str = "gemma4:e4b"
    LOCAL_LLM_MAX_CTX: int = 32768

    # --- Local Model Servers (Security: Restricted to localhost by default) ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    VLLM_BASE_URL: str = "http://localhost:8000"

    # --- Azure AI Search ---
    AZURE_SEARCH_ENDPOINT: str = ""
    AZURE_SEARCH_API_KEY: str = ""
    AZURE_SEARCH_INDEX_PREFIX: str = "cliniq-dept"
    AZURE_SEARCH_ENABLED: bool = False

    # --- Azure ChromaDB (Chat History) ---
    AZURE_CHROMA_HOST: str = "localhost"
    AZURE_CHROMA_PORT: int = 8000
    AZURE_CHROMA_AUTH_TOKEN: str = ""
    CHAT_HISTORY_ENABLED: bool = False

    # --- JWT / Auth ---
    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    JWT_EXPIRY_MINUTES: int = Field(default=480, ge=5, le=1440)
    USERS_DB_PATH: str = "./data/users.db"
    VAULT_DB_PATH: str = "./data/vault.db"
    DEMO_ADMIN_USERNAME: str = "admin"
    DEMO_ADMIN_PASSWORD: str = ""
    ALLOW_DEMO_ADMIN: bool = False

    # --- Hospital departments (configurable per deployment) ---
    HOSPITAL_DEPARTMENTS: str = (
        "radiology,pharmacy,administration,nursing,laboratory,"
        "emergency,cardiology,oncology,orthopedics,pediatrics,general"
    )

    # --- HTTP / browser security ---
    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:8000,http://127.0.0.1:8000"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    SECURITY_HEADERS_ENABLED: bool = True

    # --- Upload safety ---
    MAX_UPLOAD_BYTES: int = Field(default=25 * 1024 * 1024, ge=1, le=100 * 1024 * 1024)
    UPLOAD_QUARANTINE_DIR: str = "./tmp/uploads"
    ALLOWED_UPLOAD_EXTENSIONS: str = "pdf,docx,xlsx,xls,png,jpg,jpeg,tiff,bmp,dcm,mp3,wav,m4a,flac,ogg,mp4,mov,avi,webm"

    # Observability. External tracing is disabled by default to avoid PHI egress.
    ENABLE_EXTERNAL_TRACING: bool = False
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "ClinIQ-Hospital-Beta"

    # --- RAG pipeline ---
    MAX_QUERY_RETRIES: int = 3

    @property
    def departments_list(self) -> List[str]:
        """Returns the hospital departments as a cleaned list."""
        return [d.strip().lower() for d in self.HOSPITAL_DEPARTMENTS.split(",") if d.strip()]

    @property
    def allowed_origins_list(self) -> List[str]:
        """Return normalized CORS origins."""
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_upload_extensions_list(self) -> List[str]:
        """Return normalized allowed extensions without leading dots."""
        return [
            ext.strip().lower().lstrip(".")
            for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",")
            if ext.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @model_validator(mode="after")
    def validate_security_defaults(self) -> "Settings":
        weak_secrets = {
            "",
            "change-me",
            "change-me-in-production",
            "change-me-in-production-use-openssl-rand",
            "change-me-in-production-use-openssl-rand-hex-32",
            "dev-secret-change-in-production",
            "secret",
            "changeme",
        }

        if self.is_production:
            lower_secret = self.JWT_SECRET_KEY.lower()
            if (
                self.JWT_SECRET_KEY in weak_secrets
                or len(self.JWT_SECRET_KEY) < 32
                or "replace" in lower_secret
                or "placeholder" in lower_secret
            ):
                raise ValueError(
                    "JWT_SECRET_KEY must be a strong, deployment-specific secret in production."
                )
            if "*" in self.allowed_origins_list:
                raise ValueError("CORS_ALLOWED_ORIGINS cannot contain '*' in production.")
            if self.ALLOW_DEMO_ADMIN:
                raise ValueError("ALLOW_DEMO_ADMIN must be false in production.")
            if self.ENABLE_EXTERNAL_TRACING and not self.LANGCHAIN_API_KEY:
                raise ValueError("LANGCHAIN_API_KEY is required when external tracing is enabled.")

        if self.CORS_ALLOW_CREDENTIALS and "*" in self.allowed_origins_list:
            raise ValueError("Wildcard CORS origins are not allowed when credentials are enabled.")

        if self.AZURE_SEARCH_ENABLED and (not self.AZURE_SEARCH_ENDPOINT or not self.AZURE_SEARCH_API_KEY):
            raise ValueError("Azure Search requires AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY.")

        if self.LLM_PROVIDER not in {"azure_openai", "ollama", "vllm"}:
            raise ValueError("LLM_PROVIDER must be one of: azure_openai, ollama, vllm.")

        if self.EMBEDDING_PROVIDER not in {"gemini", "openai"}:
            raise ValueError("EMBEDDING_PROVIDER must be one of: gemini, openai.")

        return self

    def apply_runtime_env(self) -> None:
        """Keep third-party tracing libraries from enabling PHI egress by default."""
        if not self.ENABLE_EXTERNAL_TRACING:
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            os.environ.pop("LANGCHAIN_API_KEY", None)
            return

        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = self.LANGCHAIN_ENDPOINT
        os.environ["LANGCHAIN_PROJECT"] = self.LANGCHAIN_PROJECT
        if self.LANGCHAIN_API_KEY:
            os.environ["LANGCHAIN_API_KEY"] = self.LANGCHAIN_API_KEY

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
settings.apply_runtime_env()
