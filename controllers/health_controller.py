from configs.db.mongo_conn import get_client
from configs.settings import MONGO_DB_NAME


class HealthController:
    @staticmethod
    def check() -> dict:
        get_client().admin.command("ping")
        return {
            "status": "ok",
            "message": "Job Jarvios API is running",
            "database": MONGO_DB_NAME,
        }
