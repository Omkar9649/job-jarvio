from datetime import datetime, timezone

from configs.db.collections import COMPANIES
from configs.db.mongo_conn import get_db

COLLECTION_NAME = COMPANIES

SCHEMA = {
    "name": {"type": str, "allow_null": False},
    "slug": {"type": str, "allow_null": False, "unique": True},
    "rating": {"type": str, "allow_null": True},
    "profile_url": {"type": str, "allow_null": True},
    "website_url": {"type": str, "allow_null": True},
    "career_url": {"type": str, "allow_null": True},
    "career_url_status": {"type": str, "allow_null": True},
    "last_career_lookup_at": {"type": datetime, "allow_null": True},
    "last_scraped_at": {"type": datetime, "allow_null": True},
    "created_at": {"type": datetime, "allow_null": True},
    "updated_at": {"type": datetime, "allow_null": True},
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CompanyModel:
    collection_name = COLLECTION_NAME
    schema = SCHEMA
    timestamps = False

    @classmethod
    def collection(cls):
        return get_db()[cls.collection_name]

    @classmethod
    def sync_indexes(cls) -> None:
        cls.collection().create_index("slug", unique=True)
        cls.collection().create_index("career_url")

    @classmethod
    def upsert_by_slug(cls, data: dict) -> None:
        slug = data["slug"]
        now = _utc_now()
        cls.collection().update_one(
            {"slug": slug},
            {
                "$set": {**data, "updated_at": now},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

    @classmethod
    def update_career_url(
        cls,
        slug: str,
        career_url: str | None,
        status: str,
        website_url: str | None = None,
    ) -> None:
        update_fields = {
            "career_url": career_url,
            "career_url_status": status,
            "last_career_lookup_at": _utc_now(),
            "updated_at": _utc_now(),
        }
        if website_url:
            update_fields["website_url"] = website_url

        cls.collection().update_one({"slug": slug}, {"$set": update_fields})

    @classmethod
    def find_without_career_url(cls, limit: int | None = None, slug: str | None = None) -> list[dict]:
        missing_career = {
            "$or": [
                {"career_url": {"$exists": False}},
                {"career_url": None},
                {"career_url": ""},
            ]
        }
        query = {"$and": [{"slug": slug}, missing_career]} if slug else missing_career

        cursor = cls.collection().find(query).sort("created_at", 1)
        if limit is not None:
            cursor = cursor.limit(limit)
        return list(cursor)

    @classmethod
    def find_with_career_url(cls, limit: int | None = None, slug: str | None = None) -> list[dict]:
        query: dict = {"career_url": {"$nin": [None, ""]}}
        if slug:
            query["slug"] = slug

        cursor = cls.collection().find(query).sort("created_at", 1)
        if limit is not None:
            cursor = cursor.limit(limit)
        return list(cursor)

    @classmethod
    def find_all(
        cls,
        limit: int = 50,
        skip: int = 0,
        slug: str | None = None,
        has_career_url: bool | None = None,
    ) -> list[dict]:
        query: dict = {}
        if slug:
            query["slug"] = slug
        if has_career_url is True:
            query["career_url"] = {"$nin": [None, ""]}
        elif has_career_url is False:
            query["$or"] = [
                {"career_url": {"$exists": False}},
                {"career_url": None},
                {"career_url": ""},
            ]

        return list(
            cls.collection()
            .find(query)
            .sort("name", 1)
            .skip(skip)
            .limit(limit)
        )

    @classmethod
    def count(cls, has_career_url: bool | None = None) -> int:
        query: dict = {}
        if has_career_url is True:
            query["career_url"] = {"$nin": [None, ""]}
        elif has_career_url is False:
            query["$or"] = [
                {"career_url": {"$exists": False}},
                {"career_url": None},
                {"career_url": ""},
            ]
        return cls.collection().count_documents(query)

    @classmethod
    def mark_scraped(cls, slug: str) -> None:
        cls.collection().update_one(
            {"slug": slug},
            {"$set": {"last_scraped_at": _utc_now(), "updated_at": _utc_now()}},
        )

    @classmethod
    def find_by_slug(cls, slug: str) -> dict | None:
        return cls.collection().find_one({"slug": slug})
