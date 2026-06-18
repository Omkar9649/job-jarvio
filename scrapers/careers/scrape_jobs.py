from urllib.parse import urlparse

from controllers.company_controller import CompanyController
from controllers.job_controller import JobController
from scrapers.careers.http_client import fetch_html
from scrapers.careers.job_parser import career_search_urls, is_ats_host, parse_jobs_from_html

JS_CAREER_HOST_HINTS = (
    "myworkdayjobs.com",
    "myworkdaysite.com",
    "taleo.net",
    "icims.com",
)


def _needs_browser(career_url: str) -> bool:
    host = urlparse(career_url).netloc.lower()
    return is_ats_host(host) or any(hint in host for hint in JS_CAREER_HOST_HINTS)


def _scrape_with_requests(career_url: str) -> list[dict]:
    urls_to_try = [career_url, *career_search_urls(career_url)]
    seen_job_urls: set[str] = set()
    all_jobs: list[dict] = []

    for url in urls_to_try:
        try:
            html = fetch_html(url)
            jobs = parse_jobs_from_html(html, url)
            for job in jobs:
                if job["url"] not in seen_job_urls:
                    seen_job_urls.add(job["url"])
                    all_jobs.append(job)
        except Exception:
            continue

    return all_jobs


def scrape_company_jobs(company: dict) -> list[dict]:
    career_url = company["career_url"]

    # Prefer official ATS JSON APIs (Workday, Greenhouse, Lever) over HTML scraping.
    from scrapers.ats.fetch_jobs import fetch_jobs_via_ats

    ats_jobs = fetch_jobs_via_ats(company)
    if ats_jobs:
        return ats_jobs

    if _needs_browser(career_url):
        print(f"[playwright] {company['name']}: JS career site, trying browser...")
        from scrapers.careers.playwright_scraper import scrape_with_playwright

        return scrape_with_playwright(career_url)

    jobs = _scrape_with_requests(career_url)
    if jobs:
        return jobs

    print(f"[playwright] {company['name']}: static scrape empty, trying browser...")
    from scrapers.careers.playwright_scraper import scrape_with_playwright

    return scrape_with_playwright(career_url)


def scrape_jobs(limit: int | None = 20, slug: str | None = None) -> dict[str, int]:
    companies = CompanyController.get_for_job_scrape(limit=limit, slug=slug)
    stats = {"companies": 0, "jobs_saved": 0, "empty": 0}

    for company in companies:
        stats["companies"] += 1
        try:
            jobs = scrape_company_jobs(company)
            saved = JobController.save_jobs(company, jobs)
            stats["jobs_saved"] += saved

            if jobs:
                print(f"[jobs] {company['name']}: {len(jobs)} found, {saved} saved")
            else:
                stats["empty"] += 1
                print(f"[empty] {company['name']}: no jobs (ATS API + HTML + Playwright)")
        except Exception as exc:
            print(f"[error] {company['name']}: {exc}")

    return stats
