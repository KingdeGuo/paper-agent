"""Citation management API routes."""

import logging
from typing import List, Optional

from backend.services.citation_service import (
    CITATION_STYLES,
    doc_to_bibtex,
    generate_bibliography,
    generate_citation_key,
    lookup_doi,
    parse_bibtex,
    search_crossref,
)
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.registry import get_db
from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/styles", summary="List available citation styles")
async def get_citation_styles():
    """Return all supported citation styles."""
    return {
        "styles": [
            {"id": sid, "name": info["name"]}
            for sid, info in CITATION_STYLES.items()
        ],
        "default": "apa",
    }


@router.get("/export/{document_id}", summary="Export document as BibTeX")
async def export_bibtex(
    document_id: str,
    style: Optional[str] = Query(None),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Export a document as BibTeX with optional formatted citation."""
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    meta = doc.doc_metadata or {}
    bibtex = doc_to_bibtex(
        doc_id=doc.id,
        title=doc.title,
        authors=doc.authors,
        year=doc.year,
        journal=meta.get("journal"),
        volume=meta.get("volume"),
        number=meta.get("number"),
        pages=meta.get("pages"),
        doi=meta.get("doi"),
        url=getattr(doc, "arxiv_url", None),
        abstract=doc.abstract,
    )

    result = {
        "document_id": document_id,
        "bibtex": bibtex,
        "citation_key": generate_citation_key(doc.authors, doc.year, doc.title),
    }

    if style and style in CITATION_STYLES:
        formatted = generate_bibliography([
            {
                "authors": doc.authors or ["Unknown"],
                "year": doc.year,
                "title": doc.title or "Untitled",
                "journal": meta.get("journal", ""),
                "volume": meta.get("volume", ""),
                "issue": meta.get("number", ""),
                "pages": meta.get("pages", ""),
                "doi": meta.get("doi", ""),
            }
        ], style=style)
        result["formatted"] = formatted

    return result


@router.post("/export-batch", summary="Export multiple documents as BibTeX")
async def export_bibtex_batch(
    document_ids: List[str],
    style: Optional[str] = None,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Export multiple documents as a combined BibTeX file."""
    entries = []
    ref_data = []

    for doc_id in document_ids:
        doc = await db.get_document(doc_id)
        if not doc:
            continue
        meta = doc.doc_metadata or {}
        bibtex = doc_to_bibtex(
            doc_id=doc.id, title=doc.title, authors=doc.authors,
            year=doc.year, journal=meta.get("journal"),
            volume=meta.get("volume"), number=meta.get("number"),
            pages=meta.get("pages"), doi=meta.get("doi"),
            abstract=doc.abstract,
        )
        entries.append(bibtex)
        ref_data.append({
            "authors": doc.authors or ["Unknown"],
            "year": doc.year, "title": doc.title or "Untitled",
            "journal": meta.get("journal", ""),
            "volume": meta.get("volume", ""),
            "issue": meta.get("number", ""),
            "pages": meta.get("pages", ""),
            "doi": meta.get("doi", ""),
        })

    result = {
        "count": len(entries),
        "bibtex": "\n\n".join(entries),
    }

    if style and style in CITATION_STYLES:
        result["formatted"] = generate_bibliography(ref_data, style=style)

    return result


@router.post("/import-bibtex", summary="Import BibTeX entries")
async def import_bibtex(
    bibtex_content: str,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Parse and import BibTeX entries as documents."""
    entries = parse_bibtex(bibtex_content)
    imported = []

    for entry in entries:
        fields = entry["fields"]
        authors_str = fields.get("author", "")
        authors = [a.strip() for a in authors_str.replace(" and ", "|").split("|") if a.strip()]

        try:
            doc = await db.create_document({
                "filename": f"{entry['key']}.pdf",
                "title": fields.get("title", "Imported from BibTeX"),
                "authors": authors,
                "year": int(fields.get("year", 0)) if fields.get("year") else None,
                "abstract": fields.get("abstract"),
                "keywords": [k.strip() for k in fields.get("keywords", "").split(",") if k.strip()],
                "file_path": "",
                "file_size": 0,
                "processed": 2,
                "doc_metadata": {
                    "journal": fields.get("journal"),
                    "volume": fields.get("volume"),
                    "number": fields.get("number"),
                    "pages": fields.get("pages"),
                    "doi": fields.get("doi"),
                    "bibtex_key": entry["key"],
                    "entry_type": entry["type"],
                },
            })
            imported.append({"key": entry["key"], "document_id": doc.id, "title": doc.title})
        except Exception as e:
            logger.warning(f"Failed to import {entry['key']}: {e}")
            imported.append({"key": entry["key"], "error": str(e)})

    return {"imported": len(imported), "total": len(entries), "entries": imported}


@router.get("/lookup-doi", summary="Lookup DOI metadata")
async def doi_lookup(doi: str = Query(...)):
    """Look up publication metadata via DOI."""
    result = await lookup_doi(doi)
    if not result:
        raise HTTPException(status_code=404, detail="DOI not found")
    return result


@router.get("/search", summary="Search for publications")
async def search_publications(
    query: str = Query(...),
    limit: int = Query(default=10, le=50),
):
    """Search for publications using CrossRef."""
    results = await search_crossref(query, limit=limit)
    return {"query": query, "count": len(results), "results": results}


@router.post("/bibliography", summary="Generate formatted bibliography")
async def create_bibliography(
    document_ids: List[str],
    style: str = Query(default="apa"),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Generate a formatted bibliography from selected documents."""
    entries = []
    for doc_id in document_ids:
        doc = await db.get_document(doc_id)
        if not doc:
            continue
        meta = doc.doc_metadata or {}
        entries.append({
            "authors": doc.authors or ["Unknown"],
            "year": doc.year,
            "title": doc.title or "Untitled",
            "journal": meta.get("journal", ""),
            "volume": meta.get("volume", ""),
            "issue": meta.get("number", ""),
            "pages": meta.get("pages", ""),
            "doi": meta.get("doi", ""),
        })

    bibliography = generate_bibliography(entries, style=style)
    return {
        "style": style,
        "count": len(entries),
        "bibliography": bibliography,
    }
