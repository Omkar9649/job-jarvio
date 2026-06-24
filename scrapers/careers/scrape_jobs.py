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

JUNK_TITLES = frozenset(
    {
        "learn more", "read more", "view all", "apply now", "apply",
        "apply/shortlist", "shortlist", "join our talent network",
    }
)


def _scrape_quality_issue(jobs: list[dict]) -> str | None:
    if not jobs:
        return "empty"
    titles = [str(j.get("title", "")).strip().lower() for j in jobs]
    urls = [str(j.get("url", "")).strip() for j in jobs]
    if sum(t in JUNK_TITLES or "apply/shortlist" in t for t in titles) / len(titles) > 0.3:
        return "cta_titles"
    if len(urls) != len(set(urls)):
        return "duplicate_urls"
    if urls and all("persona=" in u.lower() for u in urls):
        return "persona_listing_urls"
    return None


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

    from scrapers.careers.fetch_jobs import fetch_jobs_via_ats, has_platform_config

    ats_jobs = fetch_jobs_via_ats(company)
    if ats_jobs:
        return ats_jobs

    # Configured companies must not fall back to generic HTML (avoids CTA junk).
    if has_platform_config(company):
        print(f"[skip-fallback] {company['name']}: platform configured but returned no jobs")
        return []

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
    stats = {"companies": 0, "jobs_saved": 0, "empty": 0, "rejected": 0}

    for company in companies:
        stats["companies"] += 1
        try:
            jobs = scrape_company_jobs(company)
            quality_issue = _scrape_quality_issue(jobs)

            if quality_issue:
                stats["rejected"] += 1
                CompanyController.update_scrape_status(
                    company["slug"],
                    status="needs_review",
                    reason=quality_issue,
                    job_count=len(jobs),
                )
                print(
                    f"[reject] {company['name']}: {len(jobs)} jobs discarded ({quality_issue})"
                )
                continue

            saved = JobController.save_jobs(company, jobs)
            stats["jobs_saved"] += saved
            CompanyController.update_scrape_status(
                company["slug"],
                status="ok" if jobs else "empty",
                reason=None,
                job_count=len(jobs),
            )

            if jobs:
                print(f"[jobs] {company['name']}: {len(jobs)} found, {saved} saved")
            else:
                stats["empty"] += 1
                print(f"[empty] {company['name']}: no jobs (ATS API + HTML + Playwright)")
        except Exception as exc:
            CompanyController.update_scrape_status(
                company["slug"],
                status="failed",
                reason=str(exc),
                job_count=0,
            )
            print(f"[error] {company['name']}: {exc}")

    return stats
