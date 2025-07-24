import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import func

from backend.config.settings import settings
from backend.api.routes import documents, search, summary
from backend.services.database import DatabaseService
from backend.services.pdf_processor import PDFProcessor
from backend.services.vector_service import VectorService
from backend.services.llm_service import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
db_service = DatabaseService()
pdf_processor = PDFProcessor()
vector_service = VectorService()
llm_service = LLMService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up...")
    
    # Create database tables
    db_service.create_tables()
    
    # Create data directories
    import os
    os.makedirs("./data/pdfs", exist_ok=True)
    os.makedirs("./data/vector_db", exist_ok=True)
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="智能文献管理系统",
    description="基于RAG技术的智能文献管理与检索系统",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(summary.router, prefix="/api/summary", tags=["summary"])

# Serve static files
app.mount("/static", StaticFiles(directory="data/pdfs"), name="static")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "智能文献管理系统 API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database
        stats = await db_service.get_processing_stats()
        
        # Check vector database
        vector_stats = vector_service.get_collection_stats()
        
        return {
            "status": "healthy",
            "database": {
                "total_documents": stats["total"],
                "pending": stats["pending"],
                "completed": stats["completed"]
            },
            "vector_db": {
                "total_chunks": vector_stats["total_chunks"],
                "model": vector_stats["model"]
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/api/stats")
async def get_system_stats():
    """Get system statistics."""
    try:
        db_stats = await db_service.get_processing_stats()
        vector_stats = vector_service.get_collection_stats()
        
        return {
            "documents": db_stats,
            "vector_db": vector_stats,
            "system": {
                "embedding_model": settings.embedding.model,
                "llm_provider": settings.llm.provider,
                "llm_model": settings.llm.model
            }
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.debug
    )
