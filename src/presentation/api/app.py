"""FastAPI application entry point."""

from fastapi import FastAPI

from src.domain.value_objects.item_category import ItemCategory
from src.infrastructure.config import load_category_keywords

# Load configuration at startup
ItemCategory.set_keywords(load_category_keywords())

app = FastAPI(
    title="Is It Stolen API",
    description="WhatsApp bot for checking and reporting stolen items",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Status message indicating service is healthy
    """
    return {"status": "healthy"}
