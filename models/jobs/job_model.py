from datetime import datetime, timezone

from configs.db.collections import JOBS
from configs.db.mongo_conn import get_db

COLLECTION_NAME = JOBS

SCHEMA = {
    "company_id": {"type": "objectId", "allow_null": False},
    "company_slug": {"type": str, "allow_null": False},
    "company_name": {"type": str, "allow_null": True},
    "title": {"type": str, "allow_null": False},
    "location": {"type": str, "allow_null": True},
    "description": {"type": str, "allow_null": True},
    "url": {"type": str, "allow_null": False},
    "source": {"type": str, "allow_null": False, "default": "career_page"},
    "posted_at": {"type": datetime, "allow_null": True},
    "scraped_at": {"type": datetime, "allow_null": True},
    "created_at": {"type": datetime, "allow_null": True},
    "updated_at": {"type": datetime, "allow_null": True},
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobModel:
    collection_name = COLLECTION_NAME
    schema = SCHEMA
    timestamps = False

    @classmethod
    def collection(cls):
        return get_db()[cls.collection_name]

    @classmethod
    def sync_indexes(cls) -> None:
        cls.collection().create_index(
            [("company_slug", 1), ("url", 1)],
            unique=True,
        )
        cls.collection().create_index("company_id")
        cls.collection().create_index("scraped_at")

    @classmethod
    def upsert_job(cls, company: dict, job: dict) -> bool:
        company_id = company["_id"]
        company_slug = company["slug"]
        url = job.get("url", "").strip()
        if not url:
            return False

        result = cls.collection().update_one(
            {"company_slug": company_slug, "url": url},
            {
                "$set": {
                    "company_id": company_id,
                    "company_slug": company_slug,
                    "company_name": company.get("name"),
                    "title": job.get("title", "").strip(),
                    "location": job.get("location"),
                    "description": job.get("description"),
                    "url": url,
                    "source": job.get("source", SCHEMA["source"]["default"]),
                    "scraped_at": _utc_now(),
                    "updated_at": _utc_now(),
                },
                "$setOnInsert": {"created_at": _utc_now()},
            },
            upsert=True,
        )
        return bool(result.upserted_id or result.modified_count)

    @classmethod
    def find_all_for_export(cls) -> list[dict]:
        return list(
            cls.collection()
            .find(
                {},
                {
                    "_id": 0,
                    "company_name": 1,
                    "company_slug": 1,
                    "title": 1,
                    "location": 1,
                    "url": 1,
                    "source": 1,
                    "scraped_at": 1,
                },
            )
            .sort([("scraped_at", -1), ("company_name", 1), ("title", 1)])
        )

    @classmethod
    def find_paginated(
        cls,
        limit: int = 50,
        skip: int = 0,
        company_slug: str | None = None,
    ) -> list[dict]:
        query: dict = {}
        if company_slug:
            query["company_slug"] = company_slug

        return list(
            cls.collection()
            .find(query)
            .sort([("scraped_at", -1), ("title", 1)])
            .skip(skip)
            .limit(limit)
        )

    @classmethod
    def count(cls, company_slug: str | None = None) -> int:
        query: dict = {}
        if company_slug:
            query["company_slug"] = company_slug
        return cls.collection().count_documents(query)
