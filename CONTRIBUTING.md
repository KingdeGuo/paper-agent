# Contributing to Paper Agent

We love contributions! Here's how to get involved.

---

## 🌟 Ways to Contribute

| Type | Description |
|------|-------------|
| 🐛 **Bug Reports** | Open an issue with steps to reproduce |
| 💡 **Feature Ideas** | Open an issue with use case description |
| 💻 **Code** | Submit a pull request (see below) |
| 📖 **Docs** | Improve documentation, fix typos |
| 🌐 **Translations** | Add or improve i18n translations |
| 🧪 **Testing** | Write tests, improve coverage |

---

## 🛠️ Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optional, for integration tests)

### Backend

```bash
# Clone the repo
git clone https://github.com/KingdeGuo/paper-agent.git
cd paper-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the project in development mode
pip install -e ".[dev]"

# Start the backend
python -m paper_agent.backend.main
```

### Frontend

```bash
cd paper_agent/frontend

# Install dependencies
npm install

# Start dev server
npm start
```

The backend runs on `localhost:8000` and frontend on `localhost:3000`.

---

## 📋 Code Guidelines

### Python

- **Format**: We use [Ruff](https://docs.astral.sh/ruff/) for formatting and linting
  ```bash
  ruff check paper_agent/backend/
  ```
- **Type hints**: All function signatures must include type annotations
- **Async**: Use `async/await` for I/O operations; keep CPU-bound work synchronous
- **Imports**: Order: stdlib → third-party → local (Ruff handles this automatically)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes

### JavaScript/React

- **Format**: ESLint + Prettier (configured in the frontend project)
- **Components**: Functional components with hooks, no class components
- **State**: React Context for global state, local state for component-specific data
- **i18n**: All user-facing strings must use `useTranslation()` and `t()` function
- **Naming**: `PascalCase` for components, `camelCase` for functions/variables

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Zotero batch import
fix: resolve PDF text extraction for scanned documents
docs: update API reference for search endpoints
refactor: simplify LLM provider fallback logic
test: add unit tests for auth service
i18n: add Chinese translations for discovery page
```

---

## 🔄 Pull Request Process

1. **Fork** the repository and create a branch from `main`
2. **Name your branch** descriptively:
   - `feat/zotero-batch-import`
   - `fix/pdf-extraction-encoding`
   - `docs/api-reference-update`
3. **Make your changes** following the code guidelines above
4. **Test your changes**:
   ```bash
   # Backend tests
   cd paper_agent/backend
   pytest

   # Lint check
   ruff check .

   # Frontend tests (if applicable)
   cd paper_agent/frontend
   npm test
   ```
5. **Commit** with a clear message (see convention above)
6. **Push** to your fork and open a PR against `main`
7. **Describe your changes**: What, why, and how to test
8. **Wait for review**: Maintainers will review within 1-3 days

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] New features include i18n translations (en + zh)
- [ ] API changes include OpenAPI/Swagger annotations
- [ ] Tests pass and coverage is maintained
- [ ] Documentation is updated (docs/ if applicable)
- [ ] No sensitive data (keys, secrets) in code

---

## 🧪 Testing

```bash
# Run all backend tests
pytest

# Run with coverage
pytest --cov=paper_agent.backend --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### Test Guidelines

- Write tests for all new functionality
- Use pytest fixtures for test data
- Mock external services (LLM APIs, arXiv, Zotero)
- Include both success and error path tests

---

## 📖 Documentation

Good documentation is crucial. When adding features:

1. Update the relevant section in `docs/user-guide.md`
2. Add API endpoints to `docs/api.md`
3. Update `README.md` feature list if adding major capabilities
4. Add i18n keys to both `en/common.json` and `zh/common.json`
5. Include docstrings on all new Python functions and classes

---

## ❓ Questions?

- Open a [Discussion](https://github.com/KingdeGuo/paper-agent/discussions)
- Check existing [Issues](https://github.com/KingdeGuo/paper-agent/issues)
- Ask in PR comments during review

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.
