"""
Distributed task queue for cluster deployment.

Supports Redis and RabbitMQ backends for document processing tasks.
"""

import logging
import json
import uuid
from typing import Optional, Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------

class Task:
    """Represents a task in the queue."""
    
    def __init__(
        self,
        task_type: str,
        payload: Dict[str, Any],
        task_id: Optional[str] = None,
        retry_count: int = 0,
    ):
        self.id = task_id or str(uuid.uuid4())
        self.type = task_type
        self.payload = payload
        self.retry_count = retry_count
        self.created_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "payload": self.payload,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            task_type=data["type"],
            payload=data["payload"],
            task_id=data["id"],
            retry_count=data.get("retry_count", 0),
        )


# ---------------------------------------------------------------------------
# Task Queue Base
# ---------------------------------------------------------------------------

class TaskQueueBase:
    """Base class for task queues."""
    
    def __init__(self):
        self.enabled = False
        self.queue_name = "paper_agent_tasks"
    
    async def init(self):
        pass
    
    async def close(self):
        pass
    
    async def enqueue(self, task: Task) -> bool:
        raise NotImplementedError
    
    async def dequeue(self) -> Optional[Task]:
        raise NotImplementedError
    
    async def ack(self, task_id: str) -> bool:
        raise NotImplementedError
    
    async def get_stats(self) -> Dict[str, Any]:
        return {"enabled": self.enabled, "queue": self.queue_name}


# ---------------------------------------------------------------------------
# Redis Task Queue
# ---------------------------------------------------------------------------

class RedisTaskQueue(TaskQueueBase):
    """Redis-based task queue using lists."""
    
    def __init__(self):
        super().__init__()
        self._redis = None
    
    async def init(self):
        from backend.config.cluster_settings import cluster_settings
        if not cluster_settings.task_queue.type == "redis":
            return
        
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                cluster_settings.redis.redis_url,
                db=cluster_settings.redis.db,
            )
            await self._redis.ping()
            self.enabled = True
            self.queue_name = cluster_settings.task_queue.queue_name
            logger.info(f"Redis task queue connected: {self.queue_name}")
        except Exception as e:
            logger.warning(f"Redis task queue failed: {e}")
    
    async def close(self):
        if self._redis:
            await self._redis.close()
    
    async def enqueue(self, task: Task) -> bool:
        if not self.enabled:
            return False
        try:
            data = json.dumps(task.to_dict())
            await self._redis.lpush(self.queue_name, data)
            return True
        except Exception as e:
            logger.error(f"Enqueue failed: {e}")
            return False
    
    async def dequeue(self) -> Optional[Task]:
        if not self.enabled:
            return None
        try:
            # Blocking pop with 5 second timeout
            result = await self._redis.brpop(self.queue_name, timeout=5)
            if result:
                _, data = result
                task_dict = json.loads(data)
                return Task.from_dict(task_dict)
        except Exception as e:
            logger.error(f"Dequeue failed: {e}")
        return None
    
    async def get_stats(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"enabled": False}
        try:
            length = await self._redis.llen(self.queue_name)
            return {
                "enabled": True,
                "backend": "redis",
                "queue_length": length,
                "queue_name": self.queue_name,
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}


# ---------------------------------------------------------------------------
# Task Queue Service (factory)
# ---------------------------------------------------------------------------

class TaskQueueService:
    """Task queue service with automatic backend selection."""
    
    def __init__(self):
        self._queue: Optional[TaskQueueBase] = None
    
    async def init(self):
        from backend.config.cluster_settings import cluster_settings
        
        if cluster_settings.task_queue.type == "redis":
            self._queue = RedisTaskQueue()
        else:
            logger.info("No task queue configured (type: none)")
            return
        
        await self._queue.init()
    
    async def close(self):
        if self._queue:
            await self._queue.close()
    
    @property
    def enabled(self) -> bool:
        return self._queue is not None and self._queue.enabled
    
    async def enqueue_document_process(self, document_id: str, file_path: str) -> bool:
        """Enqueue a document processing task."""
        if not self.enabled:
            return False
        
        task = Task(
            task_type="document_process",
            payload={
                "document_id": document_id,
                "file_path": file_path,
            }
        )
        return await self._queue.enqueue(task)
    
    async def enqueue_summary_generate(
        self, document_id: str, style: str = "academic"
    ) -> bool:
        """Enqueue a summary generation task."""
        if not self.enabled:
            return False
        
        task = Task(
            task_type="summary_generate",
            payload={
                "document_id": document_id,
                "style": style,
            }
        )
        return await self._queue.enqueue(task)
    
    async def dequeue(self) -> Optional[Task]:
        if not self.enabled:
            return None
        return await self._queue.dequeue()
    
    async def get_stats(self) -> Dict[str, Any]:
        if not self._queue:
            return {"enabled": False}
        return await self._queue.get_stats()


# Global task queue instance
task_queue = TaskQueueService()
