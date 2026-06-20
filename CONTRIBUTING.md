# Contributing to Traffic Sentinel

Thank you for your interest in contributing! This document explains how to get involved.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Commit Messages](#commit-messages)



## Code of Conduct

Be respectful, constructive, and inclusive. We are building public-interest civic technology for Uganda — that mission deserves collaborative, professional engagement.



## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/traffic-sentinel.git
   cd traffic-sentinel
   ```
3. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Run the tests** to verify your setup:
   ```bash
   pytest tests/ -v
   ```



## How to Contribute

### Reporting bugs

Open a GitHub Issue with:
- A clear title
- Steps to reproduce
- Expected vs. actual behaviour
- Python version and OS

### Suggesting features

Open a GitHub Issue tagged `enhancement`. Describe the use case first — we prioritise work that directly improves road safety outcomes in Uganda.

### Submitting a pull request

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
2. Make your changes.
3. Add or update tests as appropriate.
4. Run `pytest tests/ -v` — all tests must pass.
5. Push your branch and open a PR against `main`.
6. Fill in the PR template describing *what* changed and *why*.



## Development Workflow

```
main          ← stable, always deployable
 └── feat/*   ← feature branches (merge via PR)
 └── fix/*    ← bug-fix branches
 └── docs/*   ← documentation-only changes
```

Keep branches short-lived. Rebase onto `main` before opening a PR to avoid merge conflicts.



## Code Style

- **Python**: [PEP 8](https://peps.python.org/pep-0008/) — enforced with `ruff` or `flake8`.
- **Imports**: grouped (stdlib → third-party → local), sorted with `isort`.
- **Type hints**: use them on all public functions.
- **Docstrings**: one-line summary + blank line + detail for non-trivial functions.

Run the linter before committing:
```bash
ruff check backend/ tests/
```



## Testing

Tests live in `tests/`. We use `pytest`.

```bash
# Run all tests
pytest tests/ -v

# Run a single test class
pytest tests/test_basic.py::TestRiskPredictor -v

# Run with coverage (requires pytest-cov)
pytest tests/ --cov=backend --cov-report=term-missing
```

When adding a new service or module, add a corresponding test class in `tests/`.


## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(api): add /api/hotspots endpoint
fix(risk): clamp score to [0, 100] before returning
docs(readme): update quick-start instructions
test(analytics): add coverage for empty results edge case
refactor(services): extract _persist helper to VideoProcessorService
```

Use the imperative mood in the subject line. Keep it under 72 characters.



*Traffic Sentinel is maintained by [Keith Ndiema Kissa](https://github.com/veritasndiema-ctrl) and contributors.*