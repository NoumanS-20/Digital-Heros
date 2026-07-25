# Page Pulse

A small web tool that audits any URL: it fetches the page and returns HTTP status,
response time, title, meta description, H1 count, images missing alt text, and an
approximate word count — plus an opinionated **0–100 health score** and a
**prioritized fix list**.

Built for the Digital Heroes SDE qualification task.

**Live demo:** <ADD YOUR RENDER URL HERE>

## Setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# open http://127.0.0.1:8000
```

Run the tests:

```bash
python -m pytest -v
```

## API contract

### `POST /api/audit`

Request body:
```json
{ "url": "https://example.com" }
```

Success `200`:
```json
{
  "final_url": "https://example.com/",
  "fetched_at": "2026-07-24T12:00:00+00:00",
  "metrics": {
    "http_status": 200, "response_time_ms": 340,
    "title": "Example Domain", "meta_description": "…",
    "h1_count": 1, "images_total": 12, "images_missing_alt": 3, "word_count": 512
  },
  "score": { "overall": 78, "grade": "B",
             "breakdown": { "seo": 80, "accessibility": 65, "performance": 90 } },
  "fixes": [
    { "severity": "high", "area": "accessibility",
      "message": "3 of 12 images are missing alt text — add descriptive alt attributes." }
  ]
}
```

Errors are always structured and never 500:

| Condition | HTTP | code |
|---|---|---|
| Missing / blank / hostless URL | 422 | `INVALID_URL` |
| Non-http(s) scheme | 400 | `BLOCKED_SCHEME` |
| Private / loopback / reserved host | 400 | `BLOCKED_HOST` |
| DNS / connection / TLS failure | 502 | `FETCH_FAILED` |
| Response slower than 10s | 504 | `TIMEOUT` |
| Reachable but not HTML | 415 | `NOT_HTML` |

```json
{ "error": { "code": "TIMEOUT", "message": "The page took longer than 10s to respond." } }
```

### `GET /` — the frontend.  `GET /healthz` — `{"status":"ok"}` (Render health check).

## Three design decisions

1. **Pure parsing/scoring split from I/O.** `auditor` and `scoring` are pure functions
   with no network dependency, so the opinionated logic is fast and deterministic to test;
   `fetcher` isolates the one risky module and is the only thing mocked in tests.

2. **Audit on any HTTP status.** A page that returns 404 but still serves HTML is audited
   and its status reported, rather than treated as a hard failure — the tool's job is to
   describe what a URL actually serves. Only network, timeout, and non-HTML responses abort.

3. **SSRF + size guards on by default.** A public tool that fetches arbitrary URLs is an
   SSRF vector, so the host is resolved and private/loopback/reserved ranges are rejected,
   and the response body is capped at 3 MB before parsing. Cheap insurance, real-world instinct.

## Scoring

SEO (weight 0.40): title 10–60 chars · meta description 50–160 chars · exactly one H1 ·
word count > 300. Accessibility (0.35): share of images with alt text. Performance (0.25):
response-time bands (<500ms=100, <1500=70, <3000=40, else 10). Overall = weighted blend;
grade A≥90 / B≥75 / C≥60 / D≥40 / F.

## Tech

Python 3.12 · FastAPI · httpx · BeautifulSoup (lxml) · pytest. Single service; FastAPI
serves both the JSON API and the static frontend.

## AI usage

_(fill in before submitting — see the note in the design spec)._
