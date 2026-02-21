# CRITICAL: Disable proxy BEFORE any imports that use requests/urllib
# This fixes Yahoo Finance 403 Forbidden errors in environments with restrictive proxies
import os
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
# Remove proxy environment variables
for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(proxy_var, None)

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

    # Run auto-update on startup (incremental update)
    logger.info("Running auto-update on startup...")
    try:
        update_service = AutoUpdateService()
        result = await update_service.run_update(force=False)
        logger.info(f"Startup update completed: {result}")
    except Exception as e:
        logger.error(f"Startup update failed: {e}")

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


@app.get("/")
async def root():
    return {"message": "Broker API - B3 Stock Market"}
