"""The app registry: apps.yml, validated into App objects."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ("repo", "checkout", "applicationId", "site", "license", "languages", "fdroid", "apk_asset")
FDROID = re.compile(r"^(live|none|mr:\d+)$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class App:
    id: str
    name_en: str
    name_da: str
    private: bool = False
    repo: str = ""
    checkout: str = ""
    application_id: str = ""
    site: str = ""
    site_dir: str = "website"
    default_language: str = "en"
    privacy: str | None = None
    license: str = ""
    languages: tuple[str, ...] = ()
    fdroid: str = "none"
    apk_asset: str = ""
    obtainium: bool = True

    @property
    def fdroid_live(self) -> bool:
        return self.fdroid == "live"

    @property
    def fdroid_url(self) -> str:
        return f"https://f-droid.org/packages/{self.application_id}/"

    @property
    def apk_url(self) -> str:
        return f"https://github.com/cocodedk/{self.repo}/releases/latest/download/{self.apk_asset}"

    def home(self, lang: str) -> str:
        return "/" if lang == self.default_language else f"/{lang}/"


def _app(raw: dict) -> App:
    app_id = raw.get("id", "")
    if not SLUG.match(app_id):
        raise RegistryError(f"bad id {app_id!r}")
    name = raw.get("name") or {}
    if not name.get("en") or not name.get("da"):
        raise RegistryError(f"{app_id}: name needs en and da")
    if raw.get("private"):
        extra = set(raw) - {"id", "name", "private"}
        if extra:
            raise RegistryError(f"{app_id}: a private app keeps only id and name, not {sorted(extra)}")
        return App(app_id, name["en"], name["da"], private=True)
    for field in REQUIRED:
        if field not in raw:
            raise RegistryError(f"{app_id}: missing {field}")
    if not FDROID.match(str(raw["fdroid"])):
        raise RegistryError(f"{app_id}: fdroid must be live, none or mr:<number>")
    for url_field in ("site", "privacy"):
        value = raw.get(url_field)
        if value and not str(value).startswith("https://"):
            raise RegistryError(f"{app_id}: {url_field} must start with https://")
    if not str(raw["apk_asset"]).endswith(".apk"):
        raise RegistryError(f"{app_id}: apk_asset must end with .apk")
    return App(
        app_id, name["en"], name["da"], False, raw["repo"], raw["checkout"], raw["applicationId"],
        raw["site"].rstrip("/"), raw.get("site_dir", "website"), raw.get("default_language", "en"),
        raw.get("privacy"), raw["license"], tuple(raw["languages"]), str(raw["fdroid"]),
        raw["apk_asset"], bool(raw.get("obtainium", True)),
    )


def parse(data: dict) -> list[App]:
    apps, seen = [], set()
    for raw in data.get("apps", []):
        app = _app(raw)
        if app.id in seen:
            raise RegistryError(f"duplicate id {app.id}")
        seen.add(app.id)
        apps.append(app)
    return apps


def load(path: Path = ROOT / "apps.yml") -> list[App]:
    return parse(yaml.safe_load(path.read_text("utf-8")) or {})


def find(apps: list[App], app_id: str) -> App:
    for app in apps:
        if app.id == app_id:
            return app
    raise RegistryError(f"unknown app {app_id!r}")
