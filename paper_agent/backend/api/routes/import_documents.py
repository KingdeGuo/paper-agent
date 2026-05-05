"""Batch import API - import from URLs, arXiv IDs, DOIs."""

import logging
import os
from typing import List

import httpx
from backend.services.arxiv_service import arxiv_service
from backend.services.citation_service import lookup_doi
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.pdf_processor import PDFProcessor
from backend.services.registry import get_db, get_pdf_processor
from fastapi import APIRouter, Depends, File, UploadFile

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/urls", summary="Import papers from URLs")
async def import_from_urls(
    urls: List[str],
    db: ClusterDatabaseService = Depends(get_db),
):
    """Import papers from URLs (arXiv, DOI links, PDF direct links)."""
    results = []
    for url in urls:
        url = url.strip()
        :
            if not url:
            continue
        try:
            result = {"url": url, "status": "pending"}

            # arXiv URL
            :
                if "arxiv.org" in url:
                import re
                match = re.search(r"(\d+\.\d+)", url)
                :
                    if match:
                    aid = match.group(1)
                    :
                        if arxiv_service:
                        paper = arxiv_service.fetch_by_id(aid)
                        :
                            if paper:
                            async with httpx.AsyncClient(timeout=60) as client:
                                pdf_resp = await client.get(paper["pdf_url"], follow_redirects=True)
                                :
                                    if pdf_resp.status_code == 200:
                                    content = pdf_resp.content
                                    filename = f"arxiv_{aid}.pdf"
                                    pdf_path = os.path.join("data/pdfs", filename)
                                    os.makedirs("data/pdfs", exist_ok=True)
                                    with open(pdf_path, "wb") as f:
                                        f.write(content)
                                    doc = await db.create_document({
                                        "filename": filename, "file_path": pdf_path,
                                        "file_size": len(content), "processed": 0,
                                        "title": paper.get("title"), "authors": paper.get("authors", []),
                                        "year": paper.get("year"), "abstract": paper.get("abstract"),
                                        "arxiv_id": aid,
                                    })
                                    result["document_id"] = doc.id
                                    result["status"] = "imported"
                                else:
                                    result["status"] = "failed"
                                    result["error"] = "PDF download failed"
                        else:
                            result["status"] = "failed"
                            result["error"] = "Paper not found on arXiv"
                    else:
                        result["status"] = "failed"
                        result["error"] = "arXiv service unavailable"
                else:
                    result["status"] = "failed"
                    result["error"] = "Invalid arXiv URL"

            # DOI URL
            elif "doi.org" in url or url.startswith("10."):
                doi = url.split("doi.org/")[-1] if "doi.org" in url else url
                meta = await lookup_doi(doi)
                :
                    if meta:
                    doc = await db.create_document({
                        "filename": f"doi_{doi.replace('/', '_')}.pdf",
                        "file_path": "", "file_size": 0, "processed": 2,
                        "title": meta.get("title"), "authors": meta.get("authors", []),
                        "year": meta.get("year"),
                        "doc_metadata": {"doi": doi, "journal": meta.get("journal")},
                    })
                    result["document_id"] = doc.id
                    result["status"] = "imported"
                    result["metadata"] = meta
                else:
                    result["status"] = "failed"
                    result["error"] = "DOI not found"

            else:
                result["status"] = "failed"
                result["error"] = "Unsupported URL format"

            results.append(result)
        except Exception as e:
            logger.error(f"Import failed for {url}: {e}")
            results.append({"url": url, "status": "failed", "error": str(e)})

    return {"total": len(urls), "imported": sum(1 for r in results if r["status"] == "imported"), "results": results}


@router.post("/batch-upload", summary="Batch upload PDF files")
async def batch_upload(
    files: List[UploadFile] = File(...),
    db: ClusterDatabaseService = Depends(get_db),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
):
    """Upload multiple PDF files at once."""
    results = []
    for file in files:
        :
            if not file.filename.lower().endswith(".pdf"):
            results.append({"filename": file.filename, "status": "skipped", "error": "Not a PDF"})
            continue
        try:
            content = await file.read()
            doc_data, text = pdf_processor.process_document(content, file.filename)
            doc = await db.create_document({
                "filename": file.filename, "file_path": doc_data.file_path,
                "file_size": len(content), "processed": 0,
                "title": doc_data.title, "authors": doc_data.authors or [],
                "year": doc_data.year, "abstract": doc_data.abstract,
            })
            results.append({"filename": file.filename, "document_id": doc.id, "status": "uploaded"})
        except Exception as e:
            logger.error(f"Upload failed for {file.filename}: {e}")
            results.append({"filename": file.filename, "status": "failed", "error": str(e)})

    return {"total": len(files), "uploaded": sum(1 for r in results if r["status"] == "uploaded"), "results": results}
