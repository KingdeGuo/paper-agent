"""
Service registry - central place for getting backend services.

This avoids circular imports between main.py and routes.
"""

import logging

logger = logging.getLogger(__name__)

# Global service instances (lazy-initialised)
_db_service = None
_pdf_processor = None
_vector_service = None
_llm_service = None
_cache = None
_obj_storage = None
_task_queue = None


def get_db():
    """Get database service instance."""
    global _db_service
    if _db_service is None:
        try:
            from paper_agent.backend.services.cluster_database import ClusterDatabaseService
        except ImportError:
            try:
                from backend.services.cluster_database import ClusterDatabaseService
            except ImportError:
                return None
        _db_service = ClusterDatabaseService()
    return _db_service


def get_pdf_processor():
    """Get PDF processor instance."""
    global _pdf_processor
    if _pdf_processor is None:
        try:
            from paper_agent.backend.services.pdf_processor import PDFProcessor
        except ImportError:
            try:
                from backend.services.pdf_processor import PDFProcessor
            except ImportError:
                return None
        _pdf_processor = PDFProcessor()
    return _pdf_processor


def get_vector_service():
    """Get vector service instance."""
    global _vector_service
    if _vector_service is None:
        try:
            from paper_agent.backend.services.vector_service import VectorService
        except ImportError:
            try:
                from backend.services.vector_service import VectorService
            except ImportError:
                return None
        _vector_service = VectorService()
    return _vector_service


def get_llm_service():
    """Get LLM service instance."""
    global _llm_service
    if _llm_service is None:
        try:
            from paper_agent.backend.services.llm_service import LLMService
        except ImportError:
            try:
                from backend.services.llm_service import LLMService
            except ImportError:
                return None
        _llm_service = LLMService()
    return _llm_service


def get_cache():
    """Get cache service instance."""
    global _cache
    if _cache is None:
        try:
            from paper_agent.backend.services.cache_service import cache
        except ImportError:
            try:
                from backend.services.cache_service import cache
            except ImportError:
                return None
        _cache = cache
    return _cache


def get_object_storage():
    """Get object storage service instance."""
    global _obj_storage
    if _obj_storage is None:
        try:
            from paper_agent.backend.services.object_storage import storage as obj_storage
        except ImportError:
            try:
                from backend.services.object_storage import storage as obj_storage
            except ImportError:
                return None
        _obj_storage = obj_storage
    return _obj_storage


def get_task_queue():
    """Get task queue service instance."""
    global _task_queue
    if _task_queue is None:
        try:
            from paper_agent.backend.services.task_queue import task_queue
        except ImportError:
            try:
                from backend.services.task_queue import task_queue
            except ImportError:
                return None
        _task_queue = task_queue
    return _task_queue
