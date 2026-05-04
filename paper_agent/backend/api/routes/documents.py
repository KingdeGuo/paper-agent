"""
Document routes: upload, list, update, delete, download + text chunks.
"""

import os
import sys
import logging
from typing import List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends

try:
    from paper_agent.backend.models.document import DocumentCreate, DocumentResponse, DocumentUpdate
    from paper_agent.backend.services.database import DatabaseService
except ImportError:
    try:
        from backend.models.document import DocumentCreate, DocumentResponse, DocumentUpdate
        from backend.services.database import DatabaseService
    except ImportError:
        DocumentCreate = DocumentResponse = DocumentUpdate = None
        DatabaseService = None

try:
    from paper_agent.backend.services.pdf_processor import PDFProcessor
    from paper_agent.backend.services.vector_service import VectorService
    from paper_agent.backend.services.llm_service import LLMService
except ImportError:
    try:
        from backend.services.pdf_processor import PDFProcessor
        from backend.services.vector_service import VectorService
        from backend.services.llm_service import LLMService
    except ImportError:
        PDFProcessor = VectorService = LLMService = None

# Use service registry to avoid circular imports
try:
    from paper_agent.backend.services.registry import get_db, get_pdf_processor, get_vector_service, get_llm_service
except ImportError:
    try:
        from backend.services.registry import get_db, get_pdf_processor, get_vector_service, get_llm_service
    except ImportError:
        get_db = get_pdf_processor = get_vector_service = get_llm_service = lambda: None

try:
    from backend.middleware.auth import get_optional_user, get_current_user_from_token
except ImportError:
    get_optional_user = get_current_user_from_token = lambda: None

logger = logging.getLogger(__name__)

router = APIRouter()


async def process_document_task(
    document_id: str,
    db_service: DatabaseService | None = None,
    pdf_processor: PDFProcessor | None = None,
    vector_service: VectorService | None = None,
    llm_service: LLMService | None = None,
):
    """Background task to process document: extract text, vectorize, generate summary."""
    db = db_service or get_db()
    pdf = pdf_processor or get_pdf_processor()
    vs = vector_service or get_vector_service()
    llm = llm_service or get_llm_service()

    try:
        await db.update_processing_status(document_id, 1)

        document = await db.get_document(document_id)
        if not document:
            logger.error(f"Document {document_id} not found")
            return

        text = pdf.extract_text(document.file_path)
        if not text:
            await db.update_processing_status(document_id, 3)
            logger.error(f"Failed to extract text from {document_id}")
            return

        chunks = pdf.chunk_text(text)
        if not chunks:
            await db.update_processing_status(document_id, 3)
            logger.error(f"Failed to chunk text for {document_id}")
            return

        metadata = {
            "title": document.title or document.filename,
            "authors": document.authors or [],
            "year": document.year,
            "filename": document.filename,
        }

        vs.add_document(document_id, chunks, metadata)

        summary = await llm.generate_summary(text, max_length=300, style="academic")
        await db.update_processing_status(document_id, 2, summary=summary)

        logger.info(f"Successfully processed document {document_id}")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        await db.update_processing_status(document_id, 3)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    authors: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    keywords: Optional[str] = Form(None),
    db_service: DatabaseService = Depends(get_db),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
):
    """Upload and process a new PDF document."""
    try:
        content = await file.read()
        document_data, text = pdf_processor.process_document(content, file.filename)

        if title:
            document_data.title = title
        if authors:
            document_data.authors = [a.strip() for a in authors.split(",")]
        if keywords:
            document_data.keywords = [k.strip() for k in keywords.split(",")]
        if year:
            document_data.year = year

        document = await db_service.create_document(document_data)
        background_tasks.add_task(process_document_task, document.id)

        return document

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    processed: Optional[int] = None,
    db_service: DatabaseService = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get all documents with optional filtering and user isolation."""
    try:
        user_id = current_user.id if current_user else None
        if hasattr(db_service, 'get_documents'):
            documents = await db_service.get_documents(skip=skip, limit=limit, user_id=user_id)
        else:
            documents = await db_service.get_all_documents(skip=skip, limit=limit)

        if processed is not None:
            documents = [doc for doc in documents if doc.processed == processed]

        return documents

    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db_service: DatabaseService = Depends(get_db),
):
    """Get document by ID."""
    try:
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    update_data: DocumentUpdate,
    db_service: DatabaseService = Depends(get_db),
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
        logger.error(f"Error updating document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db_service: DatabaseService = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service),
):
    """Delete document from database and vector store."""
    try:
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        vector_service.delete_document(document_id)
        success = await db_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"message": "Document deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    db_service: DatabaseService = Depends(get_db),
):
    """Download the original PDF file."""
    try:
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        import os as os_mod

        if not os_mod.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="File not found")

        from fastapi.responses import FileResponse

        return FileResponse(
            document.file_path,
            media_type="application/pdf",
            filename=document.filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/text")
async def get_document_text(
    document_id: str,
    db_service: DatabaseService = Depends(get_db),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
):
    """Get extracted text content from a document."""
    try:
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        text = pdf_processor.extract_text(document.file_path)
        return {"text": text}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document text {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    db_service: DatabaseService = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service),
):
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
        logger.error(f"Error getting document chunks {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))