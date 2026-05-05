import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import io

import pdfplumber
import PyPDF2
from PIL import Image

try:
    from paper_agent.backend.config.settings import settings
    from paper_agent.backend.models.document import DocumentCreate
except ImportError:
    try:
        from backend.config.settings import settings
        from backend.models.document import DocumentCreate
    except ImportError:
        # Fallback - create minimal settings
        class DummySettings:
            class Storage:
                pdf_path = "./data/pdfs"
                max_file_size = "50MB"
                allowed_extensions = [".pdf"]
            storage = Storage()
        settings = DummySettings()
        DocumentCreate = None

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Service for processing PDF documents."""

    def __init__(self):
        self.storage_path = Path(settings.storage.pdf_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.max_file_size = self._parse_file_size(settings.storage.max_file_size)
        self.allowed_extensions = settings.storage.allowed_extensions

    def _parse_file_size(self, size_str: str) -> int:
        """Parse file size string to bytes."""
        size_str = size_str.upper()
        if size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def validate_file(self, filename: str, file_size: int) -> bool:
        """Validate file extension and size."""
        file_extension = Path(filename).suffix.lower()

        if file_extension not in self.allowed_extensions:
            raise ValueError(f"Unsupported file type: {file_extension}")

        if file_size > self.max_file_size:
            raise ValueError(f"File too large: {file_size} > {self.max_file_size}")

        return True

    def save_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file to storage."""
        file_id = str(uuid.uuid4())
        file_path = self.storage_path / f"{file_id}_{filename}"

        with open(file_path, 'wb') as f:
            f.write(file_content)

        return str(file_path)

    def extract_metadata(self, file_path: str) -> Dict[str, any]:
        """Extract metadata from PDF file."""
        metadata = {
            'title': None,
            'authors': [],
            'year': None,
            'abstract': None,
            'keywords': [],
            'num_pages': 0,
            'file_size': os.path.getsize(file_path)
        }

        try:
            # Extract basic PDF metadata
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata['num_pages'] = len(pdf_reader.pages)

                # Extract PDF metadata
                if pdf_reader.metadata:
                    pdf_meta = pdf_reader.metadata
                    metadata['title'] = pdf_meta.get('/Title', None)
                    if metadata['title'] and len(metadata['title'].strip()) < 5:
                        metadata['title'] = None

            # Extract text for additional processing
            text_content = self.extract_text(file_path)
            if text_content:
                # Try to extract title from first page
                if not metadata['title']:
                    metadata['title'] = self._extract_title_from_text(text_content[:1000])

                # Try to extract year from text
                if not metadata['year']:
                    metadata['year'] = self._extract_year_from_text(text_content)

                # Try to extract abstract
                abstract = self._extract_abstract_from_text(text_content)
                if abstract:
                    metadata['abstract'] = abstract

        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")

        return metadata

    def extract_text(self, file_path: str) -> str:
        """Extract text content from PDF."""
        text = ""

        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages[:settings.pdf_processing.max_pages]:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")

        return text

    def extract_images(self, file_path: str) -> List[Image.Image]:
        """Extract images from PDF (if enabled)."""
        if not settings.pdf_processing.extract_images:
            return []

        images = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    for img in page.images:
                        try:
                            # Extract image data
                            image_data = img['stream'].get_data()
                            image = Image.open(io.BytesIO(image_data))
                            images.append(image)
                        except Exception as e:
                            logger.warning(f"Error extracting image: {str(e)}")
        except Exception as e:
            logger.error(f"Error extracting images from {file_path}: {str(e)}")

        return images

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for vector processing."""
        chunk_size = settings.pdf_processing.chunk_size
        chunk_overlap = settings.pdf_processing.chunk_overlap

        if not text:
            return []

        # Simple chunking by sentences
        sentences = text.replace('\n', ' ').split('. ')
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) + 2 <= chunk_size:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk + ".")

                # Handle very long sentences
                if len(sentence) > chunk_size:
                    # Split by words
                    words = sentence.split()
                    temp_chunk = ""
                    for word in words:
                        if len(temp_chunk) + len(word) + 1 <= chunk_size:
                            temp_chunk += " " + word
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = word
                    if temp_chunk:
                        current_chunk = temp_chunk.strip()
                else:
                    current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk + ".")

        return chunks

    def _extract_title_from_text(self, text: str) -> Optional[str]:
        """Extract title from text content."""
        lines = text.strip().split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                return line
        return None

    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """Extract year from text content."""
        import re

        # Look for 4-digit years between 1900-2030
        year_pattern = r'\b(19\d{2}|20[0-3]\d)\b'
        years = re.findall(year_pattern, text)

        if years:
            # Return the most recent year
            return max(int(year) for year in years)

        return None

    def _extract_abstract_from_text(self, text: str) -> Optional[str]:
        """Extract abstract from text content."""
        text_lower = text.lower()

        # Look for abstract section
        abstract_patterns = [
            'abstract',
            'summary',
            'resumen',
            'résumé'
        ]

        for pattern in abstract_patterns:
            idx = text_lower.find(pattern)
            if idx != -1:
                # Extract text after abstract keyword
                abstract_start = idx + len(pattern)
                abstract_text = text[abstract_start:abstract_start+1000]

                # Clean up the abstract
                lines = abstract_text.split('\n')
                abstract = ""
                for line in lines:
                    line = line.strip()
                    if line and not line.lower().startswith('keywords'):
                        abstract += line + " "
                    if len(abstract) > 500:
                        break

                return abstract.strip()

        return None

    def process_document(self, file_content: bytes, filename: str) -> Tuple[DocumentCreate, str]:
        """Process uploaded document."""
        # Validate file
        self.validate_file(filename, len(file_content))

        # Save file
        file_path = self.save_file(file_content, filename)

        # Extract metadata
        metadata = self.extract_metadata(file_path)

        # Create document record
        document = DocumentCreate(
            filename=filename,
            title=metadata.get('title'),
            authors=metadata.get('authors', []),
            year=metadata.get('year'),
            abstract=metadata.get('abstract'),
            keywords=metadata.get('keywords', []),
            file_path=file_path,
            file_size=metadata.get('file_size', 0)
        )

        return document, self.extract_text(file_path)
