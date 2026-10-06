import http.client
import urllib.error
import urllib.request

import pytest

from tools.net import fetch


class FakeResponse:
    status = 200

    def __init__(self, body: str):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, size=-1):
        return self.body.encode("utf-8")


@pytest.mark.parametrize("error", [
    http.client.IncompleteRead(b""),
    http.client.BadStatusLine("x"),
    urllib.error.URLError("x"),
    TimeoutError(),
])
def test_fetch_turns_every_failure_into_no_answer(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    assert fetch("https://example.invalid/") == (0, "")


def test_fetch_returns_status_and_body(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: FakeResponse("hello"))
    assert fetch("https://example.invalid/") == (200, "hello")


def test_fetch_treats_a_malformed_url_as_no_answer():
    assert fetch("not a url") == (0, "")
