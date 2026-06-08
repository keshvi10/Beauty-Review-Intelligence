"""Shared helpers and contract for platform scrapers.

Each scraper is a best-effort, server-side fetcher that respects the target
site's robots.txt. Live retail sites employ heavy anti-bot/JS protections, so
every scraper degrades gracefully to an "unavailable" result instead of
crashing or returning fabricated data when it cannot retrieve real reviews.
"""
import urllib.robotparser
from urllib.parse import urlparse

import requests

USER_AGENT = "BeautyReviewIntelligenceBot/1.0 (+anonymous research tool; respects robots.txt)"

REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 8

_robots_cache = {}


def is_allowed_by_robots(url: str) -> bool:
    """Check robots.txt for the target URL before fetching it."""
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    parser = _robots_cache.get(origin)
    if parser is None:
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(f"{origin}/robots.txt")
        try:
            parser.read()
        except Exception:
            # If robots.txt can't be fetched, default to disallowing the scrape.
            parser = False
        _robots_cache[origin] = parser

    if parser is False:
        return False
    return parser.can_fetch(USER_AGENT, url)


def safe_get(url: str):
    """Fetch a URL only if robots.txt allows it. Returns response or None."""
    if not is_allowed_by_robots(url):
        return None
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            return None
        return response
    except requests.RequestException:
        return None


def unavailable_result(platform: str, reason: str = "Data unavailable for this platform"):
    return {
        "platform": platform,
        "status": "unavailable",
        "message": reason,
        "rating": None,
        "review_count": 0,
        "reviews": [],
    }


def ok_result(platform: str, rating, review_count: int, reviews: list):
    return {
        "platform": platform,
        "status": "ok",
        "message": None,
        "rating": rating,
        "review_count": review_count,
        "reviews": reviews,
    }
