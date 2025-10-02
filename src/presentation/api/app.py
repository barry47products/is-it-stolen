"""FastAPI application entry point."""
from fastapi import FastAPI

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
