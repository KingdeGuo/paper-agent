import os
from pathlib import Path
from typing import Any, Dict, List

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    provider: str = "huggingface"
    model: str = "meta-llama/Llama-3-8b"
    api_key: str = ""
    qwen_api_key: str = ""
    qwen_model: str = "qwen-plus"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    ollama_model: str = "llama3"
    ollama_base_url: str = "http://localhost:11434/v1"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-haiku-20240307"
    temperature: float = 0.7
    max_tokens: int = 512

class EmbeddingSettings(BaseSettings):
    model: str = "all-MiniLM-L6-v2"
    dimension: int = 384

class VectorDBSettings(BaseSettings):
    provider: str = "chromadb"
    path: str = "./data/vector_db"

class PDFProcessingSettings(BaseSettings):
    max_pages: int = 100
    extract_images: bool = False
    chunk_size: int = 1000
    chunk_overlap: int = 200

class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

class StorageSettings(BaseSettings):
    pdf_path: str = "./data/pdfs"
    max_file_size: str = "50MB"
    allowed_extensions: List[str] = [".pdf"]

class Settings(BaseSettings):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    vector_db: VectorDBSettings = Field(default_factory=VectorDBSettings)
    pdf_processing: PDFProcessingSettings = Field(default_factory=PDFProcessingSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)

    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "__",
    }


# ---------------------------------------------------------------------------
# Import cluster settings (lazy to avoid circular imports)
# ---------------------------------------------------------------------------

try:
    from backend.config.cluster_settings import ClusterSettings as _ClusterSettings
    cluster_settings = _ClusterSettings()
except ImportError:
    # Fallback if cluster settings not available
    class _ClusterSettings:
        enable_clustering = False
        node_id = "local-1"
        node_role = "all"
    cluster_settings = _ClusterSettings()

def load_config(config_path: str | None = None) -> Settings:
    """Load configuration from YAML file and environment variables."""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

    settings = Settings()

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data: Dict[str, Any] = yaml.safe_load(f) or {}

        # Walk nested sections since settings is a nested object
        for section, values in config_data.items():
            if hasattr(settings, section):
                section_obj = getattr(settings, section)
                if isinstance(section_obj, BaseSettings):
                    section_obj = type(section_obj)(**values)
                    setattr(settings, section, section_obj)
                else:
                    for key, value in values.items():
                        if hasattr(section_obj, key):
                            setattr(section_obj, key, value)

    return settings


# Global settings instance
settings = load_config()
