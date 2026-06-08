from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from .base import ok_result, safe_get, unavailable_result

PLATFORM = "amazon"
SEARCH_URL = "https://www.amazon.in/s?k={query}"


def fetch(product_query: str) -> dict:
    try:
        search_resp = safe_get(SEARCH_URL.format(query=quote_plus(product_query)))
        if search_resp is None:
            return unavailable_result(PLATFORM)

        soup = BeautifulSoup(search_resp.text, "html.parser")
        result = soup.select_one("div.s-result-item[data-asin]:not([data-asin=''])")
        if result is None:
            return unavailable_result(PLATFORM, "No matching product found on Amazon")

        rating_el = result.select_one("span.a-icon-alt")
        review_count_el = result.select_one("span.a-size-base.s-underline-text")
        review_text_els = result.select("span.a-size-base") or []

        rating = _parse_rating(rating_el.get_text() if rating_el else None)
        review_count = _parse_count(review_count_el.get_text() if review_count_el else None)
        reviews = [el.get_text(strip=True) for el in review_text_els][:25]

        if rating is None and review_count == 0:
            return unavailable_result(PLATFORM)

        return ok_result(PLATFORM, rating, review_count, reviews)
    except Exception:
        return unavailable_result(PLATFORM)


def _parse_rating(text):
    if not text:
        return None
    try:
        return float(text.split(" ")[0])
    except (ValueError, IndexError):
        return None


def _parse_count(text):
    if not text:
        return 0
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 0
