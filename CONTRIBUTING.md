# Contributing to Paper Agent

We love your input! We want to make contributing to Paper Agent as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Environment Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- (Optional) Kubernetes / Minikube

### Backend Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations and start:
   ```bash
   python -m paper_agent.backend.main
   ```

### Frontend Setup
1. Navigate to frontend directory:
   ```bash
   cd paper_agent/frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start development server:
   ```bash
   npm start
   ```

## Pull Request Process

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. Ensure the test suite passes.
4. Make sure your code lints.
5. Issue that pull request!

## Any questions?
Feel free to open an issue or reach out to the maintainers.
