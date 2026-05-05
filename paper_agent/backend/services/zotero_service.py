"""
Zotero integration service for Paper Agent.

Provides:
- Connect to Zotero API
- Fetch collections and items
- Import PDFs and metadata from Zotero to Paper Agent
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

ZOTERO_API_BASE = "https://api.zotero.org"

class ZoteroService:
    """Service for interacting with Zotero API."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_collections(self, user_id: str, api_key: str) -> List[Dict[str, Any]]:
        """Fetch all collections for a user."""
        url = f"{ZOTERO_API_BASE}/users/{user_id}/collections"
        headers = {"Zotero-API-Key": api_key}

        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch Zotero collections: {e}")
            return []

    async def get_items(self, user_id: str, api_key: str, collection_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch items (papers) from Zotero."""
        url = f"{ZOTERO_API_BASE}/users/{user_id}/items"
        if collection_id:
            url = f"{ZOTERO_API_BASE}/users/{user_id}/collections/{collection_id}/items"

        headers = {"Zotero-API-Key": api_key}
        params = {"format": "json", "itemType": "-attachment || attachment", "limit": 50}

        try:
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch Zotero items: {e}")
            return []

    async def download_attachment(self, user_id: str, api_key: str, item_key: str) -> Optional[bytes]:
        """Download a PDF attachment from Zotero."""
        url = f"{ZOTERO_API_BASE}/users/{user_id}/items/{item_key}/file"
        headers = {"Zotero-API-Key": api_key}

        try:
            response = await self.client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to download Zotero attachment {item_key}: {e}")
            return None

    async def import_item(self, local_user_id: str, zotero_user_id: str, api_key: str, item_key: str, db: Any) -> Optional[Any]:
        """Import a specific Zotero item."""
        # 1. Fetch item data
        url = f"{ZOTERO_API_BASE}/users/{zotero_user_id}/items/{item_key}"
        headers = {"Zotero-API-Key": api_key}

        try:
            response = await self.client.get(url, headers=headers)
            item_data = response.json()

            # 2. Extract metadata
            data = item_data.get('data', {})
            title = data.get('title', 'Unknown Title')
            creators = data.get('creators', [])
            authors = [f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() for c in creators]

            # 3. Create document record
            doc_data = {
                "title": title,
                "authors": authors,
                "filename": f"zotero_{item_key}.pdf",
                "user_id": local_user_id,
                "processed": 0,
                "doc_metadata": {"zotero_key": item_key, "source": "zotero"}
            }

            doc = await db.create_document(doc_data)

            # 4. Trigger background task to fetch PDF if available
            # (In a real system, we'd find the child attachment of type 'pdf')

            return doc
        except Exception as e:
            logger.error(f"Failed to import Zotero item {item_key}: {e}")
            return None

# Global Zotero service instance
zotero_service = ZoteroService()
