"""Data Quality Engine — validation, integrity checks, analytics across all data."""

import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

from backend.services.registry import get_db
from backend.services.cluster_database import ClusterDatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/data-quality/report", summary="Full data quality report")
async def data_quality_report(db=Depends(get_db)):
    """Generate a comprehensive data quality report across all subsystems."""
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "overall_score": 0,
        "sections": {},
        "issues": [],
        "recommendations": [],
    }
    total_checks = 0
    passed_checks = 0

    # 1. Documents
    try:
        docs = await db.get_documents(limit=10000) if db else []
        doc_count = len(docs)
        missing_title = sum(1 for d in docs if not d.title)
        missing_authors = sum(1 for d in docs if not d.authors)
        missing_abstract = sum(1 for d in docs if not d.abstract)
        missing_year = sum(1 for d in docs if not d.year)
        no_summary = sum(1 for d in docs if not d.summary and d.processed == 2)

        doc_score = 100
        issues = []
        if missing_title > 0: doc_score -= 5; issues.append(f"{missing_title} papers missing title")
        if missing_authors > 0: doc_score -= 5; issues.append(f"{missing_authors} papers missing authors")
        if missing_abstract > 0: doc_score -= 5; issues.append(f"{missing_abstract} papers missing abstract")
        if missing_year > 0: doc_score -= 3; issues.append(f"{missing_year} papers missing year")
        if no_summary > 0: doc_score -= 5; issues.append(f"{no_summary} processed papers missing AI summary")

        report["sections"]["documents"] = {
            "total": doc_count, "score": max(0, doc_score),
            "missing_title": missing_title, "missing_authors": missing_authors,
            "missing_abstract": missing_abstract, "missing_year": missing_year,
            "no_summary": no_summary, "issues": issues,
        }
        total_checks += 1
        if doc_score >= 80: passed_checks += 1
        for i in issues: report["issues"].append(f"[Documents] {i}")
    except Exception as e:
        report["sections"]["documents"] = {"error": str(e)}

    # 2. Reading List
    try:
        async with db.async_session_maker() as session:
            total = (await session.execute(sa_text("SELECT COUNT(*) FROM reading_list"))).scalar() or 0
            orphaned = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM reading_list r LEFT JOIN documents d ON r.document_id = d.id WHERE d.id IS NULL"))).scalar() or 0
            report["sections"]["reading_list"] = {"total": total, "orphaned_entries": orphaned}
            if orphaned > 0: report["issues"].append(f"[Reading List] {orphaned} orphaned entries (document no longer exists)")
            total_checks += 1
            if orphaned == 0: passed_checks += 1
    except: pass

    # 3. Flashcards
    try:
        async with db.async_session_maker() as session:
            total = (await session.execute(sa_text("SELECT COUNT(*) FROM flashcards WHERE is_deleted = 0"))).scalar() or 0
            orphaned = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM flashcards f LEFT JOIN documents d ON f.document_id = d.id WHERE d.id IS NULL AND f.is_deleted = 0"))).scalar() or 0
            report["sections"]["flashcards"] = {"total": total, "orphaned": orphaned}
            if orphaned > 0: report["issues"].append(f"[Flashcards] {orphaned} cards reference deleted documents")
            total_checks += 1
            if orphaned == 0: passed_checks += 1
    except: pass

    # 4. Discussions
    try:
        async with db.async_session_maker() as session:
            total = (await session.execute(sa_text("SELECT COUNT(*) FROM paper_discussions WHERE is_deleted = 0"))).scalar() or 0
            orphaned = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM paper_discussions pd LEFT JOIN documents d ON pd.document_id = d.id WHERE d.id IS NULL AND pd.is_deleted = 0"))).scalar() or 0
            report["sections"]["discussions"] = {"total": total, "orphaned": orphaned}
            if orphaned > 0: report["issues"].append(f"[Discussions] {orphaned} discussions reference deleted documents")
            total_checks += 1
            if orphaned == 0: passed_checks += 1
    except: pass

    # 5. Codex
    try:
        async with db.async_session_maker() as session:
            total = (await session.execute(sa_text("SELECT COUNT(*) FROM codex_entries WHERE is_deleted = 0"))).scalar() or 0
            orphaned = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM codex_entries ce LEFT JOIN documents d ON ce.source_document_id = d.id WHERE d.id IS NULL AND ce.is_deleted = 0 AND ce.source_document_id IS NOT NULL"))).scalar() or 0
            report["sections"]["codex"] = {"total": total, "orphaned": orphaned}
            total_checks += 1
            if orphaned == 0: passed_checks += 1
    except: pass

    # 6. Duplicates
    try:
        from backend.api.routes.dedup import detect_duplicates
        dup_result = await detect_duplicates(db=db)
        dup_count = len(dup_result.get("duplicates", []))
        report["sections"]["duplicates"] = {"potential_duplicates": dup_count}
        if dup_count > 0: report["issues"].append(f"[Duplicates] {dup_count} potential duplicate pairs detected")
        total_checks += 1
        if dup_count == 0: passed_checks += 1
    except: pass

    # 7. Missing metadata
    try:
        async with db.async_session_maker() as session:
            no_doi = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM documents WHERE doc_metadata IS NULL OR doc_metadata = '{}' OR json_extract(doc_metadata, '$.doi') IS NULL"))).scalar() or 0
            report["sections"]["metadata"] = {"missing_doi": no_doi}
            total_checks += 1
            if no_doi == 0: passed_checks += 1
    except: pass

    # Compute overall score
    report["overall_score"] = round((passed_checks / max(total_checks, 1)) * 100, 1)
    report["total_checks"] = total_checks
    report["passed_checks"] = passed_checks
    report["failed_checks"] = total_checks - passed_checks

    # Recommendations
    if report.get("sections", {}).get("documents", {}).get("missing_title", 0) > 0:
        report["recommendations"].append("Run metadata enhancement to fill missing titles")
    if report.get("sections", {}).get("duplicates", {}).get("potential_duplicates", 0) > 0:
        report["recommendations"].append("Run auto-dedup to merge duplicate papers")
    if report.get("sections", {}).get("reading_list", {}).get("orphaned_entries", 0) > 0:
        report["recommendations"].append("Clean up orphaned reading list entries")

    return report


@router.post("/data-quality/clean", summary="Auto-clean data issues")
async def auto_clean(db=Depends(get_db)):
    """Automatically fix common data quality issues."""
    fixed = {"orphaned_reading_list": 0, "orphaned_flashcards": 0, "orphaned_discussions": 0, "orphaned_codex": 0, "metadata_enhanced": 0}

    # 1. Remove orphaned reading list entries
    try:
        async with db.async_session_maker() as session:
            result = await session.execute(sa_text(
                "DELETE FROM reading_list WHERE document_id IN (SELECT r.document_id FROM reading_list r LEFT JOIN documents d ON r.document_id = d.id WHERE d.id IS NULL)"))
            fixed["orphaned_reading_list"] = result.rowcount
            await session.commit()
    except: pass

    # 2. Remove orphaned flashcards
    try:
        async with db.async_session_maker() as session:
            result = await session.execute(sa_text(
                "DELETE FROM flashcards WHERE document_id IN (SELECT f.document_id FROM flashcards f LEFT JOIN documents d ON f.document_id = d.id WHERE d.id IS NULL)"))
            fixed["orphaned_flashcards"] = result.rowcount
            await session.commit()
    except: pass

    # 3. Remove orphaned discussions
    try:
        async with db.async_session_maker() as session:
            result = await session.execute(sa_text(
                "DELETE FROM paper_discussions WHERE document_id IN (SELECT pd.document_id FROM paper_discussions pd LEFT JOIN documents d ON pd.document_id = d.id WHERE d.id IS NULL)"))
            fixed["orphaned_discussions"] = result.rowcount
            await session.commit()
    except: pass

    # 4. Remove orphaned codex entries
    try:
        async with db.async_session_maker() as session:
            result = await session.execute(sa_text(
                "DELETE FROM codex_entries WHERE source_document_id IN (SELECT ce.source_document_id FROM codex_entries ce LEFT JOIN documents d ON ce.source_document_id = d.id WHERE d.id IS NULL AND ce.source_document_id IS NOT NULL)"))
            fixed["orphaned_codex"] = result.rowcount
            await session.commit()
    except: pass

    # 5. Auto-enhance metadata for papers missing key fields
    try:
        from backend.api.routes.metadata_enhance import enhance_metadata
        docs = await db.get_documents(limit=50) if db else []
        for doc in docs:
            if not doc.title or not doc.authors:
                try:
                    await enhance_metadata(doc.id, db=db)
                    fixed["metadata_enhanced"] += 1
                except: pass
    except: pass

    return {"fixed": fixed, "total_fixed": sum(fixed.values())}
