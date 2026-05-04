# MCP Integration

Connect any MCP-compatible AI assistant to your research library.

## What is MCP?

**MCP (Model Context Protocol)** is an open standard that lets AI assistants (Claude, GPT, Copilot) directly interact with your tools and data. Paper Agent's MCP server exposes 19 tools, 4 prompts, and dynamic resources.

## Quick Start

```bash
pip install mcp
python mcp/server.py
```

## Client Configuration

=== "Claude Desktop"
    ```json title="claude_desktop_config.json"
    {
      "mcpServers": {
        "paper-agent": {
          "command": "python",
          "args": ["/path/to/mcp/server.py"]
        }
      }
    }
    ```

=== "VS Code"
    ```json title=".vscode/mcp.json"
    {
      "servers": {
        "paper-agent": {
          "type": "stdio",
          "command": "python",
          "args": ["${workspaceFolder}/mcp/server.py"]
        }
      }
    }
    ```

=== "Cursor"
    ```json title="~/.cursor/mcp.json"
    {
      "mcpServers": {
        "paper-agent": {
          "command": "python",
          "args": ["/path/to/mcp/server.py"]
        }
      }
    }
    ```

=== "Claude Code"
    ```bash
    claude mcp add paper-agent -- python /path/to/mcp/server.py
    ```

## Available Tools (19)

| Tool | Description |
|------|-------------|
| `search_papers` | Search your library by keyword |
| `get_paper` | Get detailed paper info |
| `get_paper_summary` | Get AI-generated summary |
| `find_related_papers` | Find semantically similar papers |
| `get_library_stats` | Get library statistics |
| `ask_library` | Ask natural language questions |
| `export_citation` | Export BibTeX/formatted citation |
| `manage_reading_list` | Set reading status |
| `get_reading_list` | Get reading queue |
| `search_arxiv` | Search and import from arXiv |
| `get_paper_annotations` | Get highlights and notes |
| `generate_research_digest` | Generate AI research digest |
| `analyze_citation_network` | Analyze citation relationships |
| `manage_alerts` | Create/list/check alerts |
| `manage_projects` | Organize papers into projects |
| `get_glossary` | Get extracted key terms |
| `manage_collections` | Create curated collections |
| `analyze_timeline` | Get research timeline data |

## Example Workflows

### "Find papers about transformers"
```
AI → search_papers(query="transformer attention mechanism")
```

### "What should I read today?"
```
AI → get_reading_list(status="to_read")
   → get_library_stats()
   → generate_research_digest()
```

### "Summarize and export my reading list"
```
AI → get_reading_list(status="reading")
   → get_paper_summary(paper_id=...)
   → export_citation(paper_id=..., style="bibtex")
```
