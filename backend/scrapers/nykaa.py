from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from .base import ok_result, safe_get, unavailable_result

PLATFORM = "nykaa"
SEARCH_URL = "https://www.nykaa.com/search/result/?q={query}"


def fetch(product_query: str) -> dict:
    try:
        search_resp = safe_get(SEARCH_URL.format(query=quote_plus(product_query)))
        if search_resp is None:
            return unavailable_result(PLATFORM)

        soup = BeautifulSoup(search_resp.text, "html.parser")
        rating_el = soup.select_one('[class*="rating"]')
        review_els = soup.select('[class*="review"]')

        rating = _parse_rating(rating_el.get_text() if rating_el else None)
        reviews = [el.get_text(strip=True) for el in review_els if el.get_text(strip=True)][:25]
        review_count = len(reviews)

        if rating is None and review_count == 0:
            return unavailable_result(PLATFORM)

        return ok_result(PLATFORM, rating, review_count, reviews)
    except Exception:
        return unavailable_result(PLATFORM)


def _parse_rating(text):
    if not text:
        return None
    try:
        for token in text.replace(",", " ").split():
            value = float(token)
            if 0 <= value <= 5:
                return value
    except ValueError:
        return None
    return None
