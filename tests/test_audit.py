from tools.audit import audit_app, status_markdown
from tools.checks import Gap
from tools.registry import parse

BASE = {"id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "demo",
        "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "license": "MIT",
        "languages": ["en", "da"], "fdroid": "none", "apk_asset": "Demo.apk"}
SECRET = {"id": "secret", "name": {"en": "Secret", "da": "Secret"}, "private": True}


def test_private_app_shows_name_only(tmp_path):
    apps = parse({"apps": [BASE, SECRET]})
    md = status_markdown(apps, {"demo": [Gap("demo", "site", "no sitemap.xml")]}, "2026-10-06")
    secret_line = next(line for line in md.splitlines() if "Secret" in line)
    assert "private" in secret_line and "dk.cocode" not in secret_line
    assert audit_app(apps[1], lambda url: (200, ""), tmp_path) == []


def test_status_lists_each_app_with_gap_count_and_gaps():
    apps = parse({"apps": [BASE]})
    md = status_markdown(apps, {"demo": [Gap("demo", "site", "no sitemap.xml")]}, "2026-10-06")
    assert "| Demo |" in md and "| 1 |" in md and "no sitemap.xml" in md and "2026-10-06" in md


def test_audit_app_collects_web_and_repo_gaps(tmp_path):
    app = parse({"apps": [BASE]})[0]
    gaps = audit_app(app, lambda url: (0, ""), tmp_path)
    areas = {g.area for g in gaps}
    assert {"site", "release", "repo", "cocode.dk"} <= areas


def _cli(monkeypatch, tmp_path):
    from tools import audit
    monkeypatch.setattr(audit, "load", lambda: parse({"apps": [BASE, SECRET]}))
    monkeypatch.setattr(audit, "real_fetch", lambda url: (0, ""))
    monkeypatch.setattr(audit, "PROJECTS", tmp_path / "projects")
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "_today", lambda: "2026-10-06")
    return audit


def test_main_all_prints_gaps_and_writes_status(monkeypatch, tmp_path, capsys):
    audit = _cli(monkeypatch, tmp_path)
    assert audit.main(["all"]) == 0
    out = capsys.readouterr().out
    assert "demo:" in out and "secret" in out
    status = (tmp_path / "STATUS.md").read_text("utf-8")
    assert "(2026-10-06)" in status and "| Demo |" in status and "| Secret | private |" in status


def test_main_one_app_prints_and_writes_no_status(monkeypatch, tmp_path, capsys):
    audit = _cli(monkeypatch, tmp_path)
    assert audit.main(["demo"]) == 0
    assert "demo:" in capsys.readouterr().out
    assert not (tmp_path / "STATUS.md").exists()


def test_today_is_the_local_date(monkeypatch):
    import time

    from tools import audit
    monkeypatch.setenv("TZ", "Pacific/Kiritimati")  # UTC+14: ahead of the UTC date for 14 hours a day
    time.tzset()
    try:
        assert audit._today() == time.strftime("%Y-%m-%d")
    finally:
        monkeypatch.delenv("TZ")
        time.tzset()
