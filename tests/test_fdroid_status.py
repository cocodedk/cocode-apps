import shutil

import yaml

from tools import fdroid_status
from tools.fdroid_status import refresh
from tools.registry import ROOT

WORKFLOW = ROOT / ".github" / "workflows" / "fdroid-status.yml"


def test_listed_app_turns_live_and_others_stay():
    data = {"apps": [
        {"id": "a", "applicationId": "dk.a", "fdroid": "mr:1"},
        {"id": "b", "applicationId": "dk.b", "fdroid": "none"},
        {"id": "p", "name": {"en": "P", "da": "P"}, "private": True},
    ]}
    fetch = lambda url: (200, "{}") if url.endswith("/dk.a") else (404, "")
    assert refresh(data, fetch) == ["a"]
    assert data["apps"][0]["fdroid"] == "live" and data["apps"][1]["fdroid"] == "none"


def test_live_app_is_never_downgraded_on_a_bad_answer():
    data = {"apps": [{"id": "a", "applicationId": "dk.a", "fdroid": "live"}]}
    assert refresh(data, lambda url: (0, "")) == [] and data["apps"][0]["fdroid"] == "live"


def test_private_and_live_apps_are_never_looked_up():
    data = {"apps": [
        {"id": "a", "applicationId": "dk.a", "fdroid": "live"},
        {"id": "p", "name": {"en": "P", "da": "P"}, "private": True},
    ]}
    calls = []
    refresh(data, lambda url: calls.append(url) or (200, ""))
    assert calls == []


def test_main_leaves_apps_yml_untouched_when_nothing_is_listed(tmp_path, monkeypatch):
    shutil.copy(ROOT / "apps.yml", tmp_path / "apps.yml")
    before = (tmp_path / "apps.yml").read_bytes()
    monkeypatch.setattr(fdroid_status, "ROOT", tmp_path)
    monkeypatch.setattr(fdroid_status, "real_fetch", lambda url: (404, ""))
    assert fdroid_status.main() == 0
    assert (tmp_path / "apps.yml").read_bytes() == before


def test_workflow_is_yaml_and_uses_the_fixed_branch():
    assert isinstance(yaml.safe_load(WORKFLOW.read_text("utf-8")), dict)
    assert "fdroid-status/refresh" in WORKFLOW.read_text("utf-8")
