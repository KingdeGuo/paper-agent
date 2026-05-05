"""
Citation management service.

Handles:
- BibTeX import/export
- Citation key generation
- DOI metadata lookup
- Citation formatting (APA, MLA, Chicago, IEEE, etc.)
"""

import logging
import re
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


def generate_citation_key(
    authors: Optional[List[str]],
    year: Optional[int],
    title: Optional[str] = None
) -> str:
    """Generate a unique citation key like 'Smith2024' or 'SmithJohnson2024'."""
    key = "Unknown"
    if authors and len(authors) > 0:
        parts = []
        for a in authors[:2]:
            surname = a.strip().split(",")[0].split()[-1] if " " in a.strip() else a.strip()
            parts.append(surname)
        key = "".join(parts)
    if year:
        key += str(year)
    elif title:
        key += str(hash(title) % 10000)
    return re.sub(r"[^a-zA-Z0-9]", "", key)


def format_authors_for_bibtex(authors: List[str]) -> str:
    """Format author list for BibTeX."""
    formatted = []
    for a in authors:
        a = a.strip()
        if "," in a:
            formatted.append(a)
        else:
            parts = a.rsplit(" ", 1)
            if len(parts) == 2:
                formatted.append(f"{parts[1]}, {parts[0]}")
            else:
                formatted.append(a)
    return " and ".join(formatted)


def doc_to_bibtex(
    doc_id: str,
    title: Optional[str],
    authors: Optional[List[str]],
    year: Optional[int],
    journal: Optional[str] = None,
    volume: Optional[str] = None,
    number: Optional[str] = None,
    pages: Optional[str] = None,
    doi: Optional[str] = None,
    url: Optional[str] = None,
    abstract: Optional[str] = None,
    key: Optional[str] = None,
) -> str:
    """Convert document metadata to BibTeX entry."""
    if not key:
        key = generate_citation_key(authors, year, title)
    if title:
        title = title.strip().rstrip(".")
    author_str = format_authors_for_bibtex(authors) if authors else "Unknown"

    fields = []
    if title:
        fields.append(f"  title = {{{{{title}}}}}")
    if author_str:
        fields.append(f"  author = {{{{{author_str}}}}}")
    if year:
        fields.append(f"  year = {{{year}}}")
    if journal:
        fields.append(f"  journal = {{{{{journal}}}}}")
    if volume:
        fields.append(f"  volume = {{{volume}}}")
    if number:
        fields.append(f"  number = {{{number}}}")
    if pages:
        fields.append(f"  pages = {{{pages}}}")
    if doi:
        fields.append(f"  doi = {{{doi}}}")
    if url:
        fields.append(f"  url = {{{url}}}")
    if abstract:
        abstract_clean = abstract.replace("}", "\\}").replace("{", "\\{")
        fields.append(f"  abstract = {{{abstract_clean[:500]}}}")

    fields_str = ",\n".join(fields)
    return f"""@article{{{key},
{fields_str}
}}"""


def parse_bibtex(bibtex_str: str) -> List[Dict[str, Any]]:
    """Parse a BibTeX string into a list of entry dicts."""
    entries = []
    pattern = r"@(\w+)\s*\{\s*([^,]+),\s*([^@]*?)\s*\}"
    matches = re.findall(pattern, bibtex_str, re.DOTALL)

    for entry_type, key, fields_str in matches:
        entry = {
            "type": entry_type.lower(),
            "key": key.strip(),
            "fields": {},
        }
        field_pattern = r"(\w+)\s*=\s*\{(.*?)\}"
        for fname, fvalue in re.findall(field_pattern, fields_str, re.DOTALL):
            entry["fields"][fname.lower()] = fvalue.strip()
        entries.append(entry)

    return entries


CITATION_STYLES = {
    "apa": {
        "name": "APA 7th Edition",
        "template": "{authors} ({year}). {title}. {journal}, {volume}({number}), {pages}. https://doi.org/{doi}" if "{doi}" else "{authors} ({year}). {title}. {journal}, {volume}({number}), {pages}.",
    },
    "mla": {
        "name": "MLA 9th Edition",
        "template": "{authors}. \"{title}.\" {journal}, vol. {volume}, no. {number}, {year}, pp. {pages}.",
    },
    "chicago": {
        "name": "Chicago 17th Edition",
        "template": "{authors}. \"{title}.\" {journal} {volume}, no. {number} ({year}): {pages}.",
    },
    "ieee": {
        "name": "IEEE",
        "template": "{authors}, \"{title},\" {journal}, vol. {volume}, no. {number}, pp. {pages}, {year}.",
    },
    "vancouver": {
        "name": "Vancouver",
        "template": "{authors}. {title}. {journal}. {year};{volume}({number}):{pages}.",
    },
    "harvard": {
        "name": "Harvard",
        "template": "{authors} ({year}) \"{title},\" {journal}, {volume}({number}), pp. {pages}.",
    },
}


def format_inline_citation(
    authors: Optional[List[str]],
    year: Optional[int],
    style: str = "apa",
) -> str:
    """Generate an inline citation like (Smith, 2024) or Smith (2024)."""
    surname = authors[0].strip().split(",")[0].split()[-1] if authors else "Unknown"

    if style == "apa":
        return f"({surname}, {year})" if year else f"({surname})"
    elif style == "mla":
        return f"({surname} {year})" if year else f"({surname})"
    elif style == "chicago":
        return f"({surname} {year})" if year else f"({surname})"
    elif style == "ieee":
        return f"[{1}]"  # Would need actual numbering
    else:
        return f"({surname}, {year})" if year else f"({surname})"


async def lookup_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Lookup metadata for a DOI via CrossRef API."""
    url = f"https://api.crossref.org/works/{doi}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            msg = data.get("message", {})

            authors = []
            for a in msg.get("author", []):
                given = a.get("given", "")
                family = a.get("family", "")
                if family:
                    authors.append(f"{family}, {given}" if given else family)

            return {
                "title": msg.get("title", [""])[0] if msg.get("title") else None,
                "authors": authors,
                "year": int(msg.get("published-print", {}).get("date-parts", [[None]])[0][0] or
                          msg.get("created", {}).get("date-parts", [[None]])[0][0] or 0),
                "journal": msg.get("container-title", [""])[0] if msg.get("container-title") else None,
                "volume": msg.get("volume"),
                "issue": msg.get("issue"),
                "pages": msg.get("page"),
                "doi": doi,
                "publisher": msg.get("publisher"),
                "type": msg.get("type"),
            }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        logger.warning(f"DOI lookup failed for {doi}: {e}")
        return None
    except Exception as e:
        logger.warning(f"DOI lookup error for {doi}: {e}")
        return None


def generate_bibliography(
    entries: List[Dict[str, Any]],
    style: str = "apa",
    sort: str = "author",
) -> str:
    """Generate a formatted bibliography from citation entries."""
    if sort == "author":
        entries.sort(key=lambda e: (e.get("authors") or ["Unknown"])[0] if e.get("authors") else "Unknown")

    style_config = CITATION_STYLES.get(style, CITATION_STYLES["apa"])
    refs = []

    for i, entry in enumerate(entries):
        authors = entry.get("authors", [])
        year = entry.get("year")
        title = entry.get("title", "Untitled")
        journal = entry.get("journal", "")
        volume = entry.get("volume", "")
        number = entry.get("issue", "")
        pages = entry.get("pages", "")
        doi = entry.get("doi", "")

        # Format authors
        if authors:
            if style == "apa":
                formatted_authors = []
                for j, a in enumerate(authors):
                    parts = a.split(", ")
                    if len(parts) == 2:
                        formatted_authors.append(f"{parts[0]}, {parts[1][0]}.")
                    else:
                        formatted_authors.append(parts[0])
                if len(formatted_authors) > 7:
                    formatted_authors = formatted_authors[:7] + ["..."]
                author_str = ", ".join(formatted_authors[:-1]) + " & " + formatted_authors[-1] if len(formatted_authors) > 1 else formatted_authors[0]
            elif style == "ieee":
                author_str = ", ".join(authors[:6]) + (" et al." if len(authors) > 6 else "")
            else:
                author_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
        else:
            author_str = "Unknown"

        ref = f"{author_str} ({year}). {title}."
        if journal:
            ref += f" {journal}"
            if volume:
                ref += f", {volume}"
            if number:
                ref += f"({number})"
            if pages:
                ref += f", {pages}"
        ref += "."
        if doi:
            if style == "apa":
                ref += f" https://doi.org/{doi}"
            elif style == "mla":
                ref += f" doi:{doi}"

        refs.append(f"[{i+1}] " + ref if style == "ieee" else ref)

    return "\n\n".join(refs)


async def search_crossref(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search CrossRef for publications matching a query."""
    url = "https://api.crossref.org/works"
    params = {"query": query, "rows": limit}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("message", {}).get("items", [])

            results = []
            for item in items:
                authors = []
                for a in item.get("author", []):
                    given = a.get("given", "")
                    family = a.get("family", "")
                    if family:
                        authors.append(f"{family}, {given}" if given else family)

                results.append({
                    "title": item.get("title", [""])[0] if item.get("title") else "Untitled",
                    "authors": authors,
                    "year": int(item.get("published-print", {}).get("date-parts", [[None]])[0][0] or
                             item.get("created", {}).get("date-parts", [[None]])[0][0] or 0),
                    "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                    "doi": item.get("DOI", ""),
                    "type": item.get("type", ""),
                    "url": item.get("URL", ""),
                })

            return results
    except Exception as e:
        logger.warning(f"CrossRef search failed: {e}")
        return []
