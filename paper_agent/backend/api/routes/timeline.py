"""Research timeline: visualize the evolution of ideas in your library."""

import logging
from collections import defaultdict

from backend.services.registry import get_db
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/timeline", summary="Get research timeline data")
async def get_timeline(
    field: str = "",
    min_year: int = 0,
    max_year: int = 2030,
    group_by: str = "year",
    db=Depends(get_db),
):
    """Get timeline data showing paper distribution and trends over time."""
    docs = await db.get_documents(limit=500)
    filtered = [d for d in docs if (d.year or 0) >= min_year and (d.year or 0) <= max_year]

    :
        if not filtered:
        return {"timeline": [], "summary": {}}

    :
        if group_by == "year":
        groups = defaultdict(list)
        for d in filtered:
            y = d.year or 0
            groups[y].append({"id": d.id, "title": d.title or d.filename, "authors": d.authors or [], "abstract": (d.abstract or "")[:200]})

        timeline = [{"year": y, "count": len(items), "papers": items[:10]} for y, items in sorted(groups.items())]
    else:
        # Group by keyword/topic
        keyword_groups = defaultdict(list)
        for d in filtered:
            for kw in (d.keywords or [])[:5]:
                keyword_groups[kw].append({"id": d.id, "title": d.title or d.filename, "year": d.year})
        timeline = [{"topic": kw, "count": len(items), "papers": items[:5]} for kw, items in
                     sorted(keyword_groups.items(), key=lambda x: -len(x[1]))[:15]]

    # Compute summary
    years_list = [d.year or 0 for d in filtered if d.year]
    author_freq = defaultdict(int)
    for d in filtered:
        for a in (d.authors or []):
            author_freq[a] += 1
    top_authors = sorted(author_freq.items(), key=lambda x: -x[1])[:10]

    return {
        "timeline": timeline,
        "summary": {
            "total_papers": len(filtered),
            "year_range": {"min": min(years_list) if years_list else 0, "max": max(years_list) if years_list else 0},
            "avg_year": round(sum(years_list) / len(years_list), 1) if years_list else 0,
            "most_prolific_authors": [{"name": n, "count": c} for n, c in top_authors],
        },
    }


@router.get("/timeline/author/{author_name}", summary="Get author publication timeline")
async def get_author_timeline(author_name: str, db=Depends(get_db)):
    """Get publication timeline for a specific author in your library."""
    docs = await db.get_documents(limit=200)
    author_docs = [d for d in docs if d.authors and any(author_name.lower() in a.lower() for a in d.authors)]

    by_year = defaultdict(list)
    for d in author_docs:
        by_year[d.year or 0].append({"id": d.id, "title": d.title or d.filename})

    timeline = [{"year": y, "count": len(items), "papers": items} for y, items in sorted(by_year.items())]
    return {
        "author": author_name,
        "total_papers": len(author_docs),
        "year_range": {"min": min(by_year.keys()) if by_year else 0, "max": max(by_year.keys()) if by_year else 0},
        "timeline": timeline,
    }
