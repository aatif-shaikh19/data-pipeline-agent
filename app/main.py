from contextlib import asynccontextmanager
from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.core.limiter import limiter
from app.api.routes import router as agent_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown events."""
    logger.info("Pipeline Guardian API service initialized.")
    yield
    logger.info("Pipeline Guardian API service shutting down.")


app = FastAPI(
    title="Pipeline Guardian API",
    description="Data Pipeline Reliability & Security Assistant API",
    version="0.1.0",
    lifespan=lifespan,
)

# Register rate limiter and middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Register routes
app.include_router(agent_router, prefix="/agent", tags=["Agent"])


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for container orchestrators and monitoring."""
    return {"status": "ok"}
