from fastapi import APIRouter, Query

from controllers.job_controller import JobController

router = APIRouter()


@router.get("")
def list_jobs(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    company_slug: str | None = None,
) -> dict:
    return JobController.list_jobs(limit=limit, skip=skip, company_slug=company_slug)


@router.post("/export")
def export_jobs() -> dict:
    count = JobController.export_to_csv()
    return {"message": "Jobs exported to CSV", "count": count, "path": "data/exports/jobs.csv"}
