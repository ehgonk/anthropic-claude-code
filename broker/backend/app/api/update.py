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
    Get the last update date formatted as dd/mm/yyyy HH:MM (BRT).

    Returns the date of the most recent candle plus the time the data was last fetched.
    Used by frontend to display in the headline.
    """
    from ..database import AsyncSessionLocal
    from ..models import Stock, StockPrice
    from sqlalchemy import select, func
    from datetime import datetime, timezone, timedelta

    BRT = timezone(timedelta(hours=-3))

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.max(StockPrice.date)))
        last_date = result.scalar()

        if last_date:
            if isinstance(last_date, str):
                date_obj = datetime.strptime(last_date, "%Y-%m-%d").date()
            else:
                date_obj = last_date

            formatted_date = date_obj.strftime("%d/%m/%Y")

            # Use max(Stock.updated_at) as last-fetched time — persists across restarts
            result_time = await db.execute(select(func.max(Stock.updated_at)))
            last_fetched: datetime | None = result_time.scalar()

            if last_fetched:
                brt_time = last_fetched.replace(tzinfo=timezone.utc).astimezone(BRT)
                time_str = brt_time.strftime("%H:%M")
                formatted = f"{formatted_date} {time_str}"
            else:
                formatted = formatted_date

            return {
                "last_update": formatted,
                "raw_date": str(date_obj)
            }
        else:
            return {
                "last_update": "Sem dados",
                "raw_date": None
            }
