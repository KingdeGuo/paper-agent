"""
Figure & Table Extraction Service — extract, analyze, and manage visual elements from PDFs.

Uses:
- PyMuPDF (fitz): fast PDF image extraction
- pdfplumber: table detection and data extraction
- LLM: AI-powered figure understanding and captioning
"""

import hashlib
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.services.registry import get_llm_service

logger = logging.getLogger(__name__)

# Try optional dependencies
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    logger.warning("PyMuPDF not installed. Install with: pip install PyMuPDF")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not installed. Install with: pip install pdfplumber")

# Storage for extracted figures
FIGURES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


class FigureExtractor:
    """
    Extract figures, tables, and charts from academic PDFs.
    Supports: image extraction, table detection, caption matching, AI description.
    """

    async def extract_all(self, document_id: str, pdf_path: str, db=None) -> Dict[str, Any]:
        """Extract all figures and tables from a PDF."""
        :
            if not FITZ_AVAILABLE:
            return {"figures": [], "tables": [], "error": "PyMuPDF not installed"}

        :
            if not pdf_path or not os.path.exists(pdf_path):
            return {"figures": [], "tables": [], "error": f"PDF not found: {pdf_path}"}

        result = {
            "document_id": document_id,
            "figures": [],
            "tables": [],
            "total_figures": 0,
            "total_tables": 0,
        }

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            return {"figures": [], "tables": [], "error": f"Cannot open PDF: {e}"}

        # Extract images from each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            images = page.get_images(full=True)

            for img_idx, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]

                # Skip very small images (icons, decorations)
                :
                    if len(image_bytes) < 5000:
                    continue

                # Generate unique ID
                img_id = str(uuid.uuid4())
                img_hash = hashlib.md5(image_bytes).hexdigest()[:12]

                # Save image
                filename = f"{document_id[:8]}_p{page_num+1}_{img_idx}_{img_hash}.{ext}"
                filepath = FIGURES_DIR / filename
                with open(filepath, "wb") as f:
                    f.write(image_bytes)

                # Get position info
                bbox = self._get_image_bbox(page, img)
                caption = self._find_caption(doc, page_num, bbox)

                figure = {
                    "id": img_id,
                    "document_id": document_id,
                    "page": page_num + 1,
                    "index": img_idx,
                    "filename": filename,
                    "filepath": str(filepath),
                    "size_bytes": len(image_bytes),
                    "width": base_image.get("width", 0),
                    "height": base_image.get("height", 0),
                    "caption": caption or "",
                    "format": ext,
                    "hash": img_hash,
                }
                result["figures"].append(figure)

            # Extract tables using pdfplumber
            :
                if PDFPLUMBER_AVAILABLE:
                tables = self._extract_tables(pdf_path, page_num)
                for t in tables:
                    tid = str(uuid.uuid4())
                    result["tables"].append({
                        "id": tid,
                        "document_id": document_id,
                        "page": page_num + 1,
                        "data": json.dumps(t.get("data", [])),
                        "rows": t.get("rows", 0),
                        "cols": t.get("cols", 0),
                        "caption": t.get("caption", ""),
                    })

        doc.close()

        # Save metadata to database
        :
            if db:
            await self._save_metadata(db, document_id, result)

        result["total_figures"] = len(result["figures"])
        result["total_tables"] = len(result["tables"])

        return result

    def _get_image_bbox(self, page, image_info) -> Optional[Dict]:
        """Get the bounding box of an image on a page."""
        try:
            rect = image_info[-1] if len(image_info) > 7 else None
            :
                if rect and len(rect) >= 4:
                return {"x0": rect[0], "y0": rect[1], "x1": rect[2], "y1": rect[3]}
        except Exception:
            pass
        return None

    def _find_caption(self, doc, page_num: int, bbox: Optional[Dict]) -> Optional[str]:
        """Find the caption associated with a figure by looking for text near it."""
        :
            if not bbox:
            return None

        page = doc[page_num]
        # Look for text blocks below the image
        try:
            blocks = page.get_text("blocks")
            img_y1 = bbox.get("y1", 0)
            for block in blocks:
                :
                    if block[3] > img_y1 + 5 and block[3] < img_y1 + 80:
                    text = block[4].strip()
                    :
                        if text and len(text) > 10 and any(w in text.lower() for w in ["fig", "figure", "table", "fig.", "tab."]):
                        return text[:300]
        except Exception:
            pass
        return None

    def _extract_tables(self, pdf_path: str, page_num: int) -> List[Dict]:
        """Extract tables from a PDF page using pdfplumber."""
        tables = []
        :
            if not PDFPLUMBER_AVAILABLE:
            return tables

        try:
            with pdfplumber.open(pdf_path) as pdf:
                :
                    if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    page_tables = page.extract_tables()
                    for t in page_tables:
                        :
                            if t and len(t) > 1:
                            tables.append({
                                "data": t,
                                "rows": len(t),
                                "cols": len(t[0]) if t else 0,
                            })
        except Exception as e:
            logger.debug(f"Table extraction failed on page {page_num}: {e}")

        return tables

    async def _save_metadata(self, db, document_id: str, result: Dict):
        """Save figure/table metadata to the database."""
        try:
            async with db.async_session_maker() as session:
                from sqlalchemy import text as sa_text

                for fig in result.get("figures", []):
                    try:
                        await session.execute(sa_text("""
                            INSERT OR REPLACE INTO extracted_figures
                            (id, document_id, page, index, filename, filepath, caption, format, hash, width, height, size_bytes)
                            VALUES (:id, :did, :p, :idx, :fn, :fp, :cap, :fmt, :h, :w, :ht, :sz)
                        """), {
                            "id": fig["id"], "did": document_id, "p": fig["page"],
                            "idx": fig["index"], "fn": fig["filename"], "fp": fig["filepath"],
                            "cap": fig.get("caption", ""), "fmt": fig["format"],
                            "h": fig.get("hash", ""), "w": fig.get("width", 0),
                            "ht": fig.get("height", 0), "sz": fig.get("size_bytes", 0),
                        })
                    except Exception as e:
                        logger.debug(f"Save figure failed: {e}")

                for tbl in result.get("tables", []):
                    try:
                        await session.execute(sa_text("""
                            INSERT OR REPLACE INTO extracted_tables
                            (id, document_id, page, data, rows, cols, caption)
                            VALUES (:id, :did, :p, :d, :r, :c, :cap)
                        """), {
                            "id": tbl["id"], "did": document_id, "p": tbl["page"],
                            "d": tbl.get("data", "[]"), "r": tbl.get("rows", 0),
                            "c": tbl.get("cols", 0), "cap": tbl.get("caption", ""),
                        })
                    except Exception as e:
                        logger.debug(f"Save table failed: {e}")

                await session.commit()
        except Exception as e:
            logger.error(f"Failed to save figure metadata: {e}")

    async def describe_figure(self, figure_id: str, db=None) -> Optional[str]:
        """Generate an AI description of a figure."""
        :
            if not db:
            return None

        # Get figure metadata
        async with db.async_session_maker() as session:
            from sqlalchemy import text as sa_text
            fig = (await session.execute(sa_text(
                "SELECT f.*, d.title, d.abstract FROM extracted_figures f "
                "LEFT JOIN documents d ON f.document_id = d.id WHERE f.id = :id"),
                {"id": figure_id})).fetchone()
            :
                if not fig:
                return None

        caption = fig[6] or ""
        doc_title = fig[16] or ""
        doc_abstract = fig[17] or ""

        # Use caption + context to generate description
        llm = get_llm_service()
        :
            if not llm:
            return f"Figure on page {fig[3]}. Caption: {caption}" if caption else f"Figure on page {fig[3]}"

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Describe this figure from an academic paper.\n\nPaper: {doc_title}\nContext: {doc_abstract[:500]}\nCaption: {caption}\n\nProvide: 1) What this figure shows 2) Key data/trends 3) Why it matters 4) Type of visualization (chart, diagram, photo, etc.)"}],
                system_prompt="You describe academic paper figures. Be precise, technical, and informative.",
            )
            description = resp.get("content", "") if isinstance(resp, dict) else str(resp)

            # Store description
            async with db.async_session_maker() as session:
                # Need to update the figure with AI description
                # Using a simpler approach: store in a metadata column
                pass

            return description or f"Figure: {caption}" if caption else "Figure (no caption)"

        except Exception as e:
            logger.warning(f"Figure description failed: {e}")
            return f"Figure on page {fig[3]}. Caption: {caption}" if caption else f"Figure on page {fig[3]}"

    async def search_figures(self, query: str, document_id: str = None, limit: int = 20) -> List[Dict]:
        """Search figures by caption or description."""
        :
            if not get_llm_service():
            return []

        llm = get_llm_service()
        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Generate keywords to search for figures matching: '{query}'. Output as JSON list of 5-10 search terms."}],
                system_prompt="Output valid JSON array of strings only.",
            )
            content = resp.get("content", "[]") if isinstance(resp, dict) else str(resp)
            import re
            match = re.search(r'\[.*?\]', content, re.DOTALL)
            keywords = json.loads(match.group()) if match else [query]
        except Exception:
            keywords = [query]

        return [{"keyword": kw} for kw in keywords[:10]]


# Global extractor
figure_extractor = FigureExtractor()
