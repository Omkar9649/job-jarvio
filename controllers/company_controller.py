import csv
from pathlib import Path

from configs.settings import COMPANIES_CSV
from models.companies.company_model import CompanyModel

PLATFORM_DEFAULTS: dict[str, dict] = {
    "tcs": {"career_url": "https://www.tcs.com/careers"},
    "accenture": {"career_url": "https://www.accenture.com/in-en/careers"},
    "wipro": {
        "career_url": "https://careers.wipro.com/",
        "scrape_type": "workday",
        "scrape_config": {
            "base_url": "https://careers.wipro.com",
            "tenant": "wipro",
            "site": "External",
        },
    },
    "cognizant": {
        "career_url": "https://careers.cognizant.com/global-en/jobs",
        "scrape_type": "rss",
        "scrape_config": {
            "format": "job_xml",
            "feed_url": "https://careers.cognizant.com/global-en/jobs/xml/?rss=true",
            "url_pattern": r"/[\w-]+/jobs/\d+/",
        },
    },
    "capgemini": {"career_url": "https://www.capgemini.com/careers/"},
    "infosys": {"career_url": "https://www.infosys.com/careers.html"},
    "hcl-technologies": {"career_url": "https://www.hcltech.com/careers"},
    "tech-mahindra": {
        "career_url": "https://careers.techmahindra.com/Currentopportunity.aspx",
        "scrape_type": "html_cards",
        "scrape_config": {
            "listing_paths": ["/Currentopportunity.aspx", "/"],
            "link_contains": "JobDetails.aspx",
            "title_parent_class": "title2",
            "dedupe_param": "JobCode",
        },
    },
    "ltimindtree": {"career_url": "https://www.ltimindtree.com/careers"},
    "ibm": {"career_url": "https://www.ibm.com/careers"},
    "mphasis": {"career_url": "https://careers.mphasis.com/"},
    "dxc-technology": {
        "career_url": "https://careers.dxc.com/",
        "scrape_type": "workday",
        "scrape_config": {
            "base_url": "https://careers.dxc.com",
            "tenant": "dxctechnology",
            "site": "DXCJobs",
        },
    },
    "persistent-systems": {"career_url": "https://www.persistent.com/careers/"},
    "cyient": {"career_url": "https://www.cyient.com/careers"},
    "hexaware": {"career_url": "https://hexaware.com/careers/"},
    "zensar": {"career_url": "https://www.zensar.com/careers"},
    "larsen-toubro-infotech": {"career_url": "https://www.lntinfotech.com/careers/"},
    "oracle": {"career_url": "https://www.oracle.com/careers/"},
    "sap": {"career_url": "https://jobs.sap.com/"},
    "microsoft": {"career_url": "https://careers.microsoft.com/"},
}


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
    def import_from_csv(csv_path: Path = COMPANIES_CSV) -> int:
        if not csv_path.exists():
            raise FileNotFoundError(f"Companies CSV not found: {csv_path}")

        count = 0
        with csv_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
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

    @staticmethod
    def update_scrape_config(
        slug: str,
        scrape_type: str | None,
        scrape_config: dict | None = None,
    ) -> None:
        CompanyModel.update_scrape_config(slug, scrape_type, scrape_config)

    @staticmethod
    def seed_platform_defaults() -> int:
        """Fill career_url / scrape_type on companies that are missing them."""
        updated = 0
        for slug, fields in PLATFORM_DEFAULTS.items():
            company = CompanyModel.find_by_slug(slug)
            if not company:
                continue

            set_fields: dict = {}
            if fields.get("career_url") and not company.get("career_url"):
                set_fields["career_url"] = fields["career_url"]
                set_fields["career_url_status"] = "known"

            if fields.get("scrape_type") and not company.get("scrape_type"):
                set_fields["scrape_type"] = fields["scrape_type"]
                set_fields["scrape_config"] = fields.get("scrape_config") or {}

            if not set_fields:
                continue

            CompanyModel.collection().update_one({"slug": slug}, {"$set": set_fields})
            updated += 1
            print(f"[seed] {slug}: {', '.join(set_fields.keys())}")

        return updated

    @staticmethod
    def update_scrape_status(
        slug: str,
        status: str,
        reason: str | None = None,
        job_count: int | None = None,
    ) -> None:
        CompanyModel.update_scrape_status(slug, status, reason, job_count)
