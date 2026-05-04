# Paper Agent LaTeX Integration

Use your Paper Agent library directly in Overleaf documents.

## Quick Start

1. **Export your references** from Paper Agent (Documents → select papers → Export BibTeX)
2. **Upload `references.bib`** to your Overleaf project
3. **Add to preamble**: `\usepackage[style=apa]{biblatex}` and `\addbibresource{references.bib}`
4. **Cite**: `\cite{key}` or `\parencite{key}`
5. **Print**: `\printbibliography`

## Using the LaTeX Package

For enhanced integration, upload `paperagent.sty` to your Overleaf project:

```latex
\documentclass{article}
\usepackage{paperagent}

\begin{document}
\section*{Related Work}
Recent work by \pacite{Smith2024} shows...
\pabibliography
\end{document}
```

## API Integration

You can also fetch your bibliography programmatically:

```bash
# Get all references as .bib
curl "http://localhost:8000/api/overleaf/bib?document_ids=id1,id2,id3"

# Get a complete Overleaf-ready export
curl -X POST "http://localhost:8000/api/overleaf/export-for-overleaf" \
  -H "Content-Type: application/json" \
  -d '{"document_ids": ["id1", "id2"], "style": "apa"}'
```

## Features

- One-click .bib file generation
- Multiple citation styles (APA, MLA, Chicago, IEEE)
- Complete LaTeX document generation
- Custom LaTeX package for Paper Agent integration
- Citation key management
