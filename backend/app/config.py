import os
from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "IP-SAKTI Sahayak"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./ip_sakti.db"

    # LLM Settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    # Pluggable WatsonX
    WATSONX_APIKEY: str = ""
    WATSONX_PROJECT_ID: str = ""
    WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"

    # RAG & Hybrid Retrieval Settings
    CONFIDENCE_THRESHOLD: float = 0.55
    MAX_RETRIEVAL_CHUNKS: int = 4
    CHUNK_SIZE: int = 750
    CHUNK_OVERLAP: int = 150
    HYBRID_RETRIEVAL_ENABLED: bool = True
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    RRF_K: int = 60

    # Reranker Settings
    RERANKER_ENABLED: bool = True
    RERANKER_CANDIDATES: int = 10
    RERANKER_TOP_K: int = 4

    # Citation Verification
    CITATION_VERIFICATION_ENABLED: bool = True

    # Paths
    STORAGE_DIR: Path = BASE_DIR / "data" / "storage"
    SEED_CORPUS_DIR: Path = BASE_DIR / "data" / "seed_corpus"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]

settings = Settings()

# Ensure data directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.SEED_CORPUS_DIR.mkdir(parents=True, exist_ok=True)
