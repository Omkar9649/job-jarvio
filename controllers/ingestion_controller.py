from datetime import datetime, timezone

from controllers.company_controller import CompanyController
from controllers.job_controller import JobController
from scrapers.careers.find_career_urls import find_career_urls
from scrapers.careers.scrape_jobs import scrape_jobs

_ingestion_state: dict = {
    "running": False,
    "last_run": None,
    "last_result": None,
    "last_error": None,
}


class IngestionController:
    @staticmethod
    def get_status() -> dict:
        return dict(_ingestion_state)

    @staticmethod
    def run_pipeline(
        limit: int = 20,
        slug: str | None = None,
        skip_import: bool = False,
        skip_find: bool = False,
        skip_scrape: bool = False,
    ) -> dict:
        if _ingestion_state["running"]:
            return {"started": False, "message": "Ingestion already running"}

        _ingestion_state["running"] = True
        _ingestion_state["last_error"] = None
        result: dict = {"started": True}

        try:
            if not skip_import:
                result["companies_imported"] = CompanyController.import_from_csv()

            if not skip_find:
                result["career_url_stats"] = find_career_urls(limit=limit, slug=slug)

            if not skip_scrape:
                result["job_scrape_stats"] = scrape_jobs(limit=limit, slug=slug)

            result["jobs_exported"] = JobController.export_to_csv()
            _ingestion_state["last_result"] = result
            _ingestion_state["last_run"] = datetime.now(timezone.utc).isoformat()
            return result
        except Exception as exc:
            _ingestion_state["last_error"] = str(exc)
            raise
        finally:
            _ingestion_state["running"] = False
