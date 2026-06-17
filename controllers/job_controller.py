import csv
from datetime import datetime

from configs.settings import EXPORTS_DIR, JOBS_EXPORT_CSV
from models.companies.company_model import CompanyModel
from models.jobs.job_model import JobModel


def _serialize_doc(doc: dict) -> dict:
    result = dict(doc)
    if "_id" in result:
        result["id"] = str(result["_id"])
        del result["_id"]
    return result


class JobController:
    @staticmethod
    def save_jobs(company: dict, jobs: list[dict]) -> int:
        slug = company["slug"]
        db_company = CompanyModel.find_by_slug(slug)
        if not db_company:
            return 0

        saved = 0
        for job in jobs:
            if JobModel.upsert_job(db_company, job):
                saved += 1

        CompanyModel.mark_scraped(slug)
        return saved

    @staticmethod
    def list_jobs(limit: int = 50, skip: int = 0, company_slug: str | None = None) -> dict:
        docs = JobModel.find_paginated(limit=limit, skip=skip, company_slug=company_slug)
        return {
            "total": JobModel.count(company_slug=company_slug),
            "limit": limit,
            "skip": skip,
            "data": [_serialize_doc(doc) for doc in docs],
        }

    @staticmethod
    def export_to_csv(output_path=JOBS_EXPORT_CSV) -> int:
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        rows = JobModel.find_all_for_export()

        fieldnames = ["company_name", "company_slug", "title", "location", "url", "source", "scraped_at"]
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                scraped_at = row.get("scraped_at")
                if isinstance(scraped_at, datetime):
                    scraped_at = scraped_at.isoformat()
                writer.writerow(
                    {
                        "company_name": row.get("company_name", ""),
                        "company_slug": row.get("company_slug", ""),
                        "title": row.get("title", ""),
                        "location": row.get("location", ""),
                        "url": row.get("url", ""),
                        "source": row.get("source", ""),
                        "scraped_at": scraped_at or "",
                    }
                )
        return len(rows)
