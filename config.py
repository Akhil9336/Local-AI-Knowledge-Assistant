"""Application configuration loaded from environment variables."""
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    generation_model: str = os.getenv("OLLAMA_GENERATION_MODEL", "llama3.2")
    embedding_model: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3")
    data_dir: Path = Path(os.getenv("RAG_DATA_DIR", "data"))
    chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "150"))
    top_k: int = int(os.getenv("RAG_TOP_K", "5"))
    similarity_threshold: float | None = (
        float(os.environ["RAG_SIMILARITY_THRESHOLD"])
        if os.getenv("RAG_SIMILARITY_THRESHOLD") else None
    )
    max_file_mb: int = int(os.getenv("RAG_MAX_FILE_MB", "50"))
    request_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "120"))

    @property
    def db_dir(self) -> Path:
        return self.data_dir / "chroma_db"


settings = Settings()
