"""
Job Jarvios — simple runner (no API needed)

  python run.py setup       # FIRST TIME: load companies.csv into MongoDB
  python run.py             # scrape jobs from 10 companies
  python run.py tcs         # scrape jobs from one company (e.g. TCS)
  python run.py --limit 5   # scrape 5 companies

Data is saved in MongoDB Atlas (database: job_jarvios).
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from configs.db.mongo_conn import init_db
from controllers.pipeline_controller import PipelineController


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Jarvios — scrape jobs from company career pages")
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="'setup' for first-time import, or a company slug like tcs",
    )
    parser.add_argument("--limit", type=int, default=10, help="How many companies to process (default: 10)")
    args = parser.parse_args()

    import_companies = args.target == "setup"
    slug = None if import_companies else args.target

    print("Connecting to MongoDB...")
    init_db()
    print("Connected.\n")

    if import_companies:
        print("Importing companies from CSV (one-time setup)...")
    else:
        label = slug or f"top {args.limit} companies"
        print(f"Finding career URLs + scraping jobs for {label}...")
        print("(This can take 1–5 minutes — please wait)\n")

    result = PipelineController.run(
        limit=args.limit,
        slug=slug,
        import_companies=import_companies,
    )

    print("\n--- Done ---")
    if import_companies:
        print(f"Companies imported: {result.get('companies_imported', 0)}")
    else:
        career = result.get("career_url_stats", {})
        jobs = result.get("job_scrape_stats", {})
        print(f"Career URLs found: {career.get('found', 0)}")
        print(f"Jobs saved to MongoDB: {jobs.get('jobs_saved', 0)}")
        print(f"Jobs exported to CSV: {result.get('jobs_exported', 0)}")
    print("\nCheck MongoDB Compass → job_jarvios → jobs")


if __name__ == "__main__":
    main()
