import re
import secrets
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import analytics
from keywords import top_keywords
from scrapers import PLATFORM_SCRAPERS
from sentiment import analyze_reviews

FRONTEND_DIR = "../frontend"

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

# Rate limiting keeps state in memory only (no IP addresses are persisted to
# disk or any database) and exists solely to deter automated abuse.
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)

PRODUCT_NAME_RE = re.compile(r"^[a-zA-Z0-9\s&+\-.,'%/]{1,120}$")

# Light synonym map so common shorthand still finds the right product (fuzzy search).
BRAND_SYNONYMS = {
    "minimalist": "minimalist",
    "mcaffeine": "mCaffeine",
    "mamaearth": "Mamaearth",
    "the ordinary": "The Ordinary",
    "ple": "Plum",
}


def sanitize_product_query(raw_query: str) -> str:
    """Strip whitespace and reject anything that isn't a plausible product name.

    Returns the cleaned string, or an empty string if the input is invalid.
    This blocks injection-style payloads (HTML/script tags, SQL meta-characters,
    shell separators, etc.) before the value ever reaches a scraper or log.
    """
    if not isinstance(raw_query, str):
        return ""
    cleaned = raw_query.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned or not PRODUCT_NAME_RE.match(cleaned):
        return ""
    return cleaned


def fuzzy_normalize(query: str) -> str:
    """Expand well-known shorthand/brand names so search results stay relevant."""
    lowered = query.lower()
    for shorthand, canonical in BRAND_SYNONYMS.items():
        if shorthand in lowered:
            lowered = lowered.replace(shorthand, canonical.lower())
    return lowered


def build_platform_card(platform: str, raw_result: dict) -> dict:
    if raw_result["status"] != "ok":
        return {
            "platform": platform,
            "status": "unavailable",
            "message": raw_result["message"] or "Data unavailable for this platform",
            "rating": None,
            "review_count": 0,
            "sentiment": None,
            "keywords": [],
        }

    reviews = raw_result["reviews"]
    return {
        "platform": platform,
        "status": "ok",
        "message": None,
        "rating": raw_result["rating"],
        "review_count": raw_result["review_count"],
        "sentiment": analyze_reviews(reviews),
        "keywords": top_keywords(reviews),
    }


def pick_best_platform(cards: list) -> dict | None:
    candidates = [c for c in cards if c["status"] == "ok" and c["rating"] is not None and c["sentiment"]]
    if not candidates:
        return None

    def score(card):
        return (card["rating"] or 0) * 20 + (card["sentiment"]["positive"] or 0)

    best = max(candidates, key=score)
    return {
        "platform": best["platform"],
        "reason": (
            f"Highest overall rating ({best['rating']}/5) and "
            f"strongest positive sentiment ({best['sentiment']['positive']}%) among available platforms."
        ),
    }


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.route("/api/search")
@limiter.limit("10 per hour")
def search():
    raw_query = request.args.get("product", "")
    product_query = sanitize_product_query(raw_query)
    if not product_query:
        return jsonify({"error": "Please enter a valid product name (letters, numbers, spaces only)."}), 400

    # Anonymous, rotating per-request session token supplied by the frontend.
    # Never linked to identity and never combined with IP/user data.
    session_id = sanitize_product_query(request.args.get("session", "")) or secrets.token_hex(8)

    normalized_query = fuzzy_normalize(product_query)

    cards = []
    with ThreadPoolExecutor(max_workers=len(PLATFORM_SCRAPERS)) as executor:
        future_to_platform = {
            executor.submit(fetch, normalized_query): platform
            for platform, fetch in PLATFORM_SCRAPERS.items()
        }
        results = {}
        for future in as_completed(future_to_platform):
            platform = future_to_platform[future]
            try:
                results[platform] = future.result()
            except Exception:
                results[platform] = {"platform": platform, "status": "unavailable",
                                      "message": "Data unavailable for this platform",
                                      "rating": None, "review_count": 0, "reviews": []}

    for platform in PLATFORM_SCRAPERS:
        cards.append(build_platform_card(platform, results[platform]))

    analytics.record_search(product_query, session_id)
    for card in cards:
        if card["status"] == "ok":
            analytics.record_platform_view(card["platform"], session_id)

    return jsonify({
        "product": product_query,
        "platforms": cards,
        "recommendation": pick_best_platform(cards),
    })


@app.errorhandler(429)
def rate_limit_handler(_err):
    return jsonify({"error": "Search limit reached (10 per hour). Please try again later."}), 429


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
