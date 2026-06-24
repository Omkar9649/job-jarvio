from datetime import datetime, timezone

from controllers.company_controller import CompanyController
from controllers.job_controller import JobController
from scrapers.careers.find_career_urls import find_career_urls
from scrapers.careers.scrape_jobs import scrape_jobs

_pipeline_state: dict = {
    "running": False,
    "last_run": None,
    "last_result": None,
    "last_error": None,
}


class PipelineController:
    """Single automation entry point: import → career URLs → scrape jobs → export."""

    @staticmethod
    def get_status() -> dict:
        return dict(_pipeline_state)

    @staticmethod
    def run(
        limit: int = 20,
        slug: str | None = None,
        import_companies: bool = False,
    ) -> dict:
        if _pipeline_state["running"]:
            return {"started": False, "message": "Pipeline already running", "status": "running"}

        _pipeline_state["running"] = True
        _pipeline_state["last_error"] = None
        result: dict = {"started": True, "status": "completed"}

        try:
            if import_companies:
                result["companies_imported"] = CompanyController.import_from_csv()
                result["companies_seeded"] = CompanyController.seed_platform_defaults()

            result["career_url_stats"] = find_career_urls(limit=limit, slug=slug)
            result["job_scrape_stats"] = scrape_jobs(limit=limit, slug=slug)
            result["jobs_exported"] = JobController.export_to_csv()

            _pipeline_state["last_result"] = result
            _pipeline_state["last_run"] = datetime.now(timezone.utc).isoformat()
            return result
        except Exception as exc:
            _pipeline_state["last_error"] = str(exc)
            _pipeline_state["last_result"] = {"started": True, "status": "failed"}
            raise
        finally:
            _pipeline_state["running"] = False
