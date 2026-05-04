"""
Cluster configuration for Paper Agent.

Supports PostgreSQL, Redis, S3-compatible storage, and distributed task queues.
"""

from typing import Optional, Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration with PostgreSQL support."""
    
    # Database type: sqlite, postgresql
    type: Literal["sqlite", "postgresql"] = "sqlite"
    
    # PostgreSQL settings
    host: str = "localhost"
    port: int = 5432
    name: str = "paper_agent"
    user: str = "paper_agent"
    password: str = ""
    
    # SQLite settings
    sqlite_path: str = "./data/documents.db"
    
    # Connection pool
    pool_size: int = 20
    max_overflow: int = 10
    pool_recycle: int = 3600
    
    @property
    def async_url(self) -> str:
        if self.type == "postgresql":
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return f"sqlite+aiosqlite:///{self.sqlite_path}"
    
    @property
    def sync_url(self) -> str:
        if self.type == "postgresql":
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return f"sqlite:///{self.sqlite_path}"


class RedisSettings(BaseSettings):
    """Redis configuration for caching and task queue."""
    
    enabled: bool = False
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    url: Optional[str] = None
    
    # Cache settings
    cache_ttl: int = 3600  # 1 hour
    cache_prefix: str = "paper_agent:"
    
    # Task queue settings
    queue_name: str = "paper_agent_tasks"
    result_ttl: int = 86400  # 24 hours
    
    @property
    def redis_url(self) -> str:
        if self.url:
            return self.url
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class ObjectStorageSettings(BaseSettings):
    """S3-compatible object storage for PDFs and files."""
    
    enabled: bool = False
    provider: Literal["minio", "s3", "oss"] = "minio"  # minio, s3, aliyun oss
    
    # Endpoint
    endpoint: str = "http://localhost:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    
    # Bucket settings
    bucket_name: str = "paper-agent"
    region: str = "us-east-1"
    
    # Paths
    pdf_prefix: str = "pdfs/"
    vector_prefix: str = "vectors/"
    export_prefix: str = "exports/"
    
    # Public URL (for serving files)
    public_url: Optional[str] = None
    
    @property
    def is_s3(self) -> bool:
        return self.provider == "s3"
    
    @property
    def is_minio(self) -> bool:
        return self.provider == "minio"


class TaskQueueSettings(BaseSettings):
    """Distributed task queue configuration."""
    
    # Queue type: none, redis, rabbitmq
    type: Literal["none", "redis", "rabbitmq"] = "none"
    
    # Worker settings
    max_workers: int = 4
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    
    # Task types
    task_document_process: str = "document_process"
    task_summary_generate: str = "summary_generate"
    task_embedding_compute: str = "embedding_compute"
    
    # RabbitMQ (optional)
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"


class VectorDBClusterSettings(BaseSettings):
    """Vector database cluster configuration."""
    
    # ChromaDB can run in client-server mode
    mode: Literal["persistent", "client_server", "distributed"] = "persistent"
    
    # Client-server mode
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_url: Optional[str] = None
    
    # Distributed mode (future)
    replication_factor: int = 2
    shard_count: int = 4
    
    @property
    def server_url(self) -> str:
        if self.chroma_url:
            return self.chroma_url
        return f"http://{self.chroma_host}:{self.chroma_port}"


class ClusterSettings(BaseSettings):
    """Main cluster configuration."""
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    storage: ObjectStorageSettings = Field(default_factory=ObjectStorageSettings)
    task_queue: TaskQueueSettings = Field(default_factory=TaskQueueSettings)
    vector_db: VectorDBClusterSettings = Field(default_factory=VectorDBClusterSettings)
    
    # Node settings
    node_id: str = "node-1"
    node_role: Literal["api", "worker", "all"] = "all"
    
    # Feature flags
    enable_clustering: bool = False
    enable_load_balancer: bool = False
    
    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "env_prefix": "CLUSTER__",
    }
