import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from configs.settings import JOB_LINK_PATTERN
from controllers.company_controller import CompanyController
from controllers.job_controller import JobController
from scrapers.careers.http_client import fetch_html

SKIP_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".css", ".js")
MIN_TITLE_LEN = 8
MAX_TITLE_LEN = 180


def _same_domain(base_url: str, target_url: str) -> bool:
    base_host = urlparse(base_url).netloc.removeprefix("www.")
    target_host = urlparse(target_url).netloc.removeprefix("www.")
    if not target_host:
        return True
    return base_host == target_host or base_host.endswith(target_host) or target_host.endswith(base_host)


def _clean_title(text: str) -> str:
    title = re.sub(r"\s+", " ", text).strip(" -|,")
    return title


def _is_job_link(href: str, text: str) -> bool:
    if not href or href.startswith("#") or href.startswith("mailto:"):
        return False
    if href.lower().endswith(SKIP_EXTENSIONS):
        return False

    haystack = f"{href} {text}".lower()
    return bool(re.search(JOB_LINK_PATTERN, haystack, re.I))


def parse_jobs_from_career_page(html: str, career_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if not href:
            continue

        absolute_url = urljoin(career_url, href)
        title = _clean_title(anchor.get_text(" ", strip=True))

        if len(title) < MIN_TITLE_LEN or len(title) > MAX_TITLE_LEN:
            continue
        if not _is_job_link(absolute_url, title):
            continue
        if not _same_domain(career_url, absolute_url):
            continue

        normalized = absolute_url.split("#")[0].rstrip("/")
        if normalized in seen_urls:
            continue

        seen_urls.add(normalized)
        jobs.append(
            {
                "title": title,
                "url": normalized,
                "location": None,
                "description": None,
                "source": "career_page",
            }
        )

    return jobs


def scrape_company_jobs(company: dict) -> list[dict]:
    career_url = company["career_url"]
    html = fetch_html(career_url)
    return parse_jobs_from_career_page(html, career_url)


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
                print(f"[empty] {company['name']}: no job links on career page HTML")
        except Exception as exc:
            print(f"[error] {company['name']}: {exc}")

    return stats
