import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
import numpy as np

from backend.config.settings import settings

logger = logging.getLogger(__name__)

class VectorService:
    """Service for managing vector database operations."""
    
    def __init__(self):
        self.model = SentenceTransformer(settings.embedding.model)
        self.dimension = settings.embedding.dimension
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=settings.vector_db.path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_document(self, document_id: str, text_chunks: List[str], metadata: Dict[str, Any]) -> List[str]:
        """Add document chunks to vector database."""
        if not text_chunks:
            logger.warning(f"No text chunks to add for document {document_id}")
            return []
        
        # Generate embeddings
        embeddings = self.model.encode(text_chunks)
        
        # Generate unique IDs for each chunk
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(text_chunks))]
        
        # Prepare metadata for each chunk
        chunk_metadata = []
        for i, chunk in enumerate(text_chunks):
            meta = metadata.copy()
            meta.update({
                "chunk_index": i,
                "chunk_text": chunk[:500],  # Store first 500 chars for preview
                "document_id": document_id
            })
            chunk_metadata.append(meta)
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=text_chunks,
            metadatas=chunk_metadata,
            ids=chunk_ids
        )
        
        logger.info(f"Added {len(text_chunks)} chunks for document {document_id}")
        return chunk_ids
    
    def search_similar(self, query: str, limit: int = 10, threshold: float = 0.7, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        # Generate query embedding
        query_embedding = self.model.encode([query])
        
        # Build where clause for filters
        where_clause = None
        if filters:
            where_clause = filters
        
        # Search in collection
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=min(limit, 100),
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        # Process results
        processed_results = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i]
                similarity = 1 - distance  # Convert distance to similarity
                
                if similarity >= threshold:
                    result = {
                        'chunk_id': doc_id,
                        'document_id': results['metadatas'][0][i]['document_id'],
                        'text': results['documents'][0][i],
                        'score': similarity,
                        'metadata': results['metadatas'][0][i]
                    }
                    processed_results.append(result)
        
        # Group by document and get best score
        document_scores = {}
        for result in processed_results:
            doc_id = result['document_id']
            if doc_id not in document_scores or result['score'] > document_scores[doc_id]['score']:
                document_scores[doc_id] = result
        
        # Sort by score and return top results
        final_results = sorted(document_scores.values(), key=lambda x: x['score'], reverse=True)[:limit]
        
        return final_results
    
    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document."""
        try:
            # Find all chunks for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document."""
        try:
            results = self.collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"]
            )
            
            chunks = []
            if results['ids']:
                for i, doc_id in enumerate(results['ids']):
                    chunk = {
                        'chunk_id': doc_id,
                        'text': results['documents'][i],
                        'metadata': results['metadatas'][i]
                    }
                    chunks.append(chunk)
            
            return chunks
        except Exception as e:
            logger.error(f"Error getting chunks for document {document_id}: {str(e)}")
            return []
    
    def update_document(self, document_id: str, text_chunks: List[str], metadata: Dict[str, Any]) -> bool:
        """Update document chunks in vector database."""
        # Delete existing chunks
        self.delete_document(document_id)
        
        # Add new chunks
        self.add_document(document_id, text_chunks, metadata)
        
        return True
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            count = self.collection.count()
            return {
                'total_chunks': count,
                'dimension': self.dimension,
                'model': settings.embedding.model
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {'total_chunks': 0, 'dimension': self.dimension, 'model': settings.embedding.model}
    
    def similarity_search_with_score(self, query: str, k: int = 10) -> List[Tuple[str, float, str]]:
        """Perform similarity search and return (document_id, score, text) tuples."""
        results = self.search_similar(query, limit=k)
        
        return [(r['document_id'], r['score'], r['text']) for r in results]
