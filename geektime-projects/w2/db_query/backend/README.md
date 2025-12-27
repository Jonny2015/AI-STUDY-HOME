# Database Query Tool - Backend

FastAPI backend for the Database Query Tool.

## Prerequisites

- Python 3.11+
- uv (Python package manager)
- LLM API key (OpenAI, or custom OpenAI-compatible API)

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
   # Edit .env and add your LLM configuration
   ```

### LLM Configuration

The application supports various LLM providers through OpenAI-compatible APIs:

#### Option 1: OpenAI (Default)
```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-openai-api-key
LLM_MODEL=gpt-4o-mini
```

#### Option 2: Custom OpenAI-Compatible API
Use any OpenAI-compatible API (local models, domestic services, etc.):

```bash
LLM_PROVIDER=custom
LLM_API_KEY=your-custom-api-key
LLM_BASE_URL=https://your-api-endpoint.com/v1
LLM_MODEL=your-model-name
```

#### Option 3: Moonshot AI (Kimi)
```bash
LLM_PROVIDER=custom
LLM_API_KEY=your-moonshot-api-key
LLM_BASE_URL=https://api.moonshot.cn/v1
LLM_MODEL=moonshot-v1-8k
```

#### Option 4: Alibaba Qwen (通义千问)
```bash
LLM_PROVIDER=custom
LLM_API_KEY=sk-your-qwen-api-key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-turbo
```

**Note:** The legacy `OPENAI_API_KEY` is still supported but deprecated. Use `LLM_API_KEY` instead.

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
