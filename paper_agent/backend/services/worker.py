"""
Background worker for processing tasks from the task queue.

Runs as a separate process/container to handle:
- Document processing (PDF extraction, chunking, vectorization)
- Summary generation
- Embedding computation
"""

import asyncio
import logging
import signal
from typing import Optional

from fastapi import FastAPI
import uvicorn

from backend.config.settings import settings
from backend.config.cluster_settings import cluster_settings
from backend.services.cluster_database import ClusterDatabaseService, Document
from backend.services.task_queue import task_queue
from backend.services.pdf_processor import PDFProcessor
from backend.services.vector_service import VectorService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Health check app for worker
health_app = FastAPI()

@health_app.get("/health")
async def health_check():
    return {"status": "healthy", "node_id": cluster_settings.node_id}

class TaskWorker:
    """Worker that processes tasks from the queue."""
    
    def __init__(self):
        self.db = ClusterDatabaseService()
        self.pdf_processor = PDFProcessor()
        self.vector_service = VectorService()
        self.llm_service = LLMService()
        self.running = False
        self._stop_event = asyncio.Event()
    
    async def start(self):
        """Start the worker loop."""
        logger.info(f"Worker started on node {cluster_settings.node_id}")
        self.running = True
        
        # Start health server in background
        config = uvicorn.Config(health_app, host="0.0.0.0", port=8001, log_level="warning")
        server = uvicorn.Server(config)
        asyncio.create_task(server.serve())
        
        while self.running:
            try:
                task = await task_queue.dequeue()
                if task:
                    await self.process_task(task)
                else:
                    # No task, sleep briefly
                    await asyncio.sleep(1)
                
                if self._stop_event.is_set():
                    break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)
        
        await self.stop()
    
    async def stop(self):
        """Stop the worker."""
        self.running = False
        logger.info("Worker stopping and cleaning up...")
        # Add cleanup logic here if needed
        logger.info("Worker stopped")
    
    def handle_exit(self, sig, frame):
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        self._stop_event.set()
        self.running = False

async def main():
    """Entry point for the worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Initialize services
    await task_queue.init()
    
    if not task_queue.enabled:
        logger.error("Task queue not enabled. Worker cannot start.")
        return
    
    worker = TaskWorker()
    
    # Register signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(worker.stop()))
    
    try:
        await worker.start()
    except Exception as e:
        logger.error(f"Fatal worker error: {e}")
    finally:
        await task_queue.close()

if __name__ == "__main__":
    asyncio.run(main())
        """Process a single task."""
        logger.info(f"Processing task {task.id} of type {task.type}")
        
        try:
            if task.type == "document_process":
                await self._process_document(task.payload)
            elif task.type == "summary_generate":
                await self._generate_summary(task.payload)
            elif task.type == "embedding_compute":
                await self._compute_embeddings(task.payload)
            else:
                logger.warning(f"Unknown task type: {task.type}")
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            # Retry logic would go here
    
    async def _process_document(self, payload: dict):
        """Process a document: extract text, chunk, and vectorize."""
        document_id = payload.get("document_id")
        file_path = payload.get("file_path")
        
        if not document_id or not file_path:
            logger.error("Invalid document_process payload")
            return
        
        # Update status to processing
        await self.db.update_processing_status(document_id, status=1)
        
        try:
            # Cluster handling: Check if file exists locally, if not, download from object storage
            actual_path = file_path
            if not os.path.isabs(file_path) or not os.path.exists(file_path):
                from paper_agent.backend.services.object_storage import storage
                if storage.enabled:
                    # Assume file_path is the key (filename)
                    filename = os.path.basename(file_path)
                    temp_local_path = os.path.join(settings.storage.pdf_path, filename)
                    
                    logger.info(f"Downloading {filename} from object storage to {temp_local_path}")
                    success = await storage.download_file(filename, temp_local_path)
                    if success:
                        actual_path = temp_local_path
                    else:
                        raise FileNotFoundError(f"File {filename} not found in object storage")
            
            # Extract text from PDF
            text = await self.pdf_processor.extract_text(actual_path)
            if not text:
                await self.db.update_processing_status(document_id, status=3)
                return
            
            # Chunk the text
            chunks = self.pdf_processor.chunk_text(text)
            
            # Add to vector store
            vector_ids = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                await self.vector_service.add_chunk(
                    chunk_id=chunk_id,
                    text=chunk,
                    metadata={"document_id": document_id, "chunk_index": i}
                )
                vector_ids.append(chunk_id)
            
            # Update document with vector IDs
            await self.db.update_processing_status(
                document_id,
                status=2,
                vector_id=",".join(vector_ids[:10])  # Store first 10 IDs
            )
            
            logger.info(f"Document {document_id} processed: {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            await self.db.update_processing_status(document_id, status=3)
    
    async def _generate_summary(self, payload: dict):
        """Generate a summary for a document."""
        document_id = payload.get("document_id")
        style = payload.get("style", "academic")
        
        # Get document
        doc = await self.db.get_document(document_id)
        if not doc:
            logger.error(f"Document {document_id} not found")
            return
        
        try:
            # Cluster handling: Check if file exists locally, if not, download from object storage
            actual_path = doc.file_path
            if not os.path.isabs(actual_path) or not os.path.exists(actual_path):
                from paper_agent.backend.services.object_storage import storage
                if storage.enabled:
                    filename = os.path.basename(actual_path)
                    temp_local_path = os.path.join(settings.storage.pdf_path, filename)
                    
                    logger.info(f"Downloading {filename} from object storage for summary")
                    success = await storage.download_file(filename, temp_local_path)
                    if success:
                        actual_path = temp_local_path
                    else:
                        raise FileNotFoundError(f"File {filename} not found in object storage")

            # Get text or chunks
            text = await self.pdf_processor.extract_text(actual_path)
            
            # Generate summary using LLM
            summary = await self.llm_service.generate_summary(text, style=style)
            
            # Update document
            await self.db.update_processing_status(
                document_id,
                status=2,
                summary=summary
            )
            
            logger.info(f"Summary generated for document {document_id}")
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
    
    async def _compute_embeddings(self, payload: dict):
        """Compute embeddings for a document."""
        # Placeholder for future implementation
        logger.info("Embedding computation not yet implemented")


async def main():
    """Entry point for the worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Initialize services
    await task_queue.init()
    
    if not task_queue.enabled:
        logger.error("Task queue not enabled. Worker cannot start.")
        return
    
    worker = TaskWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
