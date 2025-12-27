"""Error response models for API."""

from typing import Any

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel


class ErrorResponse(BaseModel):
    """Standard error response.

    Attributes:
        error: Error type/category
        message: Human-readable error message
        details: Additional error details (optional)
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error details",
    )
