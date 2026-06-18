"""Browser-based scraping for JavaScript career sites (Workday, Taleo, etc.)."""

from configs.settings import REQUEST_HEADERS
from scrapers.careers.job_parser import career_search_urls, parse_jobs_from_html

WORKDAY_JOB_SELECTORS = (
    'a[data-automation-id="jobTitle"]',
    '[data-automation-id="jobTitle"]',
    'a[data-automation-id="jobPostingTitle"]',
    ".job-search-results-list",
    "li[data-automation-id='compositeContainer']",
)

CONSENT_BUTTON_SELECTORS = (
    'button:has-text("Accept")',
    'button:has-text("Accept All")',
    'button:has-text("I Accept")',
    'button:has-text("Agree")',
    '[data-automation-id="legalAcceptButton"]',
)


def _browser_context(playwright):
    user_agent = REQUEST_HEADERS.get("User-Agent")
    return playwright.chromium.launch(headless=True).new_context(
        user_agent=user_agent,
        viewport={"width": 1366, "height": 900},
        locale="en-IN",
    )


def _dismiss_consent(page) -> None:
    for selector in CONSENT_BUTTON_SELECTORS:
        try:
            button = page.locator(selector).first
            if button.is_visible(timeout=1_500):
                button.click(timeout=2_000)
                page.wait_for_timeout(500)
                return
        except Exception:
            continue


def _wait_for_jobs(page) -> None:
    for selector in WORKDAY_JOB_SELECTORS:
        try:
            page.wait_for_selector(selector, timeout=12_000)
            return
        except Exception:
            continue
    page.wait_for_timeout(4_000)


def _scroll_results(page) -> None:
    for _ in range(3):
        page.evaluate("window.scrollBy(0, window.innerHeight)")
        page.wait_for_timeout(800)


def fetch_rendered_html(url: str) -> tuple[str, str]:
    """Return (html, final_page_url) after JavaScript renders."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        context = _browser_context(playwright)
        page = context.new_page()
        page.set_default_timeout(60_000)

        page.goto(url, wait_until="domcontentloaded")
        _dismiss_consent(page)
        _wait_for_jobs(page)
        _scroll_results(page)

        html = page.content()
        final_url = page.url
        context.close()
        return html, final_url


def scrape_with_playwright(career_url: str) -> list[dict]:
    urls_to_try = [career_url, *career_search_urls(career_url)]
    seen: set[str] = set()
    all_jobs: list[dict] = []

    for url in urls_to_try:
        try:
            html, page_url = fetch_rendered_html(url)
            jobs = parse_jobs_from_html(html, page_url)
            for job in jobs:
                if job["url"] not in seen:
                    seen.add(job["url"])
                    all_jobs.append(job)
            if all_jobs:
                break
        except Exception as exc:
            print(f"[playwright] skip {url}: {exc}")
            continue

    return all_jobs
