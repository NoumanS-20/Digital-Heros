from fastapi.testclient import TestClient

from app import fetcher
from app.fetcher import AuditError, FetchResult
from app.main import app

client = TestClient(app)

SAMPLE_HTML = (
    "<html><head><title>Test Title Here</title></head>"
    "<body><h1>Hi</h1><p>" + "word " * 400 + "</p></body></html>"
)


def test_healthz():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_audit_happy_path(monkeypatch):
    monkeypatch.setattr(fetcher, "validate_url", lambda u: u)
    monkeypatch.setattr(
        fetcher, "fetch",
        lambda url: FetchResult(final_url=url, status_code=200,
                                elapsed_ms=120, html=SAMPLE_HTML),
    )
    r = client.post("/api/audit", json={"url": "https://example.com"})
    assert r.status_code == 200
    body = r.json()
    assert body["metrics"]["title"] == "Test Title Here"
    assert body["metrics"]["http_status"] == 200
    assert "overall" in body["score"]
    assert isinstance(body["fixes"], list)


def test_invalid_url_returns_422():
    r = client.post("/api/audit", json={"url": "   "})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_URL"


def test_blocked_scheme_returns_400():
    r = client.post("/api/audit", json={"url": "ftp://example.com/file"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "BLOCKED_SCHEME"


def test_non_html_returns_415(monkeypatch):
    monkeypatch.setattr(fetcher, "validate_url", lambda u: u)

    def boom(url):
        raise AuditError("NOT_HTML", 415, "Expected HTML")

    monkeypatch.setattr(fetcher, "fetch", boom)
    r = client.post("/api/audit", json={"url": "https://example.com/x.pdf"})
    assert r.status_code == 415
    assert r.json()["error"]["code"] == "NOT_HTML"


def test_timeout_returns_504(monkeypatch):
    monkeypatch.setattr(fetcher, "validate_url", lambda u: u)

    def boom(url):
        raise AuditError("TIMEOUT", 504, "too slow")

    monkeypatch.setattr(fetcher, "fetch", boom)
    r = client.post("/api/audit", json={"url": "https://slow.example"})
    assert r.status_code == 504
