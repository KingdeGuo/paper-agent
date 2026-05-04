# Paper Agent MCP Integration

Connect your research library to AI assistants via the **Model Context Protocol (MCP)**.

## What is MCP?

MCP is an open standard that lets AI assistants (Claude, GPT, Copilot, etc.) directly interact with your tools and data. With this MCP server, any MCP-compatible AI can search your papers, get summaries, manage your reading list, and more — all through natural conversation.

## Quick Start

```bash
# Install MCP SDK
pip install mcp

# Start the MCP server
python mcp/server.py
```

## Client Configuration

### Claude Desktop

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "paper-agent": {
      "command": "python",
      "args": ["/path/to/paper-agent/mcp/server.py"]
    }
  }
}
```

### VS Code (GitHub Copilot)

Add to `.vscode/mcp.json`:
```json
{
  "servers": {
    "paper-agent": {
      "type": "stdio",
      "command": "python",
      "args": ["/path/to/paper-agent/mcp/server.py"]
    }
  }
}
```

### Cursor

Add to `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "paper-agent": {
      "command": "python",
      "args": ["/path/to/paper-agent/mcp/server.py"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add paper-agent -- python /path/to/paper-agent/mcp/server.py
```

## Available Tools

| Tool | Description |
|------|-------------|
| `search_papers` | Search your library by keyword, title, or author |
| `get_paper` | Get detailed info about a specific paper |
| `get_paper_summary` | Get AI-generated summary |
| `find_related_papers` | Find semantically similar papers |
| `get_library_stats` | Get library statistics |
| `ask_library` | Ask natural language questions about your library |
| `export_citation` | Export BibTeX or formatted citation |
| `manage_reading_list` | Set reading status (to_read/reading/read) |
| `get_reading_list` | Get your reading list |
| `search_arxiv` | Search and import from arXiv |
| `get_paper_annotations` | Get highlights and notes |
| `generate_research_digest` | Generate AI research digest |
| `analyze_citation_network` | Analyze citation relationships |

## Available Resources

| Resource | Description |
|----------|-------------|
| `paper:///<id>` | Full paper details in markdown |
| `library:///overview` | Library overview |

## Available Prompts

| Prompt | Description |
|--------|-------------|
| `analyze_paper` | Deep analysis of a paper |
| `literature_review` | Generate literature review section |
| `compare_papers` | Compare multiple papers |
| `research_idea` | Generate novel research ideas |

## Example Workflows

### "Find papers about transformers"
> AI calls `search_papers(query="transformer attention mechanism")`

### "Summarize the latest paper I saved"
> AI calls `get_reading_list(status="reading")` then `get_paper_summary(paper_id=...)`

### "Find related work for paper X"
> AI calls `get_paper(paper_id=X)` then `find_related_papers(paper_id=X)`

### "Export my reading list as BibTeX"
> AI calls `get_reading_list()` then `export_citation()` for each paper

### "What are the research trends in my library?"
> AI calls `analyze_citation_network()` then `generate_research_digest()`
