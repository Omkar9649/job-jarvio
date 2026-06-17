import time

import requests

from configs.settings import REQUEST_DELAY_SECONDS, REQUEST_HEADERS, REQUEST_TIMEOUT


class FetchError(RuntimeError):
    pass


def fetch_html(url: str, delay: bool = True) -> str:
    if delay:
        time.sleep(REQUEST_DELAY_SECONDS)

    response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    html = response.text
    if "access denied" in html.lower():
        raise FetchError(f"Blocked while fetching: {url}")

    return html
