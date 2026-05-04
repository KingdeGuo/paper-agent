"""Figure & Table API — extract, browse, search, and compare visual elements."""

import os
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text as sa_text

from backend.services.registry import get_db
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.figure_service import figure_extractor, FIGURES_DIR

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db):
    """Create figure/table tables if needed."""
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS extracted_figures (
                id TEXT PRIMARY KEY, document_id TEXT NOT NULL,
                page INTEGER, idx INTEGER, filename TEXT, filepath TEXT,
                caption TEXT, format TEXT, hash TEXT,
                width INTEGER, height INTEGER, size_bytes INTEGER,
                ai_description TEXT, tags TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS extracted_tables (
                id TEXT PRIMARY KEY, document_id TEXT NOT NULL,
                page INTEGER, data TEXT, rows INTEGER, cols INTEGER,
                caption TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS figure_tags (
                id TEXT PRIMARY KEY, document_id TEXT,
                figure_id TEXT, tag TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]:
            try:
                await session.execute(sa_text(ddl))
            except Exception:
                pass
        await session.commit()


@router.post("/figures/extract/{document_id}", summary="Extract figures from PDF")
async def extract_figures(document_id: str, db=Depends(get_db)):
    """Extract all figures, tables, and charts from a paper's PDF."""
    await ensure_tables(db)
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    result = await figure_extractor.extract_all(document_id, doc.file_path or "", db=db)
    return {
        "document_id": document_id,
        "title": doc.title or doc.filename,
        "figures": result["total_figures"],
        "tables": result["total_tables"],
        "results": result,
    }


@router.get("/figures/{document_id}", summary="Get figures for a document")
async def get_figures(document_id: str, db=Depends(get_db)):
    """Get all extracted figures for a document."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM extracted_figures WHERE document_id = :did ORDER BY page, idx"),
            {"did": document_id})).fetchall()
        return [{
            "id": r[0], "document_id": r[1], "page": r[2], "index": r[3],
            "filename": r[4], "filepath": r[5], "caption": r[6] or "",
            "format": r[7], "width": r[8] or 0, "height": r[9] or 0,
            "size_bytes": r[10] or 0, "ai_description": r[11] or "",
            "tags": json.loads(r[12]) if isinstance(r[12], str) else (r[12] or []),
        } for r in rows]


@router.get("/figures/image/{figure_id}", summary="Get figure image file")
async def get_figure_image(figure_id: str, db=Depends(get_db)):
    """Get the actual image file for a figure."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        row = (await session.execute(sa_text(
            "SELECT filepath, filename FROM extracted_figures WHERE id = :id"),
            {"id": figure_id})).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Figure not found")

    filepath = row[0]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(filepath, media_type=f"image/{row[1].split('.')[-1] if '.' in row[1] else 'png'}")


@router.get("/figures/gallery", summary="Browse all figures across library")
async def browse_figures(
    document_id: str = None,
    page: int = None,
    limit: int = 50,
    offset: int = 0,
    db=Depends(get_db),
):
    """Browse all extracted figures across the library with optional filters."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        sql = "SELECT f.*, d.title as doc_title FROM extracted_figures f LEFT JOIN documents d ON f.document_id = d.id WHERE 1=1"
        params = {}
        if document_id:
            sql += " AND f.document_id = :did"
            params["did"] = document_id
        if page is not None:
            sql += " AND f.page = :p"
            params["p"] = page
        sql += " ORDER BY f.created_at DESC LIMIT :lim OFFSET :off"
        params["lim"] = limit
        params["off"] = offset

        rows = (await session.execute(sa_text(sql), params)).fetchall()
        return [{
            "id": r[0], "document_id": r[1], "page": r[2], "filename": r[4],
            "caption": (r[6] or "")[:200], "doc_title": r[16] or "Unknown",
            "width": r[8] or 0, "height": r[9] or 0,
        } for r in rows]


@router.get("/figures/describe/{figure_id}", summary="AI describe a figure")
async def describe_figure(figure_id: str, db=Depends(get_db)):
    """Generate an AI description of a figure."""
    await ensure_tables(db)
    description = await figure_extractor.describe_figure(figure_id, db=db)
    return {"figure_id": figure_id, "description": description or "No description available"}


@router.get("/tables/{document_id}", summary="Get extracted tables")
async def get_tables(document_id: str, db=Depends(get_db)):
    """Get all extracted tables for a document."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM extracted_tables WHERE document_id = :did ORDER BY page"),
            {"did": document_id})).fetchall()
        return [{
            "id": r[0], "document_id": r[1], "page": r[2],
            "data": json.loads(r[3]) if isinstance(r[3], str) else [],
            "rows": r[4] or 0, "cols": r[5] or 0,
            "caption": r[6] or "",
        } for r in rows]


@router.post("/figures/extract-batch", summary="Extract figures from multiple papers")
async def batch_extract(document_ids: List[str], db=Depends(get_db)):
    """Extract figures from multiple papers at once."""
    results = []
    for did in document_ids[:5]:
        try:
            result = await extract_figures(did, db=db)
            results.append(result)
        except Exception as e:
            results.append({"document_id": did, "error": str(e)})
    return {"total": len(results), "results": results}
