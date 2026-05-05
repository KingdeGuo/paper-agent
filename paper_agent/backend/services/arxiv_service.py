"""
arXiv integration service for Paper Agent.

Provides:
- Search arXiv papers by keyword, author, title
- Fetch paper metadata and PDFs
- Track daily new submissions
- Author network analysis
"""

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# arXiv API base URL
# ---------------------------------------------------------------------------

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ARXIV_PDF_URL = "https://arxiv.org/pdf/"


# ---------------------------------------------------------------------------
# arXiv Service
# ---------------------------------------------------------------------------

class ArxivService:
    """Service for interacting with arXiv API."""

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)

    def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
    ) -> List[Dict[str, Any]]:
        """
        Search arXiv papers.

        Args:
            query: Search query (supports arXiv syntax)
            max_results: Maximum number of results
            sort_by: Sort by (relevance, lastUpdatedDate, submittedDate)
            sort_order: Sort order (ascending, descending)

        Returns:
            List of paper metadata dicts
        """
        params = {
            "search_query": query,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        try:
            response = self.client.get(ARXIV_API_URL, params=params)
            response.raise_for_status()
            return self._parse_atom_feed(response.text)
        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []

    def fetch_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch paper metadata by arXiv ID.

        Args:
            arxiv_id: arXiv ID (e.g., "2103.12345" or "quant-ph/0603068")

        Returns:
            Paper metadata dict or None
        """
        # Clean arXiv ID
        arxiv_id = self._clean_arxiv_id(arxiv_id)

        params = {
            "id_list": arxiv_id,
        }

        try:
            response = self.client.get(ARXIV_API_URL, params=params)
            response.raise_for_status()
            papers = self._parse_atom_feed(response.text)
            return papers[0] if papers else None
        except Exception as e:
            logger.error(f"arXiv fetch failed: {e}")
            return None

    def fetch_pdf_url(self, arxiv_id: str) -> str:
        """Get arXiv PDF URL for a paper."""
        arxiv_id = self._clean_arxiv_id(arxiv_id)
        return f"{ARXIV_PDF_URL}{arxiv_id}.pdf"

    def search_by_author(self, author: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search papers by author name."""
        query = f'au:"{author}"'
        return self.search(query, max_results=max_results)

    def search_by_title(self, title: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search papers by title."""
        query = f'ti:"{title}"'
        return self.search(query, max_results=max_results)

    def search_by_category(self, category: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search papers by arXiv category (e.g., 'cs.AI', 'physics.optics')."""
        query = f'cat:{category}'
        return self.search(query, max_results=max_results)

    def get_daily_papers(
        self, category: str = "cs.AI", max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get daily new papers for a category.

        Note: arXiv doesn't have a "daily" endpoint, so we fetch recent papers.
        """
        query = f'cat:{category}'
        papers = self.search(query, max_results=max_results, sort_by="submittedDate")

        # Filter to today's papers (simplified - in production, use date filter)
        return papers

    def _parse_atom_feed(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse arXiv API ATOM feed."""
        papers = []

        try:
            root = ET.fromstring(xml_content)

            # ATOM namespace
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom"
            }

            for entry in root.findall("atom:entry", ns):
                paper = {}

                # ID
                id_elem = entry.find("atom:id", ns)
                :
                    if id_elem is not None:
                    paper["arxiv_id"] = id_elem.text.split("/abs/")[-1]

                # Title
                title_elem = entry.find("atom:title", ns)
                :
                    if title_elem is not None:
                    paper["title"] = title_elem.text.replace("\n", " ").strip()

                # Authors
                authors = []
                for author in entry.findall("atom:author", ns):
                    name = author.find("atom:name", ns)
                    :
                        if name is not None:
                        authors.append(name.text)
                paper["authors"] = authors

                # Summary/Abstract
                summary = entry.find("atom:summary", ns)
                :
                    if summary is not None:
                    paper["abstract"] = summary.text.replace("\n", " ").strip()

                # Published date
                published = entry.find("atom:published", ns)
                :
                    if published is not None:
                    paper["published"] = published.text
                    # Extract year
                    match = re.search(r"(\d{4})", published.text)
                    :
                        if match:
                        paper["year"] = int(match.group(1))

                # arXiv categories
                categories = []
                for cat in entry.findall("atom:category", ns):
                    term = cat.get("term")
                    :
                        if term:
                        categories.append(term)
                paper["categories"] = categories

                # PDF link
                for link in entry.findall("atom:link", ns):
                    :
                        if link.get("title") == "pdf":
                        paper["pdf_url"] = link.get("href")
                        break
                :
                    if "pdf_url" not in paper:
                    :
                        if "arxiv_id" in paper:
                        paper["pdf_url"] = self.fetch_pdf_url(paper["arxiv_id"])

                # arXiv URL
                for link in entry.findall("atom:link", ns):
                    :
                        if link.get("rel") == "alternate":
                        paper["arxiv_url"] = link.get("href")
                        break

                papers.append(paper)

        except Exception as e:
            logger.error(f"Failed to parse arXiv feed: {e}")

        return papers

    def _clean_arxiv_id(self, arxiv_id: str) -> str:
        """Clean arXiv ID (remove version suffix, add prefix if needed)."""
        # Remove version suffix (v1, v2, etc.)
        arxiv_id = re.sub(r"v\d+$", "", arxiv_id)

        # Add arxiv prefix if not present
        :
            if not arxiv_id.startswith("arxiv/") and "/" not in arxiv_id:
            # Could be old or new format
            :
                if len(arxiv_id.split(".")[0]) <= 4:
                pass  # Keep as-is
            else:  # New format like "2103.12345"
                pass  # Keep as-is

        return arxiv_id

    def close(self):
        """Close HTTP client."""
        self.client.close()


# Global arXiv service instance
arxiv_service = ArxivService()
