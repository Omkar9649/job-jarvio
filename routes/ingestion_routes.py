from fastapi import APIRouter, BackgroundTasks, Query

from controllers.ingestion_controller import IngestionController
from utils.app_error import AppError

router = APIRouter()


@router.get("/status")
def ingestion_status() -> dict:
    return IngestionController.get_status()


@router.post("/run")
def run_ingestion(
    background_tasks: BackgroundTasks,
    limit: int = Query(20, ge=1, le=500),
    slug: str | None = None,
    skip_import: bool = False,
    skip_find: bool = False,
    skip_scrape: bool = False,
    background: bool = True,
) -> dict:
    if IngestionController.get_status()["running"]:
        raise AppError("Ingestion already running", 409)

    kwargs = {
        "limit": limit,
        "slug": slug,
        "skip_import": skip_import,
        "skip_find": skip_find,
        "skip_scrape": skip_scrape,
    }

    if background:
        background_tasks.add_task(IngestionController.run_pipeline, **kwargs)
        return {"message": "Ingestion started in background", "status": "running"}

    result = IngestionController.run_pipeline(**kwargs)
    return {"message": "Ingestion completed", "result": result}
