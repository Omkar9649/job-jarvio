"""MongoDB connection (like configs/db/conveyance.js in Express projects)."""

from pymongo import MongoClient
from pymongo.database import Database

from configs.settings import MONGO_DB_NAME, MONGO_URI

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client


def get_db() -> Database:
    return get_client()[MONGO_DB_NAME]


def init_db() -> None:
    from models.companies.company_model import CompanyModel
    from models.jobs.job_model import JobModel

    get_client().admin.command("ping")
    CompanyModel.sync_indexes()
    JobModel.sync_indexes()
