import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import json
import asyncio

from backend.models.document import SummaryRequest, SummaryResponse
from backend.services.database import DatabaseService
from backend.services.pdf_processor import PDFProcessor
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
db_service = DatabaseService()
pdf_processor = PDFProcessor()

def get_llm_service(provider: str = None) -> LLMService:
    """Get LLM service with specified provider or default from settings."""
    from backend.config.settings import settings
    
    if provider:
        # Temporarily override provider
        original_provider = settings.llm.provider
        settings.llm.provider = provider
        try:
            service = LLMService()
            return service
        finally:
            # Restore original provider
            settings.llm.provider = original_provider
    else:
        return LLMService()

async def generate_summary_task(document_id: str, max_length: int, style: str, provider: str = None):
    """Background task to generate summary."""
    try:
        llm_service = get_llm_service(provider)
        
        # Get document
        document = await db_service.get_document(document_id)
        if not document:
            logger.error(f"Document {document_id} not found")
            return
        
        # Extract text
        text = pdf_processor.extract_text(document.file_path)
        if not text:
            logger.error(f"Failed to extract text from {document_id}")
            return
        
        # Generate summary
        summary = await llm_service.generate_summary(text, max_length, style)
        
        # Update document with summary
        await db_service.update_document(
            document_id,
            {"summary": summary}
        )
        
        logger.info(f"Successfully generated summary for document {document_id}")
        
    except Exception as e:
        logger.error(f"Error generating summary for document {document_id}: {str(e)}")

@router.post("/generate", response_model=SummaryResponse)
async def generate_summary(
    request: SummaryRequest,
    background_tasks: BackgroundTasks
):
    """Generate summary for document."""
    try:
        # Get LLM service with specified provider
        provider = getattr(request, 'model', None)
        llm_service = get_llm_service(provider)
        
        # Get document
        document = await db_service.get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Extract text if not already done
        text = getattr(document, 'text', None)
        if not text:
            text = pdf_processor.extract_text(document.file_path)
            if text:
                # Update document with extracted text
                await db_service.update_document(request.document_id, {"text": text})
        
        if not text:
            raise HTTPException(status_code=400, detail="Failed to extract text from document")
        
        # For immediate response, return existing summary or generate new one
        existing_summary = getattr(document, 'summary', None)
        if existing_summary:
            return SummaryResponse(
                document_id=request.document_id,
                summary=existing_summary,
                style=request.style
            )
        
        # Generate summary in background and return a placeholder
        background_tasks.add_task(
            generate_summary_task, 
            request.document_id, 
            request.max_length, 
            request.style,
            provider
        )
        
        return SummaryResponse(
            document_id=request.document_id,
            summary="Summary generation started. Please check back later.",
            style=request.style
        )
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-streaming")
async def generate_streaming_summary(request: dict):
    """Generate streaming summary for document with thinking process."""
    try:
        # Get LLM service with specified provider
        provider = request.get('model')
        llm_service = get_llm_service(provider)
        
        document_id = request.get("document_id")
        max_length = request.get("max_length", 300)
        style = request.get("style", "academic")
        
        # Get document
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Extract text if not already done
        text = getattr(document, 'text', None)
        if not text:
            text = pdf_processor.extract_text(document.file_path)
        
        if not text:
            raise HTTPException(status_code=400, detail="Failed to extract text from document")
        
        # Create prompt with thinking process
        prompt = f"""Think step by step and show your thinking process. Then provide a {style} summary of the following document:

Document:
{text[:3000]}...

Summary (max {max_length} characters):"""
        
        # Return streaming response
        return StreamingResponse(
            stream_summary_response(prompt, max_length, llm_service),
            media_type="text/plain"
        )
        
    except Exception as e:
        logger.error(f"Error generating streaming summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def stream_summary_response(prompt: str, max_length: int, llm_service: LLMService):
    """Stream the summary response."""
    try:
        async for chunk in llm_service.generate_streaming_response(prompt, max_length):
            yield chunk
    except Exception as e:
        yield f"Error: {str(e)}"

@router.post("/question-streaming")
async def answer_question_streaming(request: dict):
    """Answer question with streaming response and thinking process."""
    try:
        # Get LLM service with specified provider
        provider = request.get('model')
        llm_service = get_llm_service(provider)
        
        document_id = request.get("document_id")
        question = request.get("question")
        
        if not document_id or not question:
            raise HTTPException(status_code=400, detail="document_id and question are required")
        
        # Get document
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Extract text if not already done
        text = getattr(document, 'text', None)
        if not text:
            text = pdf_processor.extract_text(document.file_path)
        
        if not text:
            raise HTTPException(status_code=400, detail="Failed to extract text from document")
        
        # Create prompt with thinking process
        prompt = f"""First, think step by step and show your analysis process. Then answer the following question based on the document:

Document:
{text[:2000]}...

Question: {question}

Answer:"""
        
        # Return streaming response
        return StreamingResponse(
            stream_summary_response(prompt, 500, llm_service),
            media_type="text/plain"
        )
        
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}", response_model=SummaryResponse)
async def get_summary(document_id: str):
    """Get existing summary for a document."""
    try:
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.summary:
            raise HTTPException(status_code=404, detail="Summary not found")
        
        return SummaryResponse(
            document_id=document_id,
            summary=document.summary,
            length=len(document.summary),
            style=getattr(document, 'summary_style', 'academic')
        )
    except Exception as e:
        logger.error(f"Error getting summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/regenerate", response_model=SummaryResponse)
async def regenerate_summary(
    request: SummaryRequest,
    background_tasks: BackgroundTasks
):
    """Regenerate summary for document."""
    try:
        # Get LLM service with specified provider
        provider = getattr(request, 'model', None)
        llm_service = get_llm_service(provider)
        
        # Get document
        document = await db_service.get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Extract text if not already done
        text = getattr(document, 'text', None)
        if not text:
            text = pdf_processor.extract_text(document.file_path)
            if text:
                # Update document with extracted text
                await db_service.update_document(request.document_id, {"text": text})
        
        if not text:
            raise HTTPException(status_code=400, detail="Failed to extract text from document")
        
        # Generate summary in background
        background_tasks.add_task(
            generate_summary_task, 
            request.document_id, 
            request.max_length, 
            request.style,
            provider
        )
        
        return SummaryResponse(
            document_id=request.document_id,
            summary="Summary regeneration started. Please check back later.",
            style=request.style
        )
        
    except Exception as e:
        logger.error(f"Error regenerating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))