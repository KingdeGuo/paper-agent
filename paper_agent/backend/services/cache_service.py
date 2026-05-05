"""
Redis-based caching service for cluster deployment.
"""

import logging
import os
import pickle
import sys
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Try to import redis
try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

logger = logging.getLogger(__name__)


class CacheService:
    """Distributed cache service using Redis."""

    def __init__(self):
        self.enabled = False
        self._redis = None
        self._prefix = "paper_agent:"

    async def init(self):
        """Initialize Redis connection."""
        try:
            from paper_agent.backend.config.cluster_settings import cluster_settings
        except ImportError:
            try:
                from backend.config.cluster_settings import cluster_settings
            except ImportError:
                # Fallback - Redis disabled
                class DummyClusterSettings:
                    class Redis:
                        enabled = False
                    redis = Redis()
                cluster_settings = DummyClusterSettings()

        if not cluster_settings.redis.enabled:
            logger.info("Redis cache disabled")
            return

        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                cluster_settings.redis.redis_url,
                db=cluster_settings.redis.db,
                decode_responses=False,  # We'll handle encoding
            )
            await self._redis.ping()
            self.enabled = True
            self._prefix = cluster_settings.redis.cache_prefix
            logger.info(f"Redis cache connected: {cluster_settings.redis.redis_url}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Running without cache.")
            self.enabled = False

    async def close(self):
        if self._redis:
            await self._redis.close()

    def _make_key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        try:
            data = await self._redis.get(self._make_key(key))
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self.enabled:
            return False
        try:
            from backend.config.cluster_settings import cluster_settings
            ttl = ttl or cluster_settings.redis.cache_ttl
            data = pickle.dumps(value)
            await self._redis.setex(self._make_key(key), ttl, data)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        if not self.enabled:
            return False
        try:
            await self._redis.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        if not self.enabled:
            return 0
        try:
            keys = await self._redis.keys(self._make_key(pattern))
            if keys:
                return await self._redis.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
        return 0

    # -----------------------------------------------------------------------
    # High-level cache helpers
    # -----------------------------------------------------------------------

    async def get_document(self, doc_id: str) -> Optional[Dict]:
        return await self.get(f"doc:{doc_id}")

    async def set_document(self, doc_id: str, doc: Dict, ttl: int = 3600):
        await self.set(f"doc:{doc_id}", doc, ttl)

    async def invalidate_document(self, doc_id: str):
        await self.delete(f"doc:{doc_id}")
        await self.delete_pattern("search:*")

    async def get_search_results(self, query_hash: str) -> Optional[List]:
        return await self.get(f"search:{query_hash}")

    async def set_search_results(self, query_hash: str, results: List, ttl: int = 300):
        await self.set(f"search:{query_hash}", results, ttl)

    async def get_stats(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"enabled": False}
        try:
            info = await self._redis.info()
            return {
                "enabled": True,
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "total_keys": await self._redis.dbsize(),
                "uptime_days": info.get("uptime_in_days", 0),
            }
        except Exception as e:
            return {"enabled": True, "connected": False, "error": str(e)}


# Global cache instance
cache = CacheService()
