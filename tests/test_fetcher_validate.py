import pytest

from app.fetcher import AuditError, validate_url


def test_valid_http_url_passes():
    assert validate_url("https://example.com/path") == "https://example.com/path"


def test_blank_url_raises_invalid():
    with pytest.raises(AuditError) as e:
        validate_url("   ")
    assert e.value.code == "INVALID_URL"
    assert e.value.http_status == 422


def test_non_http_scheme_blocked():
    with pytest.raises(AuditError) as e:
        validate_url("ftp://example.com/x")
    assert e.value.code == "BLOCKED_SCHEME"
    assert e.value.http_status == 400


def test_loopback_host_blocked():
    with pytest.raises(AuditError) as e:
        validate_url("http://127.0.0.1:8000/admin")
    assert e.value.code == "BLOCKED_HOST"


def test_private_host_blocked():
    with pytest.raises(AuditError) as e:
        validate_url("http://10.0.0.1/")
    assert e.value.code == "BLOCKED_HOST"
