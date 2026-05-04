# Document Management

Upload, organize, and manage your academic paper library.

## Uploading Papers

### Upload a PDF

1. Navigate to **Documents**
2. Click **Upload Document**
3. Select a `.pdf` file
4. Optionally add metadata:
   - **Title** — Override the extracted title
   - **Authors** — Comma-separated names
   - **Year** — Publication year
   - **Keywords** — Comma-separated tags
5. Click **Upload**

### Import from arXiv

1. Go to **Search** → **arXiv Global** tab
2. Search by keyword, author, or category
3. Click the import button next to any result
4. The paper is automatically downloaded and processed

### Import from URL

```bash
curl -X POST http://localhost:8000/api/import/urls \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://arxiv.org/abs/1706.03762"]}'
```

### Import BibTeX

Go to **Citations** → **Import BibTeX** tab and paste your BibTeX content.

## Managing Documents

### Document Table

The documents page shows a table with:
- **Checkbox** — Select for batch operations
- **Filename** — Original file name
- **Title** — Paper title (may be auto-extracted)
- **Authors** — First 2 authors shown
- **Year** — Publication year
- **Status** — Processing status (Pending/Processing/Completed/Failed)

### Batch Operations

Select multiple papers to:
- **Compare** — Deep comparison analysis
- **Distill** — Contradiction detection and gap analysis
- **Export BibTeX** — Export selected as references

### Processing Status

| Status | Meaning |
|--------|---------|
| 🟡 Pending | Uploaded but not processed |
| 🔵 Processing | AI is analyzing the text |
| 🟢 Completed | Processing finished |
| 🔴 Failed | Error during processing |

## Document Detail View

Click any document to see:

- **Metadata** — Title, authors, year, keywords
- **AI Summary** — Generated with configurable style
- **Paper Review** — Multi-dimensional AI evaluation
- **Reading Status** — Mark as to-read/reading/read
- **PDF Viewer** — In-browser PDF reader with annotations
- **Thinking Mode** — See AI's reasoning process
- **Related Papers** — Semantically similar papers
- **Citation Export** — Copy BibTeX, share link
- **Scholar Perspectives** — Community discussions
- **Flashcards** — Generate and review flashcards

!!! tip "Keyboard Shortcuts"
    In the PDF viewer: `Left/Right` arrows change pages, `Ctrl+F` searches within the PDF.
