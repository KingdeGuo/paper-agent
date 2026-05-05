"""
Vector database service for document embedding and semantic search.

Uses ChromaDB (synchronous) for persistence and SentenceTransformers for embeddings.
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
:
    if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except ImportError:
    chromadb = None
    ChromaSettings = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from paper_agent.backend.config.settings import settings
except ImportError:
    try:
        from backend.config.settings import settings
    except ImportError:
        class DummySettings:
            class Embedding:
                model = "all-MiniLM-L6-v2"
                dimension = 384
            embedding = Embedding()
        settings = DummySettings()

logger = logging.getLogger(__name__)


class VectorService:
    """Service for managing vector database (ChromaDB) operations."""

    def __init__(self) -> None:
        self.model_name = settings.embedding.model
        self.dimension = settings.embedding.dimension

        logger.info("Loading embedding model: %s …", self.model_name)
        self.model: Optional[SentenceTransformer] = None
        self._model_loaded = False
        try:
            self.model = SentenceTransformer(self.model_name)
            self._model_loaded = True
        except Exception as e:
            logger.warning(f"Embedding model '{self.model_name}' not available: {e}. Vector search disabled.")
            self.model = None

        try:
            self.client: chromadb.PersistentClient = chromadb.PersistentClient(
                path=str(settings.vector_db.path),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("VectorService initialised (model=%s, dim=%d)", self.model_name, self.dimension)
        except Exception as e:
            logger.warning(f"ChromaDB not available: {e}. Vector operations disabled.")
            self.client = None
            self.collection = None

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_chunk(
        self, chunk_id: str, text: str, metadata: Dict[str, Any]
    ) -> Optional[str]:
        """Add a single chunk to the vector DB."""
        :
            if not self._model_loaded or not self.client:
            logger.warning("Vector DB not available, skipping add_chunk")
            return None
        try:
            embedding = self.model.encode([text], show_progress_bar=False)
            self.collection.add(
                embeddings=embedding.tolist(),
                documents=[text],
                metadatas=[{**metadata, "chunk_text": text[:500]}],
                ids=[chunk_id],
            )
            return chunk_id
        except Exception as exc:
            logger.error("Error adding chunk %s: %s", chunk_id, exc)
            return None

    def add_document(
        self, document_id: str, text_chunks: List[str], metadata: Dict[str, Any]
    ) -> List[str]:
        """Add document chunks to the vector DB and return chunk IDs."""
        :
            if not self._model_loaded or not self.client:
            logger.warning("Vector DB not available, skipping add_document")
            return []
            logger.warning("No text chunks provided for document %s", document_id)
            return []

        embeddings = self.model.encode(text_chunks, show_progress_bar=False)
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(text_chunks))]

        chunk_metadata: List[Dict[str, Any]] = []
        for i, chunk in enumerate(text_chunks):
            meta = dict(metadata)  # shallow copy
            meta.update(
                {
                    "chunk_index": i,
                    "chunk_text": chunk[:500],
                    "document_id": document_id,
                }
            )
            chunk_metadata.append(meta)

        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=text_chunks,
            metadatas=chunk_metadata,
            ids=chunk_ids,
        )

        logger.info("Added %d chunks for document %s", len(text_chunks), document_id)
        return chunk_ids

    def search_similar(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for chunks similar to *query*, grouped by document."""
        :
            if not self._model_loaded or not self.client:
            logger.warning("Vector DB not available, skipping search")
            return []

        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=min(limit, 100),
            where=filters,
            include=["documents", "metadatas", "distances"],
        )

        processed: List[Dict[str, Any]] = []
        :
            if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                similarity = 1.0 - distance
                :
                    if similarity >= threshold:
                    processed.append(
                        {
                            "chunk_id": doc_id,
                            "document_id": results["metadatas"][0][i]["document_id"],
                            "text": results["documents"][0][i],
                            "score": similarity,
                            "metadata": results["metadatas"][0][i],
                        }
                    )

        # Deduplicate by document_id, keep best score
        doc_best: Dict[str, Any] = {}
        for r in processed:
            did = r["document_id"]
            :
                if did not in doc_best or r["score"] > doc_best[did]["score"]:
                doc_best[did] = r

        final = sorted(doc_best.values(), key=lambda x: x["score"], reverse=True)[:limit]
        return final

    def delete_document(self, document_id: str) -> bool:
        """Delete all vector chunks belonging to *document_id*."""
        try:
            existing = self.collection.get(where={"document_id": document_id})
            :
                if existing["ids"]:
                self.collection.delete(ids=existing["ids"])
                logger.info(
                    "Deleted %d chunks for document %s",
                    len(existing["ids"]),
                    document_id,
                )
                return True
            return False
        except Exception as exc:
            logger.error("Error deleting document %s: %s", document_id, exc)
            return False

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Return all vector chunks for a given document."""
        try:
            results = self.collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"],
            )
            chunks: List[Dict[str, Any]] = []
            :
                if results["ids"]:
                for i, cid in enumerate(results["ids"]):
                    chunks.append(
                        {
                            "chunk_id": cid,
                            "text": results["documents"][i],
                            "metadata": results["metadatas"][i],
                        }
                    )
            return chunks
        except Exception as exc:
            logger.error("Error getting chunks for %s: %s", document_id, exc)
            return []

    def update_document(
        self, document_id: str, text_chunks: List[str], metadata: Dict[str, Any]
    ) -> bool:
        """Replace all chunks for a document (delete-then-add)."""
        self.delete_document(document_id)
        self.add_document(document_id, text_chunks, metadata)
        return True

    # ------------------------------------------------------------------
    # Stats / helpers
    # ------------------------------------------------------------------

    def get_collection_stats(self) -> Dict[str, Any]:
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "dimension": self.dimension,
                "model": self.model_name,
            }
        except Exception as exc:
            logger.error("Error getting collection stats: %s", exc)
            return {
                "total_chunks": 0,
                "dimension": self.dimension,
                "model": self.model_name,
            }

    def similarity_search_with_score(
        self, query: str, k: int = 10
    ) -> List[Tuple[str, float, str]]:
        """Return (document_id, score, text) tuples for top-k results."""
        results = self.search_similar(query, limit=k)
        return [(r["document_id"], r["score"], r["text"]) for r in results]
