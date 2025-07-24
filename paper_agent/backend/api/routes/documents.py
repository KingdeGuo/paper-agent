import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy import func

from backend.models.document import DocumentCreate, DocumentResponse, DocumentUpdate
from backend.services.database import DatabaseService
from backend.services.pdf_processor import PDFProcessor
from backend.services.vector_service import VectorService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
db_service = DatabaseService()
pdf_processor = PDFProcessor()
vector_service = VectorService()
llm_service = LLMService()

async def process_document_task(document_id: str):
    """Background task to process document."""
    try:
        # Update status to processing
        await db_service.update_processing_status(document_id, 1)
        
        # Get document
        document = await db_service.get_document(document_id)
        if not document:
            logger.error(f"Document {document_id} not found")
            return
        
        # Extract text and process
        text = pdf_processor.extract_text(document.file_path)
        if not text:
            await db_service.update_processing_status(document_id, 3)
            logger.error(f"Failed to extract text from {document_id}")
            return
        
        # Chunk text
        chunks = pdf_processor.chunk_text(text)
        if not chunks:
            await db_service.update_processing_status(document_id, 3)
            logger.error(f"Failed to chunk text for {document_id}")
            return
        
        # Add to vector database
        metadata = {
            "title": document.title or document.filename,
            "authors": document.authors or [],
            "year": document.year,
            "filename": document.filename
        }
        
        vector_service.add_document(document_id, chunks, metadata)
        
        # Generate summary
        summary = await llm_service.generate_summary(text, max_length=300, style="academic")
        
        # Update document with summary and mark as completed
        await db_service.update_processing_status(document_id, 2, summary=summary)
        
        logger.info(f"Successfully processed document {document_id}")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        await db_service.update_processing_status(document_id, 3)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    authors: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    keywords: Optional[str] = Form(None)
):
    """Upload and process a new document."""
    try:
        # Read file content
        content = await file.read()
        
        # Process document
        document_data, text = pdf_processor.process_document(content, file.filename)
        
        # Override with provided metadata
        if title:
            document_data.title = title
        if authors:
            document_data.authors = [a.strip() for a in authors.split(',')]
        if keywords:
            document_data.keywords = [k.strip() for k in keywords.split(',')]
        if year:
            document_data.year = year
        
        # Create document record
        document = await db_service.create_document(document_data)
        
        # Start background processing
        background_tasks.add_task(process_document_task, document.id)
        
        return document
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    processed: Optional[int] = None
):
    """Get all documents with optional filtering."""
    try:
        documents = await db_service.get_all_documents(skip=skip, limit=limit)
        
        if processed is not None:
            documents = [doc for doc in documents if doc.processed == processed]
        
        return documents
        
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get document by ID."""
    try:
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    update_data: DocumentUpdate
):
    """Update document metadata."""
    try:
        document = await db_service.update_document(document_id, update_data)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete document."""
    try:
        # Get document to delete from vector db
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from vector database
        vector_service.delete_document(document_id)
        
        # Delete from database
        success = await db_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}/download")
async def download_document(document_id: str):
    """Download document file."""
    try:
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        import os
        if not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            document.file_path,
            media_type='application/pdf',
            filename=document.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}/text")
async def get_document_text(document_id: str):
    """Get document text content."""
    try:
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        text = pdf_processor.extract_text(document.file_path)
        return {"text": text}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document text {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}/chunks")
async def get_document_chunks(document_id: str):
    """Get document chunks from vector database."""
    try:
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        chunks = vector_service.get_document_chunks(document_id)
        return {"chunks": chunks}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document chunks {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
