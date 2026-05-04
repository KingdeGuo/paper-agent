# User Guide

Complete walkthrough of all Paper Agent features.

---

## 📑 Table of Contents

1. [Getting Started](#-getting-started)
2. [Dashboard](#-dashboard)
3. [Document Management](#-document-management)
4. [Smart Search](#-smart-search)
5. [AI Summarization](#-ai-summarization)
6. [Paper Review](#-paper-review)
7. [Knowledge Graph](#-knowledge-graph)
8. [Discovery & Distillation](#-discovery--distillation)
9. [Drafting Bridge](#-drafting-bridge)
10. [Comparative Analysis](#-comparative-analysis)
11. [Notebooks](#-notebooks)
12. [Integrations](#-integrations)

---

## 🚀 Getting Started

### First Login

1. Open the application at `http://localhost:3000`
2. Click **Register** to create an account
3. Fill in your username, email, and password
4. Log in with your credentials

### Dashboard Overview

After logging in, you'll see the Dashboard with:
- **Document Statistics**: Total uploaded, processed, and in-progress documents
- **Processing Status**: Visual breakdown of document processing states
- **System Information**: Current embedding model and LLM provider
- **Trending Documents**: Recently accessed or popular documents

---

## 📁 Document Management

### Uploading Documents

1. Navigate to **Documents** in the sidebar
2. Click **Upload Document**
3. Select a PDF file
4. Optionally add metadata:
   - **Title**: Override the extracted title
   - **Authors**: Comma-separated author names
   - **Year**: Publication year
   - **Keywords**: Comma-separated keywords
5. Click **Upload**

The system will:
- Extract text from the PDF
- Generate embeddings for semantic search
- Queue the document for AI processing

### Managing Documents

- **View**: Click a document to see its details, summary, and PDF
- **Download**: Download the original PDF file
- **Delete**: Remove a document from the system
- **Compare**: Select 2+ documents and click "Compare" for side-by-side analysis
- **Distill**: Select 2+ documents and click "Distill" for contradiction/gap analysis

### Status Indicators

| Status | Meaning |
|--------|---------|
| 🟡 Pending | Uploaded but not yet processed |
| 🔵 Processing | AI is analyzing the document |
| 🟢 Completed | Processing finished successfully |
| 🔴 Failed | Processing encountered an error |

---

## 🔍 Smart Search

### Search Types

**Local Search**: Search within your uploaded documents
- **Simple Search**: Quick keyword or phrase search
- **Advanced Search**: Filter by year, author, and title
- **Semantic Search**: AI-powered concept matching (finds related ideas even with different wording)

**arXiv Search**: Search millions of academic papers
- **Keyword**: Search by topic
- **Author**: Find papers by specific researchers
- **Title**: Search within paper titles
- **Category**: Browse by arXiv category (cs.AI, cs.CV, etc.)
- **Daily Papers**: Latest pre-prints in your field

### Pro Tips
- Use quotes for exact phrase matching: `"attention mechanism"`
- Results include relevance scores for semantic searches
- One-click import arXiv papers into your library

---

## 📝 AI Summarization

### Generating a Summary

On a document detail page:
1. Select a style:
   - **Academic**: Formal, comprehensive analysis
   - **Simple**: Easy-to-understand overview
   - **Detailed**: In-depth breakdown of all sections
2. Click **Generate Summary**
3. View the AI-generated summary

### Thinking Mode

Enable **Thinking Mode** to see the AI's reasoning process:

1. Select the **Thinking Mode** tab
2. The AI shows its step-by-step analysis with `<thought>` tags
3. See how the model processes information before delivering the final answer
4. Ask follow-up questions in the interactive Q&A panel

### Intelligent Q&A

Ask questions about any document:
1. Open a document's Thinking Mode
2. Type your question (e.g., "What methodology did they use?")
3. The AI answers with citations to specific pages and paragraphs
4. Click citations to jump directly to the source

---

## 🔬 Paper Review

### AI-Powered Review

1. Open a document
2. Click **Review Paper**
3. The AI analyzes across multiple dimensions:
   - **Methodology**: Experimental design and approach
   - **Innovation**: Novelty of contributions
   - **Clarity**: Writing quality and presentation
   - **References**: Coverage of related work

4. Get structured feedback:
   - **Overall Score**: 1-10 rating
   - **Strengths**: What the paper does well
   - **Weaknesses**: Areas for improvement
   - **Suggestions**: Actionable recommendations

### Citation Impact Prediction

Predict how influential a paper might become:
- Estimated citation count
- Potential impact factors
- Comparison with similar papers

---

## 🕸️ Knowledge Graph

### Graph Views

**Local View**: Relationships for a single document
- Papers it cites
- Papers that cite it
- Related works by topic

**Global View**: Your entire library as a network
- Citation connections between all papers
- Author collaboration networks
- Topic clusters and research areas

### Interactive Features

- **Drag** nodes to rearrange the graph
- **Scroll** to zoom in/out
- **Click** a node to show document details
- **Click** an edge to see relationship explanation
- **Search** to find specific papers in the graph
- **Export** the graph as SVG

### Edge Types

| Edge Color | Relationship |
|------------|-------------|
| 🟢 Gray | Citation |
| 🔴 Red | Improves upon |
| 🟠 Orange | Contradicts |

---

## 🎯 Discovery & Distillation

### Contradiction Detection

Identify conflicting findings across papers:
1. Select 2+ papers from your library
2. Navigate to **Discovery** → click **Distill**
3. The AI analyzes each paper's claims, results, and methodology
4. Highlights direct contradictions and differences

### Research Gap Analysis

Discover unexplored research opportunities:
1. Select papers in a research area
2. Run **Gap Analysis**
3. The AI identifies:
   - "Semantic voids" between papers
   - Opportunities for methodological hybridization
   - High-impact research hypotheses
4. Save findings to your notebook
5. Start a **Research Thread** for deeper exploration

### Research Threads

Persistent AI research sessions:
- Set a research goal
- The AI explores connections between papers
- Saves conversation history
- Export findings to your notebook

---

## ✍️ Drafting Bridge

### Literature Review Generator

1. Select the papers you want to review
2. Click **Generate Related Work**
3. Choose options:
   - **Context**: Focus area (optional)
   - **Format**: LaTeX output
4. The AI produces a structured `Related Work` section with:
   - Thematic organization of papers
   - Comparative analysis of approaches
   - Citation tracking
5. Copy the LaTeX output directly to your manuscript

### Formula Decoder

1. Paste a mathematical formula
2. The AI explains it in plain language
3. Uses context from your selected papers
4. Get intuition about what the formula means and why it matters

### Grounded Q&A

Chat with your papers:
- Ask specific questions about methodologies, results, or claims
- Every answer includes citations like `[Page 3, Para 2]`
- Click citations to verify sources directly

---

## 📊 Comparative Analysis

Compare 2-3 papers side by side:
1. Go to **Documents**
2. Check the boxes next to 2-3 papers
3. Click **Compare**
4. The AI generates:
   - **Methodology Comparison**: How approaches differ
   - **Results Analysis**: Performance differences
   - **Strengths/Weaknesses**: Per-paper assessment
   - **Synthesis**: Combined insights

---

## 📓 Notebooks

### Creating Notebooks

1. Navigate to **Notebooks**
2. Click **+** to create a new notebook
3. Give it a title and optional description
4. Organize your research by topic or project

### Adding Content

Entries can come from:
- **Discovery Results**: Save contradictions and gaps
- **Manual Notes**: Write your own observations
- **AI Synthesis**: Generate insights from selected papers

### AI Synthesis

1. Select a notebook with entries
2. Click **AI Synthesis**
3. The AI analyzes all entries and generates:
   - Cross-referenced insights
   - Research hypotheses
   - Literature review snippets

---

## 🔌 Integrations

### Zotero

1. Navigate to **Zotero**
2. Enter your Zotero User ID and API Key
3. Click **Connect Library**
4. Browse your Zotero collections
5. Click a collection to see its papers
6. Import papers individually or use **Sync All**

### arXiv

1. Navigate to **Search** → **arXiv Global** tab
2. Search by keyword, author, or category
3. Browse daily papers in your field
4. Click **Import** to add to your library
5. Papers are automatically processed with summaries

---

## ⚙️ Configuration

### Model Selection

In the header, select your preferred LLM model:
- **OpenAI GPT**: General purpose, strong performance
- **Qwen (通义千问)**: Excellent for Chinese-language papers
- **DeepSeek**: Cost-effective option
- **Anthropic Claude**: Strong analytical capabilities
- **Ollama**: Local, private, no API cost
- **HuggingFace**: Fallback open-source models

### Language

Toggle between English and Chinese in the interface. All features support both languages.

### API Keys

For programmatic access:
1. Go to your profile
2. Generate an API key
3. Use it in the `Authorization` header: `Bearer <api-key>`
