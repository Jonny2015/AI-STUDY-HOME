"""Database Query Tool - FastAPI Application."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # pragma: no cover
    """Application lifespan manager.

    Yields:
        None
    """
    # Startup
    from app.core.db import db_manager

    await db_manager.initialize_database()
    yield
    # Shutdown
    # Cleanup


# Create FastAPI application
app = FastAPI(
    title="Database Query Tool",
    description="API for managing database connections and executing SQL queries",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS - allow all origins (Open Access Policy)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions.

    Args:
        request: The request object
        exc: The exception

    Returns:
        JSONResponse with error details
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": str(exc),
            "details": None,
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict with status
    """
    return {"status": "healthy"}


# Import and include API routers
from app.api.v1 import databases, queries

app.include_router(databases.router, prefix="/api/v1")
app.include_router(queries.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
