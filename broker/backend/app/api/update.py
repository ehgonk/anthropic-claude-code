"""
Auto-update API endpoints

Endpoints for controlling and monitoring automatic stock data updates.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from datetime import datetime

from ..services.auto_update import auto_update_service
from ..scheduler import scheduler

router = APIRouter(prefix="/update", tags=["update"])


@router.get("/status")
async def get_update_status():
    """
    Get current auto-update status

    Returns information about the last update run, including:
    - When it last ran
    - Whether it succeeded
    - Statistics about the update
    - Whether an update is currently running
    """
    return auto_update_service.get_status()


@router.post("/run")
async def run_update(
    background_tasks: BackgroundTasks,
    force: bool = False
):
    """
    Manually trigger an update

    - **force**: If true, re-download all data. If false (default), only download missing data.

    The update runs in the background and returns immediately.
    Use GET /update/status to check progress.
    """
    status = auto_update_service.get_status()

    if status["is_running"]:
        raise HTTPException(
            status_code=409,
            detail="An update is already running. Check /update/status for progress."
        )

    # Run update in background
    background_tasks.add_task(auto_update_service.run_update, force=force)

    return {
        "status": "started",
        "message": "Update started in background",
        "force": force,
        "started_at": datetime.utcnow().isoformat()
    }


@router.post("/run-sync")
async def run_update_sync(force: bool = False):
    """
    Manually trigger an update (synchronous)

    - **force**: If true, re-download all data. If false (default), only download missing data.

    This endpoint waits for the update to complete before returning.
    Use this for testing or when you need to know the result immediately.

    ⚠️ WARNING: This can take several minutes to complete!
    """
    try:
        result = await auto_update_service.run_update(force=force)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.get("/schedule")
async def get_schedule():
    """
    Get scheduler information

    Returns information about the automatic update schedule:
    - Whether scheduler is running
    - Next scheduled run time
    """
    return {
        "enabled": scheduler.is_running(),
        "next_run": scheduler.get_next_run_time(),
        "timezone": "America/Sao_Paulo",
        "schedule": "Daily at 19:00 (7 PM Brazil time)"
    }
