"""
Auto-update API endpoints

Endpoints for controlling and monitoring automatic stock data updates.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from datetime import datetime

from ..services.auto_update import auto_update_service

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


@router.get("/last-update-date")
async def get_last_update_date():
    """
    Get the last update date formatted as dd/mm/yyyy

    Returns the date of the most recent successful update in Brazilian date format.
    Used by frontend to display in the headline.
    """
    from ..database import AsyncSessionLocal
    from ..models import StockPrice
    from sqlalchemy import select, func
    from datetime import datetime

    async with AsyncSessionLocal() as db:
        # Get the most recent date in the database
        result = await db.execute(select(func.max(StockPrice.date)))
        last_date = result.scalar()

        if last_date:
            # Convert string to date if needed
            if isinstance(last_date, str):
                date_obj = datetime.strptime(last_date, "%Y-%m-%d").date()
            else:
                date_obj = last_date

            # Format as dd/mm/yyyy
            formatted_date = date_obj.strftime("%d/%m/%Y")
            return {
                "last_update": formatted_date,
                "raw_date": str(date_obj)
            }
        else:
            return {
                "last_update": "Sem dados",
                "raw_date": None
            }
