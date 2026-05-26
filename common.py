from __future__ import annotations

import re
import time
from typing import Callable

import requests

from config import HEADERS, REQUEST_DELAY_SEC


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def sleep_between() -> None:
    time.sleep(REQUEST_DELAY_SEC)


def normalize_key(name: str) -> str:
    """მარტივი გასაღები შედარებისთვის (იგივე პროდუქტი სხვადასხვა წყაროში)."""
    s = name.lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s-ჰ]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:120]


def paginate(
    fetch_page: Callable[[int], list[dict]],
    *,
    max_pages: int,
    stop_on_empty: bool = True,
) -> list[dict]:
    rows: list[dict] = []
    for page in range(1, max_pages + 1):
        batch = fetch_page(page)
        if not batch:
            if stop_on_empty:
                break
            continue
        rows.extend(batch)
        sleep_between()
    return rows
