# Beauty Review Intelligence

A secure, anonymous web app that compares beauty product reviews and sentiment
across Amazon, Nykaa, Myntra, Tira, and AJIO in a single dashboard.

## How it works

1. Type a product name (e.g. "minimalist vitamin c serum") and hit search.
2. The Flask backend fetches review data from all five platforms in parallel,
   server-side only — no credentials or API keys ever reach the browser.
3. Each platform's reviews are run through VADER sentiment analysis and a
   keyword extractor, then rendered as comparison cards with rating, a
   sentiment donut chart, and top keywords.
4. A simple recommendation highlights the platform with the best combination
   of rating and positive sentiment.

If a platform blocks scraping or has no matching product, its card shows
"Data unavailable for this platform" instead of crashing the page.

## Project layout

```
backend/
  app.py            Flask app, routes, rate limiting, sanitisation, recommendation logic
  scrapers/         One module per platform; each respects robots.txt and degrades gracefully
  sentiment.py      VADER-based positive/neutral/negative classification
  keywords.py       Lightweight keyword/phrase frequency extraction
  analytics.py      Anonymous Supabase analytics client (no-op if unconfigured)
frontend/
  index.html, style.css, app.js   Static dashboard UI (no framework, no build step)
supabase_schema.sql Anonymous analytics tables
```

## Running locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000 — the Flask app also serves the frontend.

## Privacy & security

- **No accounts, no personal data.** The app never asks for a name, email, or
  login, and stores no personal identifiers.
- **No IP storage.** Rate limiting (10 searches/hour/IP) is enforced with an
  in-memory counter that is never written to disk or any database.
- **Input sanitisation.** Product names are validated against an allow-list
  pattern (`backend/app.py: sanitize_product_query`) before being used in any
  request or log, blocking script/SQL/shell-injection style payloads.
- **Server-side scraping only.** All requests to Amazon/Nykaa/Myntra/Tira/AJIO
  happen from the backend; no API keys or scraping logic are exposed to the
  client.
- **robots.txt aware.** `backend/scrapers/base.py` checks each target site's
  robots.txt before issuing a request and refuses to scrape disallowed paths.
- **Security headers & HTTPS.** `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, and HSTS headers are set on every response; deploy behind
  HTTPS (Vercel/Railway provide this by default).
- **Anonymous analytics only.** Supabase tables (`supabase_schema.sql`) record
  aggregate, anonymised facts — total searches, searched product names,
  platform views, and a random per-tab session token — never identity or IP.

## Configuring analytics (optional)

1. Create a free Supabase project and run `supabase_schema.sql` in the SQL editor.
2. Copy `backend/.env.example` to `backend/.env` and fill in `SUPABASE_URL` /
   `SUPABASE_KEY` (use the anon/public key — analytics only ever *inserts*
   anonymised rows).
3. Without these variables set, the app runs normally and analytics calls are
   no-ops.

## Deployment notes

- Deploy the Flask app to Railway/Render/Vercel (Python runtime) behind HTTPS.
- Because Amazon/Nykaa/Myntra/Tira/AJIO actively guard against automated
  scraping with JavaScript rendering and bot-detection, live results may show
  "Data unavailable for this platform" in production. The scraping layer is
  isolated in `backend/scrapers/`, so a Playwright/Puppeteer-based fetcher (or
  an official partner API/data feed, where available) can be swapped in
  without changing the rest of the app.

---

Built by Keshvi Singhvi · Beauty Review Intelligence Tool · 2026
