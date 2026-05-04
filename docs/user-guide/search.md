# Smart Search

Search across your library, arXiv, and external sources.

## Local Search

Search within your uploaded documents:

### Simple Search
Quick keyword or phrase search across titles, authors, and abstracts.

```bash
curl "http://localhost:8000/api/search/simple?q=transformer+attention&limit=10"
```

### Advanced Search
Filter by year, author, and title with more precision.

```bash
curl "http://localhost:8000/api/search/advanced?q=machine+learning&year=2024&author=Smith"
```

### Semantic Search
AI-powered concept matching — finds related ideas even with different wording.

```bash
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "efficient attention mechanisms", "limit": 10, "threshold": 0.7}'
```

## arXiv Search

Search millions of open-access papers:

- **Keyword** — Search by topic
- **Author** — Find papers by specific researchers
- **Title** — Search within paper titles
- **Category** — Browse by arXiv category
- **Daily Papers** — Latest pre-prints in your field

## Unified Search

Search everything at once — papers, discussions, glossary, codex, tags:

```bash
curl "http://localhost:8000/api/search-unified?q=transformer&sources=papers,discussions,codex,glossary,tags"
```

The response includes results from all sources merged by relevance.

## Multi-Source Search

Search arXiv, PubMed, CrossRef, and your local library simultaneously:

```bash
curl "http://localhost:8000/api/multi-search?q=attention+mechanism&sources=arxiv,pubmed,crossref,local&limit=5"
```

## Saved Searches

Save frequently used searches:

1. Perform a search
2. Click **Save Search**
3. Name it for easy recall
4. Access saved searches from the side panel

## Search History

Your search history is automatically saved. Access it from the side panel to quickly re-run previous searches.

!!! tip "Search Tips"
    - Use quotes for exact phrase matching: `"attention mechanism"`
    - Results show relevance scores for semantic searches
    - Import arXiv papers directly from search results
    - Save complex searches for literature review workflows
