import httpx
import pytest

from app import fetcher
from app.fetcher import AuditError, fetch


class FakeResp:
    def __init__(self, status=200, ctype="text/html; charset=utf-8",
                 content=b"<html></html>", url="https://x/", encoding="utf-8"):
        self.status_code = status
        self.headers = {"content-type": ctype}
        self.content = content
        self.url = url
        self.encoding = encoding


def test_fetch_happy_returns_result(monkeypatch):
    monkeypatch.setattr(fetcher.httpx, "get", lambda *a, **k: FakeResp())
    r = fetch("https://x/")
    assert r.status_code == 200
    assert r.html == "<html></html>"
    assert r.final_url == "https://x/"


def test_fetch_non_html_raises_415(monkeypatch):
    monkeypatch.setattr(fetcher.httpx, "get",
                        lambda *a, **k: FakeResp(ctype="application/pdf", content=b"%PDF"))
    with pytest.raises(AuditError) as e:
        fetch("https://x/f.pdf")
    assert e.value.http_status == 415
    assert e.value.code == "NOT_HTML"


def test_fetch_timeout_raises_504(monkeypatch):
    def boom(*a, **k):
        raise httpx.TimeoutException("t")
    monkeypatch.setattr(fetcher.httpx, "get", boom)
    with pytest.raises(AuditError) as e:
        fetch("https://x/")
    assert e.value.http_status == 504


def test_fetch_connect_error_raises_502(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("c")
    monkeypatch.setattr(fetcher.httpx, "get", boom)
    with pytest.raises(AuditError) as e:
        fetch("https://x/")
    assert e.value.http_status == 502
