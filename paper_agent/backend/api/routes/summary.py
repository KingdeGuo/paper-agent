"""
Summary & Q&A routes: generate, stream, and fetch summaries and answers.
"""

import logging
import os
import sys
from typing import Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse

try:
    from paper_agent.backend.models.document import SummaryRequest, SummaryResponse
    from paper_agent.backend.services.database import DatabaseService
except ImportError:
    try:
        from backend.models.document import SummaryRequest, SummaryResponse
        from backend.services.database import DatabaseService
    except ImportError:
        SummaryRequest = SummaryResponse = None
        DatabaseService = None

try:
    from paper_agent.backend.services.llm_service import LLMService
    from paper_agent.backend.services.pdf_processor import PDFProcessor
except ImportError:
    try:
        from backend.services.llm_service import LLMService
        from backend.services.pdf_processor import PDFProcessor
    except ImportError:
        PDFProcessor = LLMService = None

# Use service registry to avoid circular imports
try:
    from paper_agent.backend.services.registry import get_db, get_llm_service, get_pdf_processor
except ImportError:
    try:
        from backend.services.registry import get_db, get_llm_service, get_pdf_processor
    except ImportError:
        get_db = get_pdf_processor = get_llm_service = lambda: None

logger = logging.getLogger(__name__)

router = APIRouter()


async def generate_summary_task(
    document_id: str,
    max_length: int,
    style: str,
    db_service: Optional[DatabaseService] = None,
    pdf_processor: Optional[PDFProcessor] = None,
    llm_service: Optional[LLMService] = None,
):
    """Background task to generate a summary for a document."""
    db = db_service or DatabaseService()
    pdf = pdf_processor or PDFProcessor()
    llm = llm_service or LLMService()

    try:
        document = await db.get_document(document_id)
        if not document:
            logger.error(f"Document {document_id} not found")
            return

        text = pdf.extract_text(document.file_path)
        if not text:
            logger.error(f"Failed to extract text from {document_id}")
            return

        summary = await llm.generate_summary(text, max_length, style)

        from backend.models.document import DocumentUpdate
        await db.update_document(document_id, DocumentUpdate(summary=summary))

        logger.info(f"Successfully generated summary for document {document_id}")

    except Exception as e:
        logger.error(f"Error generating summary for document {document_id}: {e}")


@router.post("/generate", response_model=SummaryResponse)
async def generate_summary(
    request: SummaryRequest,
    background_tasks: BackgroundTasks,
    db_service: DatabaseService = Depends(get_db),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Generate a summary for a document. Returns immediately; processes in background."""
    try:
        document = await db_service.get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # If summary already exists, return it immediately
        if document.summary:
            return SummaryResponse(
                document_id=request.document_id,
                summary=document.summary,
                length=len(document.summary),
                style=request.style,
            )

        text = pdf_processor.extract_text(document.file_path)
        if not text:
            raise HTTPException(status_code=400, detail="Failed to extract text from document")

        # Generate summary in background
        background_tasks.add_task(
            generate_summary_task,
            request.document_id,
            request.max_length,
            request.style,
            db_service,
            pdf_processor,
            llm_service,
        )

        return SummaryResponse(
            document_id=request.document_id,
            summary="Summary generation started. Please check back later.",
            style=request.style,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-streaming")
async def generate_streaming_summary(
    request: SummaryRequest,
    db_service: DatabaseService = Depends(get_db),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Generate a streaming summary with thinking process."""
    try:
        document = await db_service.get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        text = pdf_processor.extract_text(document.file_path)
        if not text:
            raise HTTPException(status_code=400, detail="Failed to extract text from document")

        prompt = (
            f"Think step by step and show your thinking process. "
            f"Then provide a {request.style} summary of the following document:\n\n"
            f"Document:\n{text[:3000]}...\n\n"
            f"Summary (max {request.max_length} characters):"
        )

        async def stream():
            async for chunk in llm_service.generate_streaming_response(prompt, request.max_length):
                yield chunk

        return StreamingResponse(stream(), media_type="text/plain")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating streaming summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/question-streaming")
async def answer_question_streaming(
    document_id: str,
    question: str,
    db_service: DatabaseService = Depends(get_db),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Answer a question with streaming response and thinking process."""
    try:
        if not document_id or not question:
            raise HTTPException(status_code=400, detail="document_id and question are required")

        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        text = pdf_processor.extract_text(document.file_path)
        if not text:
            raise HTTPException(status_code=400, detail="Failed to extract text from document")

        # Use standardized QA prompt with reasoning
        from backend.services.llm_service import _build_qa_prompt
        prompt = _build_qa_prompt(question, text)

        async def stream():
            async for chunk in llm_service.generate_streaming_response(prompt, 500):
                yield chunk

        return StreamingResponse(stream(), media_type="text/plain")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=SummaryResponse)
async def get_summary(
    document_id: str,
    db_service: DatabaseService = Depends(get_db),
):
    """Get existing summary for a document."""
    try:
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if not document.summary:
            raise HTTPException(status_code=404, detail="Summary not found for this document")

        return SummaryResponse(
            document_id=document_id,
            summary=document.summary,
            length=len(document.summary),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate", response_model=SummaryResponse)
async def regenerate_summary(
    request: SummaryRequest,
    background_tasks: BackgroundTasks,
    db_service: DatabaseService = Depends(get_db),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Regenerate a summary for a document."""
    try:
        document = await db_service.get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        text = pdf_processor.extract_text(document.file_path)
        if not text:
            raise HTTPException(status_code=400, detail="Failed to extract text from document")

        background_tasks.add_task(
            generate_summary_task,
            request.document_id,
            request.max_length,
            request.style,
            db_service,
            pdf_processor,
            llm_service,
        )

        return SummaryResponse(
            document_id=request.document_id,
            summary="Summary regeneration started. Please check back later.",
            style=request.style,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
