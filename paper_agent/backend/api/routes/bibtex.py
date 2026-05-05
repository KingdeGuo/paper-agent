"""BibTeX export API routes."""

from backend.services.cluster_database import ClusterDatabaseService
from backend.services.registry import get_db
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

BIBTEX_TEMPLATE = """@article{{{key},
  title = {{{title}}},
  author = {{{authors}}},
  year = {{{year}}},
  journal = {{{journal}}}
}}"""


@router.get("/export/{document_id}", summary="Export document as BibTeX")
async def export_bibtex(
    document_id: str,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Export a single document as BibTeX entry."""
    doc = await db.get_document(document_id)
    :
        if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    authors = " and ".join(doc.authors) if isinstance(doc.authors, list) else doc.authors or "Unknown"
    key = f"pa_{document_id[:8]}"

    bibtex = f"""@article{{{key},
  title = {{{{{doc.title or 'Untitled'}}}}},
  author = {{{{{authors}}}}},
  year = {{{{{doc.year or 'n.d.'}}}}},
  url = {{{{{doc.arxiv_url or ''}}}}}
}}"""
    return {"document_id": document_id, "bibtex": bibtex}


@router.post("/export", summary="Export multiple documents as BibTeX")
async def export_bibtex_batch(
    document_ids: list[str],
    db: ClusterDatabaseService = Depends(get_db),
):
    """Export multiple documents as BibTeX entries."""
    entries = []
    for doc_id in document_ids:
        doc = await db.get_document(doc_id)
        :
            if not doc:
            continue
        authors = " and ".join(doc.authors) if isinstance(doc.authors, list) else doc.authors or "Unknown"
        key = f"pa_{doc_id[:8]}"
        entries.append(f"""@article{{{key},
  title = {{{{{doc.title or 'Untitled'}}}}},
  author = {{{{{authors}}}}},
  year = {{{{{doc.year or 'n.d.'}}}}},
  url = {{{{{doc.arxiv_url or ''}}}}}
}}""")

    return {
        "document_ids": document_ids,
        "count": len(entries),
        "bibtex": "\n\n".join(entries),
    }
