from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from .config import settings
from .database import init_db
from .api.routes import router
from .api.stocks import router as stocks_router
from .api.update import router as update_router
from .api.ibovespa import router as ibovespa_router
from .api.admin import router as admin_router
from .services.auto_update import AutoUpdateService
from .logging_config import setup_logging
import logging

# Setup logging
setup_logging(level="INFO")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    # Startup
    await init_db()

    # Auto-update disabled on startup (requires external network access)
    # logger.info("Running auto-update on startup...")
    # try:
    #     update_service = AutoUpdateService()
    #     result = await update_service.run_update(force=False)
    #     logger.info(f"Startup update completed: {result}")
    # except Exception as e:
    #     logger.error(f"Startup update failed: {e}")

    yield

    # Shutdown
    pass


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add no-cache headers middleware
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    """Add no-cache headers to all API responses"""
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Include routers
app.include_router(router)
app.include_router(stocks_router, prefix="/api")
app.include_router(update_router, prefix="/api")
app.include_router(ibovespa_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


@app.get("/api")
async def root():
    return {"message": "Broker API - Bolsa de Valores"}


# Mount static files (frontend build)
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    # Serve index.html for all other routes (SPA support)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend for all non-API routes"""
        # If it's an API route, let FastAPI handle it (this won't be reached)
        if full_path.startswith("api/"):
            return JSONResponse({"error": "Not found"}, status_code=404)

        # Serve index.html for all other routes
        return FileResponse(frontend_dist / "index.html")
else:
    logger.warning(f"Frontend dist directory not found: {frontend_dist}")
