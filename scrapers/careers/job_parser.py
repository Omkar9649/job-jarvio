"""Shared job link parsing for static HTML and Playwright-rendered pages."""

import re
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from configs.settings import JOB_LINK_PATTERN

SKIP_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".css", ".js")
MIN_TITLE_LEN = 8
MAX_TITLE_LEN = 180

STRONG_JOB_URL_PATTERN = re.compile(
    r"(/job[s]?/|requisition|reqid|req-id|jobdetail|job-detail|/opening[s]?/|"
    r"/vacancy/|/position[s]?/|/go/|/opportunity/|jobid=|job_id=)",
    re.I,
)

NOISE_URL_PARTS = (
    "locale=",
    "/content/",
    "/talentcommunity/",
    "fraud-awareness",
    "life-at-",
    "early-career",
    "experienced-professional",
    "/privacy",
    "/cookie",
)

NOISE_TITLE_PARTS = (
    "skip to main",
    "join our talent network",
    "fraud awareness",
    "life at ",
    "early career",
    "experienced professional",
    "please visit our job search",
    "accessible format",
)

LOCALE_TITLE_PATTERN = re.compile(r"^[\w\s\-'.()]+\([\w\s\-'.]+\)$")

# Career pages often redirect to a third-party ATS (Workday, Greenhouse, etc.)
ATS_HOST_SUFFIXES = (
    ".myworkdayjobs.com",
    ".myworkdaysite.com",
    "greenhouse.io",
    "lever.co",
    "taleo.net",
    "icims.com",
    "smartrecruiters.com",
    "jobvite.com",
)


def is_ats_host(host: str) -> bool:
    lowered = host.lower()
    return any(suffix in lowered for suffix in ATS_HOST_SUFFIXES)


def same_domain(base_url: str, target_url: str) -> bool:
    base_host = urlparse(base_url).netloc.removeprefix("www.")
    target_host = urlparse(target_url).netloc.removeprefix("www.")
    if not target_host:
        return True
    if is_ats_host(target_host):
        return True
    return base_host == target_host or base_host.endswith(target_host) or target_host.endswith(base_host)


def clean_title(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" -|,")


def is_noise_link(url: str, title: str) -> bool:
    lowered_url = url.lower()
    lowered_title = title.lower()

    if any(part in lowered_url for part in NOISE_URL_PARTS):
        return True
    if any(part in lowered_title for part in NOISE_TITLE_PARTS):
        return True
    if LOCALE_TITLE_PATTERN.match(title) and "locale=" in lowered_url:
        return True

    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    if path in ("/", "/search") and not STRONG_JOB_URL_PATTERN.search(url):
        return True

    query = parse_qs(parsed.query)
    if set(query.keys()) <= {"locale"}:
        return True

    return False


def is_job_link(href: str, text: str) -> bool:
    if not href or href.startswith("#") or href.startswith("mailto:"):
        return False
    if href.lower().endswith(SKIP_EXTENSIONS):
        return False

    if not STRONG_JOB_URL_PATTERN.search(href):
        return False

    haystack = f"{href} {text}".lower()
    return bool(re.search(JOB_LINK_PATTERN, haystack, re.I))


def parse_jobs_from_html(html: str, page_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    # Workday / Oracle Taleo ATS — job titles after JavaScript renders
    for anchor in soup.select(
        'a[data-automation-id="jobTitle"], '
        'a[data-automation-id="jobPostingTitle"], '
        'a.jobTitle-link'
    ):
        href = anchor.get("href", "").strip()
        if not href:
            continue
        absolute_url = urljoin(page_url, href)
        title = clean_title(anchor.get_text(" ", strip=True))
        location = _find_workday_location(anchor)
        job = _build_job(page_url, absolute_url, title, location, seen_urls)
        if job:
            jobs.append(job)

    # Generic anchor scan
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if not href:
            continue

        absolute_url = urljoin(page_url, href)
        title = clean_title(anchor.get_text(" ", strip=True))

        if len(title) < MIN_TITLE_LEN or len(title) > MAX_TITLE_LEN:
            continue
        if is_noise_link(absolute_url, title):
            continue
        if not is_job_link(absolute_url, title):
            continue
        if not same_domain(page_url, absolute_url):
            continue

        job = _build_job(page_url, absolute_url, title, None, seen_urls)
        if job:
            jobs.append(job)

    return jobs


def _find_workday_location(title_anchor) -> str | None:
    row = title_anchor.find_parent("li") or title_anchor.find_parent("tr")
    if not row:
        return None
    loc_el = row.select_one(
        '[data-automation-id="jobLocation"], '
        '[data-automation-id="locations"], '
        ".jobLocation"
    )
    if loc_el:
        return clean_title(loc_el.get_text(" ", strip=True))
    return None


def _build_job(
    page_url: str,
    absolute_url: str,
    title: str,
    location: str | None,
    seen_urls: set[str],
) -> dict | None:
    if len(title) < MIN_TITLE_LEN or len(title) > MAX_TITLE_LEN:
        return None
    if is_noise_link(absolute_url, title):
        return None
    if not same_domain(page_url, absolute_url):
        return None

    normalized = absolute_url.split("#")[0].rstrip("/")
    if normalized in seen_urls:
        return None

    seen_urls.add(normalized)
    return {
        "title": title,
        "url": normalized,
        "location": location,
        "description": None,
        "source": "career_page",
    }


def career_search_urls(career_url: str) -> list[str]:
    base = career_url.rstrip("/")
    host = urlparse(career_url).netloc.lower()

    urls = [
        f"{base}/search/?locationsearch=India",
        f"{base}/search?locationsearch=India",
        f"{base}/jobs/search",
        f"{base}/jobs",
    ]

    if "careers.mphasis.com" in host:
        urls.extend(
            [
                f"{base}/home/hot-jobs/location-search/india.html",
                f"{base}/home/hot-jobs/skill-search.html",
            ]
        )

    if "myworkdayjobs.com" in host:
        urls.insert(0, f"{base}/jobs")

    return urls
