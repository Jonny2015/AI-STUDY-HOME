# Database Query Tool - Backend

FastAPI backend for the Database Query Tool.

## Prerequisites

- Python 3.11+
- uv (Python package manager)
- OpenAI API key

## Installation

1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Create virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Development

Run the development server:
```bash
uv run uvicorn app.main:app --reload --port 8000
```

API documentation will be available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Code Quality

Format code:
```bash
uv run black app tests
```

Check linting:
```bash
uv run ruff check app tests
```

Type checking:
```bash
uv run mypy app --strict
```

## Testing

Run tests:
```bash
uv run pytest
```

Run tests with coverage:
```bash
uv run pytest --cov=app
```

## Project Structure

```
app/
├── main.py              # FastAPI application entry
├── config.py            # Configuration management
├── models/              # Pydantic data models
├── adapters/            # Database adapters (SOLID)
├── services/            # Business services
├── api/v1/              # API routes
├── core/                # Core functionality
└── utils/               # Utilities
```
