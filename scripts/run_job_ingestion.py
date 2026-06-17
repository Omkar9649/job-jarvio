"""
Step 2 pipeline (CLI alternative to POST /api/ingestion/run):
1. Connect MongoDB + indexes
2. Import companies.csv
3. Find official career URLs
4. Scrape jobs from career pages
5. Export jobs to data/exports/jobs.csv
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from controllers.ingestion_controller import IngestionController
from configs.db.mongo_conn import init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Jarvios - career URL + job ingestion")
    parser.add_argument("--limit", type=int, default=20, help="Number of companies to process")
    parser.add_argument("--slug", type=str, default=None, help="Process one company slug (e.g. tcs)")
    parser.add_argument("--skip-import", action="store_true", help="Skip CSV import step")
    parser.add_argument("--skip-find", action="store_true", help="Skip career URL discovery")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip job scraping")
    args = parser.parse_args()

    init_db()
    print("MongoDB ready.")

    result = IngestionController.run_pipeline(
        limit=args.limit,
        slug=args.slug,
        skip_import=args.skip_import,
        skip_find=args.skip_find,
        skip_scrape=args.skip_scrape,
    )
    print(result)


if __name__ == "__main__":
    main()
