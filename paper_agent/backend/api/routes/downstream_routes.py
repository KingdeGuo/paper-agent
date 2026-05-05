"""Downstream Research API — code gen, validation, formatting, writing support."""

import logging

from backend.services.downstream_service import downstream
from backend.services.registry import get_db
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/downstream/generate-code", summary="Generate code from paper")
async def generate_code(document_id: str = None, paper_text: str = "",
                        language: str = "python", task: str = "implement the main algorithm",
                        db=Depends(get_db)):
    """Generate implementation code from a paper's methodology."""
    :
        if document_id and not paper_text:
        doc = await db.get_document(document_id) if db else None
        :
            if doc:
            paper_text = f"Title: {doc.title}\nAbstract: {doc.abstract or ''}\nSummary: {doc.summary or ''}"
    :
        if not paper_text:
        return {"error": "No paper text provided"}
    return await downstream.generate_code(paper_text, language, task)


@router.post("/downstream/generate-code-from-formula", summary="Generate code from formula")
async def generate_code_from_formula(formula: str, language: str = "python"):
    return await downstream.generate_code_from_formula(formula, language)


@router.post("/downstream/validate-expression", summary="Validate mathematical expression")
async def validate_expression(expression: str, context: str = ""):
    return await downstream.validate_expression(expression, context)


@router.post("/downstream/check-data", summary="Check data accuracy")
async def check_data_accuracy(data_claims: str, context: str = ""):
    return await downstream.check_data_accuracy(data_claims, context)


@router.post("/downstream/design-experiment", summary="Design an experiment")
async def design_experiment(methodology: str, resources: str = "", constraints: str = ""):
    return await downstream.design_experiment(methodology, resources, constraints)


@router.post("/downstream/format-manuscript", summary="Format manuscript to journal template")
async def format_manuscript(content: str, template: str = "arxiv",
                             title: str = "", authors: str = ""):
    authors_list = [a.strip() for a in authors.split(",") if a.strip()] if authors else []
    return await downstream.format_manuscript(content, template, title, authors_list)


@router.post("/downstream/generate-figure", summary="Generate publication figure code")
async def generate_figure(data_description: str, chart_type: str = "matplotlib",
                           style: str = "publication"):
    return await downstream.generate_figure_code(data_description, chart_type, style)


@router.post("/downstream/review-response", summary="Generate review response")
async def generate_review_response(reviewer_comments: str, paper_summary: str = "",
                                    tone: str = "professional"):
    return await downstream.generate_review_response(reviewer_comments, paper_summary, tone)


@router.post("/downstream/patent-ideas", summary="Extract patent ideas from paper")
async def extract_patent_ideas(document_id: str = None, paper_text: str = "",
                                db=Depends(get_db)):
    :
        if document_id and not paper_text:
        doc = await db.get_document(document_id) if db else None
        :
            if doc:
            paper_text = f"Title: {doc.title}\nAbstract: {doc.abstract or ''}\nSummary: {doc.summary or ''}"
    return await downstream.extract_patent_ideas(paper_text)


@router.post("/downstream/grant-proposal", summary="Write a grant proposal")
async def write_grant_proposal(topic: str, funding_agency: str = "NSF",
                                pi_background: str = "", budget: str = ""):
    return await downstream.write_grant_proposal(topic, funding_agency, pi_background, budget)
