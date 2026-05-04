# Frequently Asked Questions

## General

### What is Paper Agent?
Paper Agent is an open-source AI Research Companion that helps researchers manage, analyze, and synthesize academic literature. It goes beyond PDF management with AI-powered analysis, knowledge graphs, team collaboration, and MCP integration.

### Is Paper Agent free?
Yes! Paper Agent is completely free and open-source under the MIT License. You self-host it on your own infrastructure.

### How is this different from Zotero, Mendeley, or Paperpile?
Traditional tools focus on **reference management**. Paper Agent focuses on the **entire research lifecycle**:

| Feature | Paper Agent | Zotero | Mendeley | Paperpile |
|---------|------------|--------|----------|-----------|
| PDF Management | ✅ | ✅ | ✅ | ✅ |
| AI Summaries | ✅ | ❌ | ❌ | ❌ |
| Knowledge Graph | ✅ | ❌ | ❌ | ❌ |
| Research Gap Analysis | ✅ | ❌ | ❌ | ❌ |
| Literature Review Gen | ✅ | ❌ | ❌ | ❌ |
| Team Workspaces | ✅ | ✅ | ✅ | ❌ |
| MCP Protocol | ✅ | ❌ | ❌ | ❌ |
| Self-Hosted | ✅ | ❌ | ❌ | ❌ |
| Open Source | ✅ | ✅ | ❌ | ❌ |

## Setup & Installation

### What are the system requirements?
- **Development**: 2 CPU cores, 4GB RAM, 10GB disk
- **Production**: 4 CPU cores, 8GB RAM, 50GB+ disk
- **Software**: Python 3.10+, Node.js 18+, Docker (optional)

### Can I use SQLite in production?
SQLite is fine for personal use or small teams. For production, PostgreSQL is recommended for better concurrency and reliability.

### Do I need a GPU?
No. All AI features work with CPU. GPU acceleration is used only if you run local models via Ollama or HuggingFace.

## AI Features

### Which LLM providers are supported?
OpenAI, Qwen (通义千问), DeepSeek, Anthropic Claude, Ollama (local), and HuggingFace Transformers.

### Do I need an API key?
For cloud providers (OpenAI, Qwen, DeepSeek, Claude), yes. For local models (Ollama, HuggingFace), no — but you need sufficient hardware.

### Are my documents sent to external APIs?
Only when you use cloud LLM providers. With Ollama or HuggingFace, everything stays local.

## MCP Integration

### What is MCP?
Model Context Protocol — an open standard that lets AI assistants (Claude, Copilot, etc.) directly interact with your Paper Agent library.

### Which MCP clients are supported?
Claude Desktop, VS Code (GitHub Copilot), Cursor, Claude Code, and any MCP-compatible application.

## Troubleshooting

### Upload fails
Check file size (max 50MB), ensure it's a valid PDF, and verify the backend is running.

### Search returns no results
Try different keywords. If using semantic search, ensure documents have been processed (status = Completed).

### Docker build fails
Ensure `requirements.txt` exists at the project root. Try `docker-compose build --no-cache`.

### More help
Open a [GitHub Issue](https://github.com/KingdeGuo/paper-agent/issues).
