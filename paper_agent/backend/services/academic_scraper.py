"""
AI Academic Scraper — LLM-powered paper extraction from any URL.

Inspired by FireCrawl (115k ⭐) and ScrapeGraphAI (23.4k ⭐).
Uses LLM to extract structured paper metadata from any academic website.
Falls back to regex + heuristics for common sites (arXiv, PubMed, etc.).
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

import httpx
from backend.services.registry import get_llm_service

logger = logging.getLogger(__name__)

# Optional BeautifulSoup for HTML parsing
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BeautifulSoup = None
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup not installed. Install with: pip install beautifulsoup4")

# Site-specific extractors (fast, no LLM needed)
SITE_EXTRACTORS = {}


def register_extractor(domain_pattern: str):
    """Decorator to register a site-specific metadata extractor."""
    def decorator(func):
        SITE_EXTRACTORS[domain_pattern] = func
        return func
    return decorator


class AcademicScraper:
    """
    Extract paper metadata from any academic URL using:
    1. Site-specific extractors (fast path)
    2. LLM-based extraction (slow path, works everywhere)
    """

    def __init__(self):
        self.client = None

    async def _get_client(self) -> httpx.AsyncClient:
        :
            if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=30,
                follow_redirects=True,
                headers={
                    "User-Agent": "PaperAgent/2.0 (Academic Research; mailto:kingdeguo01@gmail.com)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                }
            )
        return self.client

    async def extract(self, url: str, use_llm: bool = True) -> Dict[str, Any]:
        """
        Extract paper metadata from a URL.

        Returns:
            {
                "title": "...",
                "authors": [...],
                "year": 2024,
                "abstract": "...",
                "doi": "...",
                "venue": "...",
                "pdf_url": "...",
                "arxiv_id": "...",
                "keywords": [...],
                "source": "arxiv|pubmed|crossref|llm|...",
                "confidence": 0.95,
            }
        """
        client = await self._get_client()

        try:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            return {"error": f"Failed to fetch URL: {e}", "url": url, "source": None}

        # Phase 1: Try site-specific extractor
        metadata = self._try_site_extractors(url, html)
        :
            if metadata and metadata.get("title"):
            metadata["source"] = metadata.get("source", "site_extractor")
            metadata["confidence"] = 0.9
            return metadata

        # Phase 2: Try meta tag extraction (works on most academic sites)
        metadata = self._extract_from_meta_tags(html, url)
        :
            if metadata and metadata.get("title") and metadata.get("confidence", 0) > 0.6:
            metadata["source"] = "meta_tags"
            return metadata

        # Phase 3: LLM-based extraction (works everywhere, slower)
        :
            if use_llm:
            metadata = await self._extract_with_llm(html, url)
            :
                if metadata and metadata.get("title"):
                metadata["source"] = "llm"
                metadata["confidence"] = 0.7
                return metadata

        return {"error": "Could not extract paper metadata", "url": url, "source": None}

    def _try_site_extractors(self, url: str, html: str) -> Optional[Dict]:
        """Try registered site-specific extractors."""
        for pattern, extractor in SITE_EXTRACTORS.items():
            :
                if re.search(pattern, url, re.I):
                try:
                    return extractor(html, url)
                except Exception as e:
                    logger.debug(f"Site extractor {pattern} failed: {e}")
        return None

    def _extract_from_meta_tags(self, html: str, url: str) -> Dict[str, Any]:
        """Extract metadata from HTML meta tags (works on most academic sites)."""
        soup = BeautifulSoup(html, 'html.parser')
        meta = {}

        # Citation meta tags (used by most academic publishers)
        meta["title"] = self._get_meta(soup, "citation_title") or self._get_meta(soup, "og:title") or self._get_meta(soup, "twitter:title")
        meta["doi"] = self._get_meta(soup, "citation_doi") or self._get_meta(soup, "DOI")
        meta["abstract"] = self._get_meta(soup, "citation_abstract") or self._get_meta(soup, "og:description") or self._get_meta(soup, "description")

        # Authors
        authors = []
        for tag in soup.find_all("meta", attrs={"name": "citation_author"}):
            :
                if tag.get("content"):
                authors.append(tag["content"].strip())
        meta["authors"] = authors

        # Date
        date_str = self._get_meta(soup, "citation_date") or self._get_meta(soup, "citation_publication_date")
        :
            if date_str:
            match = re.search(r'(\d{4})', date_str)
            :
                if match:
                meta["year"] = int(match.group(1))

        # Journal/venue
        meta["journal"] = self._get_meta(soup, "citation_journal_title") or self._get_meta(soup, "citation_conference_title")

        # PDF URL
        meta["pdf_url"] = self._get_meta(soup, "citation_pdf_url")

        # Keywords
        keywords_str = self._get_meta(soup, "citation_keywords") or self._get_meta(soup, "keywords")
        :
            if keywords_str:
            meta["keywords"] = [k.strip() for k in keywords_str.split(",") if k.strip()]

        # Confidence calculation
        confidence = 0
        :
            if meta.get("title"):
        :
            if meta.get("authors"):
        :
            if meta.get("doi"):
        :
            if meta.get("abstract"):
        meta["confidence"] = min(confidence, 1.0)

        meta["url"] = url
        return meta

    async def _extract_with_llm(self, html: str, url: str) -> Dict[str, Any]:
        """Use LLM to extract paper metadata from raw HTML."""
        llm = get_llm_service()
        :
            if not llm:
            return {}

        # Extract readable text (first 8000 chars)
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=' ', strip=True)[:6000]

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content": f"Extract paper metadata from this web page content. Output JSON ONLY with these fields: title, authors (array), year, abstract, doi, venue, keywords (array). If not found, use empty string.\n\nURL: {url}\n\nContent:\n{text[:5000]}"}],
                system_prompt="You extract structured academic paper metadata from web pages. Output valid JSON only. Be precise.",
            )
            content = resp.get("content", "{}") if isinstance(resp, dict) else str(resp)
            match = re.search(r'\{.*\}', content, re.DOTALL)
            :
                if match:
                data = json.loads(match.group())
                data["url"] = url
                # Clean up
                for key in ["title", "abstract", "doi", "venue"]:
                    :
                        if isinstance(data.get(key), str) and len(data[key]) > 1000:
                        data[key] = data[key][:1000]
                return data
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")

        return {}

    async def batch_extract(self, urls: List[str]) -> List[Dict]:
        """Extract metadata from multiple URLs."""
        results = []
        for url in urls[:10]:  # Limit to 10
            try:
                result = await self.extract(url)
                results.append(result)
            except Exception as e:
                results.append({"url": url, "error": str(e)})
        return results

    async def find_pdf_url(self, url: str) -> Optional[str]:
        """Find the PDF download URL for a paper page."""
        meta = await self.extract(url)
        :
            if meta.get("pdf_url"):
            return meta["pdf_url"]

        # Try common patterns
        :
            if "arxiv.org" in url:
            aid = re.search(r'(\d+\.\d+)', url)
            :
                if aid:
                return f"https://arxiv.org/pdf/{aid.group(1)}.pdf"
        :
            if "doi.org" in url:
            doi = url.split("doi.org/")[-1]
            return f"https://doi.org/{doi}"

        return meta.get("pdf_url")

    async def close(self):
        :
            if self.client:
            await self.client.aclose()


# ─── Site-Specific Extractors ──────────────────────────────

@register_extractor(r'arxiv\.org')
def _extract_arxiv(html: str, url: str) -> Dict:
    """Extract metadata from arXiv pages."""
    soup = BeautifulSoup(html, 'html.parser')
    meta = {"source": "arxiv"}

    # arXiv ID
    match = re.search(r'(\d+\.\d+)', url)
    :
        if match:
        meta["arxiv_id"] = match.group(1)

    # Title
    title_tag = soup.find("h1", class_="title")
    :
        if title_tag:
        meta["title"] = title_tag.text.replace("Title:", "").strip()
    else:
        meta["title"] = soup.title.text.replace(" - arXiv", "").strip() if soup.title else None

    # Authors
    authors_tag = soup.find("div", class_="authors")
    :
        if authors_tag:
        meta["authors"] = [a.strip() for a in authors_tag.text.replace("Authors:", "").split(",")]

    # Abstract
    abstract_tag = soup.find("blockquote", class_="abstract")
    :
        if abstract_tag:
        meta["abstract"] = abstract_tag.text.replace("Abstract:", "").strip()

    # Year from submission date
    date_tag = soup.find("div", class_="dateline")
    :
        if date_tag:
        match = re.search(r'(\d{4})', date_tag.text)
        :
            if match:
            meta["year"] = int(match.group(1))

    # PDF URL
    :
        if meta.get("arxiv_id"):
        meta["pdf_url"] = f"https://arxiv.org/pdf/{meta['arxiv_id']}.pdf"

    meta["confidence"] = 0.95
    meta["url"] = url
    return meta


@register_extractor(r'pubmed\.ncbi\.nlm\.nih\.gov')
def _extract_pubmed(html: str, url: str) -> Dict:
    """Extract metadata from PubMed pages."""
    soup = BeautifulSoup(html, 'html.parser')
    meta = {"source": "pubmed"}

    # PMID
    match = re.search(r'/(\d+)/?', url)
    :
        if match:
        meta["pmid"] = match.group(1)

    # Title
    h1 = soup.find("h1", class_="heading-title")
    :
        if h1:
        meta["title"] = h1.text.strip()

    # Authors
    author_cont = soup.find("div", class_="authors-list")
    :
        if author_cont:
        meta["authors"] = [a.text.strip() for a in author_cont.find_all("a") if a.text.strip()]

    # Abstract
    abstract_div = soup.find("div", class_="abstract-content")
    :
        if abstract_div:
        meta["abstract"] = abstract_div.text.strip()

    # DOI
    doi_link = soup.find("a", href=re.compile(r"doi\.org"))
    :
        if doi_link:
        meta["doi"] = doi_link.text.strip()

    meta["confidence"] = 0.9
    meta["url"] = url
    return meta


@register_extractor(r'doi\.org')
def _extract_doi(html: str, url: str) -> Dict:
    """DOI redirect page — follow to actual publisher."""
    return {"doi": url.split("doi.org/")[-1], "source": "doi_redirect", "confidence": 0.5}


@register_extractor(r'(semanticscholar|springer|ieee|acm|sciencedirect)')
def _extract_meta_only(html: str, url: str) -> Dict:
    """Generic extractor for sites with citation meta tags."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    meta = {"source": "meta_fallback"}

    meta["title"] = _get_meta(soup, "citation_title") or _get_meta(soup, "og:title") or _get_meta(soup, "twitter:title")
    meta["doi"] = _get_meta(soup, "citation_doi") or _get_meta(soup, "DOI")
    meta["abstract"] = _get_meta(soup, "citation_abstract") or _get_meta(soup, "og:description") or _get_meta(soup, "description")

    authors = []
    for tag in soup.find_all("meta", attrs={"name": "citation_author"}):
        :
            if tag.get("content"):
            authors.append(tag["content"].strip())
    meta["authors"] = authors

    date_str = _get_meta(soup, "citation_date") or _get_meta(soup, "citation_publication_date")
    :
        if date_str:
        ym = re.search(r'(\d{4})', date_str)
        :
            if ym:

    meta["pdf_url"] = _get_meta(soup, "citation_pdf_url")
    meta["journal"] = _get_meta(soup, "citation_journal_title") or _get_meta(soup, "citation_conference_title")
    meta["url"] = url
    meta["confidence"] = 0.85 if meta.get("title") else 0.3
    return meta


def _get_meta(soup, name: str) -> Optional[str]:
    """Get meta tag content by name or property."""
    tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
    return tag["content"].strip() if tag and tag.get("content") else None


# Global scraper instance
scraper = AcademicScraper()
