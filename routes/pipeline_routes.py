from fastapi import APIRouter, BackgroundTasks, Query

from controllers.pipeline_controller import PipelineController
from utils.app_error import AppError

router = APIRouter()


@router.post("/run")
def run_pipeline(
    background_tasks: BackgroundTasks,
    limit: int = Query(10, ge=1, le=500),
    slug: str | None = Query(None, example="tcs"),
    import_companies: bool = Query(False, description="First time only: load companies.csv"),
    background: bool = Query(False, description="True = return immediately (advanced)"),
) -> dict:
    """
    One API does everything: find career URLs → scrape jobs → save to MongoDB.

    **First time:** `POST /api/pipeline/run?import_companies=true&limit=1`
    **Normal use:** `POST /api/pipeline/run?slug=tcs&limit=1`
    """
    if PipelineController.get_status()["running"]:
        raise AppError("Pipeline already running", 409)

    kwargs = {"limit": limit, "slug": slug, "import_companies": import_companies}

    if background:
        background_tasks.add_task(PipelineController.run, **kwargs)
        return {"status": "running", "message": "Started in background. Check GET /api/pipeline/status"}

    result = PipelineController.run(**kwargs)
    career = result.get("career_url_stats", {})
    jobs = result.get("job_scrape_stats", {})

    return {
        "status": "completed",
        "message": "Pipeline finished",
        "career_urls_found": career.get("found", 0),
        "jobs_saved": jobs.get("jobs_saved", 0),
        "jobs_exported": result.get("jobs_exported", 0),
        "details": result,
    }


@router.get("/status")
def pipeline_status() -> dict:
    return PipelineController.get_status()
