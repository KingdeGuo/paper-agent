"""Paper-to-Presentation — auto-generate slide summaries from papers."""

import json
import logging

from backend.services.registry import get_db, get_llm_service
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/presentation/{document_id}", summary="Generate paper presentation")
async def generate_presentation(document_id: str, style: str = "academic",
                                 slides: int = 5, db=Depends(get_db),
                                 llm_service=Depends(get_llm_service)):
    """Auto-generate slide content for a paper."""
    doc = await db.get_document(document_id)
    :
        if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    text = f"Title: {doc.title}\nAuthors: {', '.join(doc.authors or [])}\nYear: {doc.year}\nAbstract: {(doc.abstract or '')[:1500]}\nSummary: {(doc.summary or '')[:1000]}"

    slide_templates = {
        "academic": ["Title Slide", "Background & Motivation", "Methodology", "Key Results", "Discussion & Conclusions"],
        "seminar": ["Motivation", "Problem Statement", "Approach", "Experiments", "Takeaways", "Q&A"],
        "quick": ["What & Why", "How", "Results", "Takeaway"],
    }

    slide_titles = slide_templates.get(style, slide_templates["academic"])[:slides]

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Create a {slides}-slide presentation outline for this paper. Style: {style}. Slide titles: {', '.join(slide_titles)}.\n\nPaper:\n{text}\n\nOutput as JSON: {{\"slides\": [{{\"title\": \"...\", \"bullets\": [\"...\"], \"notes\": \"...\"}}], \"style\": \"{style}\"}}" }],
            system_prompt="You create concise, presentation-ready content. Each slide should have 3-5 bullet points. Output valid JSON only.",
        )
        content = resp.get("content", "{}") if isinstance(resp, dict) else str(resp)
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        result = json.loads(match.group()) if match else {}
    except Exception as e:
        result = {"error": str(e)}

    return {
        "document_id": document_id,
        "title": doc.title or doc.filename,
        "style": style,
        "slide_count": slides,
        "presentation": result,
        "slide_titles": slide_titles,
    }


@router.post("/presentation/batch", summary="Generate presentations for multiple papers")
async def batch_generate(document_ids: list[str], style: str = "quick",
                          slides: int = 3, db=Depends(get_db),
                          llm_service=Depends(get_llm_service)):
    """Generate quick presentations for multiple papers."""
    results = []
    for did in document_ids[:5]:
        try:
            result = await generate_presentation(did, style=style, slides=slides, db=db, llm_service=llm_service)
            results.append(result)
        except Exception as e:
            results.append({"document_id": did, "error": str(e)})

    return {
        "style": style,
        "slides_per_paper": slides,
        "papers": len(results),
        "presentations": results,
    }
