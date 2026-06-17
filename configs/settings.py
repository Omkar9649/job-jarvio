from pathlib import Path
import os

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / "config.env")

DATA_DIR = ROOT_DIR / "data"
EXPORTS_DIR = DATA_DIR / "exports"
KNOWN_CAREER_URLS_PATH = DATA_DIR / "known_career_urls.json"

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "job_jarvios")
PORT = int(os.getenv("PORT", "8000"))

COMPANIES_CSV = DATA_DIR / "companies.csv"
if not COMPANIES_CSV.exists():
    COMPANIES_CSV = ROOT_DIR / "companies.csv"

JOBS_EXPORT_CSV = EXPORTS_DIR / "jobs.csv"

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-IN,en;q=0.9",
}

REQUEST_TIMEOUT = 30
REQUEST_DELAY_SECONDS = 2

JOB_LINK_PATTERN = (
    r"(job|jobs|career|careers|position|opening|vacancy|requisition|req-id|jobdetail|job-detail)"
)
