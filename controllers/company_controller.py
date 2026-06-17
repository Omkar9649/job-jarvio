import csv
import json
from pathlib import Path

from configs.settings import COMPANIES_CSV, KNOWN_CAREER_URLS_PATH
from models.companies.company_model import CompanyModel


def _serialize_doc(doc: dict | None) -> dict | None:
    if not doc:
        return None
    result = dict(doc)
    if "_id" in result:
        result["id"] = str(result["_id"])
        del result["_id"]
    return result


class CompanyController:
    @staticmethod
    def load_known_career_urls() -> dict[str, str]:
        if not KNOWN_CAREER_URLS_PATH.exists():
            return {}
        return json.loads(KNOWN_CAREER_URLS_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def import_from_csv(csv_path: Path = COMPANIES_CSV) -> int:
        if not csv_path.exists():
            raise FileNotFoundError(f"Companies CSV not found: {csv_path}")

        count = 0
        with csv_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            print(reader)
            for row in reader:
                slug = row.get("slug", "").strip()
                if not slug:
                    continue

                CompanyModel.upsert_by_slug(
                    {
                        "name": row.get("company_name", "").strip(),
                        "slug": slug,
                        "rating": row.get("rating", "").strip(),
                        "profile_url": row.get("profile_url", "").strip(),
                    }
                )
                count += 1
        return count

    @staticmethod
    def list_companies(
        limit: int = 50,
        skip: int = 0,
        slug: str | None = None,
        has_career_url: bool | None = None,
    ) -> dict:
        docs = CompanyModel.find_all(
            limit=limit,
            skip=skip,
            slug=slug,
            has_career_url=has_career_url,
        )
        return {
            "total": CompanyModel.count(has_career_url=has_career_url),
            "limit": limit,
            "skip": skip,
            "data": [_serialize_doc(doc) for doc in docs],
        }

    @staticmethod
    def get_by_slug(slug: str) -> dict | None:
        return _serialize_doc(CompanyModel.find_by_slug(slug))

    @staticmethod
    def get_for_career_lookup(limit: int | None = None, slug: str | None = None) -> list[dict]:
        docs = CompanyModel.find_without_career_url(limit=limit, slug=slug)
        return [_serialize_doc(doc) for doc in docs]

    @staticmethod
    def get_for_job_scrape(limit: int | None = None, slug: str | None = None) -> list[dict]:
        docs = CompanyModel.find_with_career_url(limit=limit, slug=slug)
        return [_serialize_doc(doc) for doc in docs]

    @staticmethod
    def update_career_url(
        slug: str,
        career_url: str | None,
        status: str,
        website_url: str | None = None,
    ) -> None:
        CompanyModel.update_career_url(slug, career_url, status, website_url)
