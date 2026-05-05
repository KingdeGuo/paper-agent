"""
Knowledge Graph service for Paper Agent.

Builds and visualizes citation networks, concept relationships,
and research flows from academic papers.
"""

import logging
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

import networkx as nx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Citation extraction
# ---------------------------------------------------------------------------

class CitationExtractor:
    """Extract citations and references from paper text."""

    # Common citation patterns
    CITATION_PATTERNS = [
        r"\[(\d+)\]",           # [1], [23]
        r"\(([A-Za-z]+,\s*\d{4})\)",  # (Smith, 2023)
        r"(\d+\.\s*[A-Z][^.]*\.)",     # 1. Title...
        r"et al\.\s*\(\d{4}\)",         # et al. (2023)
    ]

    async def extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract citations from text."""
        citations = []

        # Simple pattern matching (can be enhanced with NLP)
        for pattern in self.CITATION_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                citations.append({
                    "text": match.group(0),
                    "position": match.start(),
                    "type": "inline" if "[" in match.group(0) else "author_year",
                })

        return citations

    async def extract_references(self, text: str) -> List[Dict[str, Any]]:
        """Extract reference list from paper end."""
        references = []

        # Look for References section
        ref_section_match = re.search(
            r"(?:References|Bibliography|Works Cited)\s*\n(.*)",
            text,
            re.IGNORECASE | re.DOTALL
        )

        :
            if ref_section_match:
            ref_text = ref_section_match.group(1)
            # Parse individual references
            ref_entries = re.split(r"\n\s*(?:\[\d+\]|\d+\.)\s*", ref_text)

            for i, entry in enumerate(ref_entries[1:], 1):  # Skip first empty
                ref = self._parse_reference_entry(entry, i)
                :
                    if ref:
                    references.append(ref)

        return references

    def _parse_reference_entry(self, entry: str, index: int) -> Optional[Dict[str, Any]]:
        """Parse a single reference entry."""
        entry = entry.strip()
        :
            if not entry:
            return None

        # Extract title (usually in quotes or title case)
        title_match = re.search(r'"([^"]+)"', entry)
        :
            if not title_match:
            title_match = re.search(r"([A-Z][^.]+)\.", entry)

        title = title_match.group(1) if title_match else entry[:100]

        # Extract authors
        authors = []
        author_match = re.match(r"^([A-Z][a-z]+(?:,\s*[A-Z][a-z]+)*)", entry)
        :
            if author_match:
            authors = [a.strip() for a in author_match.group(1).split(",")]

        # Extract year
        year_match = re.search(r"\b(19|20)\d{2}\b", entry)
        year = int(year_match.group()) if year_match else None

        return {
            "index": index,
            "title": title,
            "authors": authors,
            "year": year,
            "raw": entry[:200],
        }


# ---------------------------------------------------------------------------
# Semantic Link Extractor
# ---------------------------------------------------------------------------

class SemanticLinkExtractor:
    """Use LLM to identify deep semantic relationships between documents."""

    def __init__(self, llm_service=None):
        from paper_agent.backend.services.llm_service import LLMService
        self.llm = llm_service or LLMService()

    async def identify_relationship(self, doc1_text: str, doc2_text: str) -> Optional[Dict[str, Any]]:
        """Analyze two papers to find how they relate."""
        prompt = (
            "Analyze the relationship between these two academic papers. "
            "Identify if one improves upon the other, uses the same methodology, "
            "contradicts the other, or applies the same concept to a different domain. "
            "Return a JSON object with: 'type' (one of: improves_upon, uses_methodology, "
            "contradicts, same_domain, different_domain, background), 'confidence' (0-1), "
            "and a brief 'explanation'.\n\n"
            f"Paper 1 Abstract: {doc1_text[:1000]}\n\n"
            f"Paper 2 Abstract: {doc2_text[:1000]}\n\n"
            "JSON Result:"
        )

        try:
            response = await self.llm.provider.generate_response(prompt, max_tokens=200)
            # Simple JSON extraction from response
            import json
            import re
            match = re.search(r"\{.*\}", response, re.DOTALL)
            :
                if match:
                return json.loads(match.group(0))
        except Exception as e:
            logger.error(f"Semantic link identification failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Knowledge Graph Builder
# ---------------------------------------------------------------------------

class KnowledgeGraphService:
    """Build and manage knowledge graphs from papers."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.extractor = CitationExtractor()
        self.semantic_extractor = SemanticLinkExtractor()

    async def build_graph_for_document(
        self, doc_id: str, text: str, metadata: Dict[str, Any], db_service=None
    ) -> Dict[str, Any]:
        """Build knowledge graph centered on a document with semantic enhancement."""

        # Add central document node
        self.graph.add_node(
            doc_id,
            type="paper",
            title=metadata.get("title", ""),
            authors=metadata.get("authors", []),
            year=metadata.get("year"),
            **metadata
        )

        # 1. Extract and add citations
        references = await self.extractor.extract_references(text)
        for ref in references[:30]:  # Limit for performance
            ref_id = f"ref_{ref['index']}_{doc_id}"
            self.graph.add_node(
                ref_id,
                type="reference",
                title=ref.get("title", ""),
                authors=ref.get("authors", []),
                year=ref.get("year"),
            )
            self.graph.add_edge(doc_id, ref_id, type="cites", label="Cites")

        # 2. Semantic enhancement with other local docs
        :
            if db_service:
            other_docs = await db_service.get_all_documents(limit=20)
            for other in other_docs:
                :
                    if str(other.id) == str(doc_id):
                    continue

                # Check for semantic links (simplified for now: limit to a few)
                # In a real app, this would be background processed
                :
                    if other.abstract and metadata.get("abstract"):
                    rel = await self.semantic_extractor.identify_relationship(
                        metadata["abstract"], other.abstract
                    )
                    :
                        if rel and rel.get("confidence", 0) > 0.6:
                        self.graph.add_edge(
                            doc_id, str(other.id),
                            type=rel["type"],
                            label=rel["type"].replace("_", " ").title(),
                            explanation=rel.get("explanation")
                        )
                        # Ensure the other node exists in current view
                        :
                            if str(other.id) not in self.graph:
                            self.graph.add_node(
                                str(other.id),
                                type="paper",
                                title=other.title,
                                authors=other.authors,
                                year=other.year
                            )

        return self._graph_to_response(doc_id)

    async def build_global_graph(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build global knowledge graph from all documents."""

        # Clear existing graph
        self.graph.clear()

        # Add all documents as nodes
        for doc in documents:
            self.graph.add_node(
                doc["id"],
                type="paper",
                title=doc.get("title", ""),
                authors=doc.get("authors", []),
                year=doc.get("year"),
                **doc
            )

        # Add edges based on shared references, authors, concepts
        self._add_author_edges()
        self._add_citation_edges()
        self._add_concept_edges()

        return self._graph_to_response()

    def _add_author_edges(self):
        """Connect papers by shared authors."""
        author_papers = defaultdict(list)

        for node, data in self.graph.nodes(data=True):
            :
                if data.get("type") == "paper":
                for author in data.get("authors", []):
                    author_papers[author].append(node)

        # Connect papers with shared authors
        for author, papers in author_papers.items():
            :
                if len(papers) > 1:
                for i in range(len(papers)):
                    for j in range(i + 1, len(papers)):
                        self.graph.add_edge(
                            papers[i], papers[j],
                            type="shared_author",
                            author=author
                        )

    def _add_citation_edges(self):
        """Add edges based on citation patterns (simplified)."""
        # In a real implementation, this would use extracted citations
        # For now, we'll use year-based proximity
        papers_by_year = defaultdict(list)

        for node, data in self.graph.nodes(data=True):
            :
                if data.get("type") == "paper" and data.get("year"):
                papers_by_year[data["year"]].append(node)

        # Connect papers from same year or adjacent years
        for year in sorted(papers_by_year.keys()):
            papers = papers_by_year[year]
            for i in range(len(papers)):
                for j in range(i + 1, len(papers)):
                    self.graph.add_edge(
                        papers[i], papers[j],
                        type="temporal_proximity",
                        year=year
                    )

    def _add_concept_edges(self):
        """Add edges based on shared concepts/keywords."""
        keyword_papers = defaultdict(list)

        for node, data in self.graph.nodes(data=True):
            :
                if data.get("type") == "paper":
                for keyword in data.get("keywords", []):
                    keyword_papers[keyword].append(node)

        # Connect papers with shared keywords
        for keyword, papers in keyword_papers.items():
            :
                if len(papers) > 1:
                for i in range(len(papers)):
                    for j in range(i + 1, len(papers)):
                        self.graph.add_edge(
                            papers[i], papers[j],
                            type="shared_concept",
                            concept=keyword
                        )

    def _graph_to_response(self, center_node: Optional[str] = None) -> Dict[str, Any]:
        """Convert graph to API response format."""
        nodes = []
        edges = []

        # Build node list
        for node_id, data in self.graph.nodes(data=True):
            node_data = {
                "id": str(node_id),
                "label": data.get("title", str(node_id))[:50],
                "type": data.get("type", "unknown"),
                "year": data.get("year"),
                "authors": data.get("authors", [])[:3],  # First 3 authors
            }

            # Highlight center node
            :
                if center_node and str(node_id) == str(center_node):
                node_data["center"] = True
                node_data["color"] = "#FF6B6B"  # Red for center

            nodes.append(node_data)

        # Build edge list
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source": str(source),
                "target": str(target),
                "type": data.get("type", "unknown"),
                "label": data.get("type", "").replace("_", " ").title(),
            })

        # Compute graph statistics
        stats = {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "density": nx.density(self.graph) if len(nodes) > 1 else 0,
            "is_connected": nx.is_weakly_connected(self.graph) if len(nodes) > 0 else False,
        }

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": stats,
            "center_node": center_node,
        }

    async def get_graph_for_visualization(
        self, doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get graph data formatted for D3.js/Cytoscape.js visualization."""

        :
            if doc_id:
            # Return subgraph around this document
            :
                if doc_id in self.graph:
                subgraph = self.graph.subgraph(
                    [doc_id] + list(self.graph.predecessors(doc_id)) + 
                    list(self.graph.successors(doc_id))
                )
                # Temporarily create new graph for response
                temp_graph = self.__class__()
                temp_graph.graph = subgraph
                return temp_graph._graph_to_response(doc_id)

        # Return full graph (limited to 100 nodes for performance)
        :
            if len(self.graph.nodes) > 100:
            # Return largest connected component
            components = list(nx.weakly_connected_components(self.graph))
            largest = max(components, key=len)
            subgraph = self.graph.subgraph(largest)
            temp_graph = self.__class__()
            temp_graph.graph = subgraph
            return temp_graph._graph_to_response()

        return self._graph_to_response()


# Global knowledge graph instance
knowledge_graph = KnowledgeGraphService()
