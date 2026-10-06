# cocode-apps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the cocode-apps project — registry, standard, templates, audit/render/F-Droid-status tools, the skill — and produce the first `STATUS.md` for all 16 Cocode Android apps.

**Architecture:** `apps.yml` holds app facts; `tools/registry.py` loads and validates it into `App` objects. Pure functions in `tools/blocks.py` turn an `App` into install/navigation/footer blocks; `tools/render.py` writes them between markers in app checkouts, and `tools/catalogue.py` writes each app's download link into the cocode.dk catalogue. `tools/checks/*` each test one area and return `Gap`s; `tools/audit.py` runs them and writes `STATUS.md`. All network access goes through one injectable `fetch`.

**Tech Stack:** Python 3.12+, PyYAML, pytest (offline), ruff when installed, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-06-cocode-apps-design.md` (read it first). Facts: `docs/audit-2026-10-06.md`.

## Global Constraints

- `apps.yml` is the single source of truth; no app fact is hard-coded in tools, templates or standard files.
- Private apps: only `id`, `name`, `private: true` in `apps.yml`; nothing else about them in this public repo.
- Runtime dependency: PyYAML only. Tests: pytest, offline; every network call goes through `fetch(url) -> (status, text)`; `tests/conftest.py` fails any test that opens a non-loopback socket.
- `audit.py` never changes an app repository. `render.py` changes only text between `<!-- cocode-apps:<block>:start -->` / `<!-- cocode-apps:<block>:end -->` markers; without markers it reports and changes nothing.
- Nothing is pushed to or merged in an app repository or cocode.dk without the owner's OK.
- Never name Spamhaus in install blocks, catalogue entries or store texts.
- English and Danish baseline for every app-facing text.
- Code files under 200 lines. Conventional Commits; end each commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never `--no-verify`.

## Review Focus

1. **A site that times out or answers 5xx** → its checks report one "site unreachable" gap each, never a crash, and the audit goes on with the next app (Task 5 test `unreachable_site_is_one_gap_not_a_crash`).
2. **An app checkout missing on disk** → repo-file checks report "checkout missing" once and skip the rest for that app (Task 6 test `missing_checkout_is_one_gap`).
3. **A private app** → audit, render and fdroid_status skip it entirely and STATUS.md shows only its name and "private" (Task 7 test `private_app_shows_name_only`).
4. **`gradle.properties` without a literal `VERSION_CODE`** → the fastlane check reports that gap instead of guessing the changelog file (Task 6 test `non_literal_version_code_is_a_gap`).
5. **A file with only a start marker or markers in the wrong order** → render reports "broken markers" and leaves the file unchanged (Task 4 test `broken_markers_change_nothing`).

## File structure

```
apps.yml                     registry (Task 2)
tools/__init__.py
tools/registry.py            App, load(), parse(), find()            (Task 2)
tools/net.py                 fetch() — the only network code          (Task 5)
tools/blocks.py              install/nav/footer/catalogue text        (Task 3)
tools/blocks_text.py         en/da labels used by blocks.py           (Task 3)
tools/render.py              replace_block(), apply(), CLI            (Task 4)
tools/catalogue.py           cocode.dk catalogue download links       (Task 4b)
tools/checks/__init__.py     Gap
tools/checks/web.py          site, privacy, release, F-Droid checks   (Task 5)
tools/checks/repo.py         README, fastlane, in-app checks          (Task 6)
tools/audit.py               run checks, write STATUS.md, CLI         (Task 7)
tools/fdroid_status.py       refresh F-Droid states in apps.yml       (Task 8)
templates/badges/            F-Droid badges en + da (PNG)             (Task 3)
templates/about-strings.md, templates/privacy-skeleton.html           (Task 9)
standard/*.md                the rulebook                             (Task 9)
skill/SKILL.md               the cocode-apps skill                    (Task 10)
.github/workflows/fdroid-status.yml                                   (Task 8)
scripts/gate.sh, pyproject.toml, requirements-dev.txt, README.md, LICENSE (Task 1)
tests/                       one test file per module
```

---

### Task 1: Scaffold and gate

**Files:** Create `pyproject.toml`, `requirements-dev.txt`, `scripts/gate.sh`, `.gitignore`, `README.md`, `LICENSE` (MIT, "Copyright (c) 2026 Babak Bandpey"), `tools/__init__.py` (empty), `tools/checks/__init__.py` (Task 5 fills it), `tests/conftest.py`, `tests/test_offline.py`.

- [ ] **Step 1: Write the offline guard and its test**

`tests/conftest.py`:
```python
import socket

import pytest

_real_connect = socket.socket.connect


def _guarded_connect(self, address):
    host = address[0] if isinstance(address, tuple) else address
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise RuntimeError(f"tests are offline: tried to reach {address!r}")
    return _real_connect(self, address)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)
```

`tests/test_offline.py`:
```python
import socket

import pytest


def test_non_loopback_socket_is_refused():
    with pytest.raises(RuntimeError, match="offline"):
        socket.create_connection(("192.0.2.1", 80), timeout=1)
```

- [ ] **Step 2: Gate files**

`pyproject.toml`:
```toml
[project]
name = "cocode-apps"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["PyYAML>=6"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 110
```
`requirements-dev.txt`: `PyYAML>=6` and `pytest>=8` on two lines.
`scripts/gate.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pytest -q
if command -v ruff >/dev/null 2>&1; then ruff check tools tests; fi
```
`.gitignore`: `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `scratchpad/`, `.zvec-grep/`, `memory/`.
`README.md`: three short paragraphs — what cocode-apps is (link the spec), the commands from `CLAUDE.md`, and "Private apps are listed by name only".

- [ ] **Step 3: Run the gate** — `python3 -m pip install --user -r requirements-dev.txt` if needed, then `bash scripts/gate.sh`. Expected: `1 passed`.
- [ ] **Step 4: Commit** — `git add -A && git commit -m "chore: scaffold cocode-apps with an offline test gate"`.

### Task 2: Registry (`apps.yml`, `tools/registry.py`)

**Files:** Create `tools/registry.py`, `apps.yml`; Test `tests/test_registry.py`.

**Interfaces — Produces:**
```python
@dataclass(frozen=True)
class App:
    id: str; name_en: str; name_da: str; private: bool = False
    repo: str = ""; checkout: str = ""; application_id: str = ""
    site: str = ""; site_dir: str = "website"; default_language: str = "en"
    privacy: str | None = None; license: str = ""; languages: tuple[str, ...] = ()
    fdroid: str = "none"; apk_asset: str = ""; obtainium: bool = True
    fdroid_live: bool  (property)   fdroid_url: str (property)   apk_url: str (property)
    home(lang: str) -> str    # "/" for default_language, "/<lang>/" otherwise
class RegistryError(ValueError)
def parse(data: dict) -> list[App]
def load(path: Path = ROOT / "apps.yml") -> list[App]
def find(apps: list[App], app_id: str) -> App          # raises RegistryError if unknown
ROOT: Path                                              # the repository root
```

- [ ] **Step 1: Write the failing tests**

```python
import pytest

from tools.registry import RegistryError, find, parse

PUBLIC = {
    "id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "demo-android",
    "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "site_dir": "website",
    "default_language": "da", "privacy": "https://demo.cocode.dk/privacy/", "license": "Apache-2.0",
    "languages": ["en", "da"], "fdroid": "mr:123", "apk_asset": "Demo.apk",
}


def one(**over):
    return parse({"apps": [{**PUBLIC, **over}]})[0]


def test_public_app_parses_with_derived_urls():
    app = one()
    assert app.application_id == "dk.cocode.demo"
    assert app.fdroid_url == "https://f-droid.org/packages/dk.cocode.demo/"
    assert app.apk_url == "https://github.com/cocodedk/demo-android/releases/latest/download/Demo.apk"
    assert not app.fdroid_live and one(fdroid="live").fdroid_live


def test_home_paths_follow_default_language():
    app = one()
    assert app.home("da") == "/" and app.home("en") == "/en/"


def test_private_app_keeps_name_only():
    app = parse({"apps": [{"id": "secret", "name": {"en": "S", "da": "S"}, "private": True}]})[0]
    assert app.private and app.repo == ""


def test_private_app_with_details_is_rejected():
    with pytest.raises(RegistryError, match="private"):
        parse({"apps": [{"id": "secret", "name": {"en": "S", "da": "S"}, "private": True, "repo": "x"}]})


@pytest.mark.parametrize("field", ["repo", "checkout", "applicationId", "site", "license", "fdroid", "apk_asset"])
def test_missing_required_field_is_rejected(field):
    data = {**PUBLIC}
    del data[field]
    with pytest.raises(RegistryError, match=field):
        parse({"apps": [data]})


@pytest.mark.parametrize("value", ["published", "mr:", "mr:abc", "LIVE"])
def test_bad_fdroid_value_is_rejected(value):
    with pytest.raises(RegistryError, match="fdroid"):
        one(fdroid=value)


def test_duplicate_ids_are_rejected():
    with pytest.raises(RegistryError, match="duplicate"):
        parse({"apps": [PUBLIC, PUBLIC]})


def test_non_https_site_and_non_apk_asset_are_rejected():
    with pytest.raises(RegistryError, match="https"):
        one(site="http://demo.cocode.dk")
    with pytest.raises(RegistryError, match=".apk"):
        one(apk_asset="Demo.zip")


def test_find_unknown_app_raises():
    with pytest.raises(RegistryError, match="unknown"):
        find([one()], "nope")


def test_shipped_registry_loads():
    from tools.registry import load
    apps = load()
    assert len(apps) == 16
    assert sum(a.private for a in apps) == 1
```

- [ ] **Step 2: Run** `python3 -m pytest tests/test_registry.py -q` → FAIL (`ModuleNotFoundError: tools.registry`).

- [ ] **Step 3: Implement `tools/registry.py`**

```python
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
```

- [ ] **Step 4: Write `apps.yml`** with all 16 apps from `docs/audit-2026-10-06.md`. Rules: `privacy` is the live URL (`<site>/privacy.html` where the audit says privacy.html, `<site>/privacy/` for guard-android, omitted where none); `fdroid` is `live`, `mr:<number>` or `none` as in the audit; `site_dir` is `docs` for LinkQRWallet, persian-calendar and tms-measurement-app, `website` otherwise; `default_language` is `da` for guard-android, `en` otherwise; `languages` from the audit where known (guard-android `[en, da]`, BabakPlayer `[en, fa]`, tms-measurement-app `[en, ar, fa, zh]`), `[en]` elsewhere; `checkout` per the audit's folder exceptions (`Calendar`, `TMSMeasurement`, `measure-app`, `markdown-viewer`). exercise-log is private: `id`, `name` (en and da "Exercise Log"), `private: true` only. Keep the file free of comments (Task 8 rewrites it with `yaml.safe_dump`). Example entry:

```yaml
apps:
  - id: guard-android
    name: {en: Guard for Android, da: Guard for Android}
    repo: guard-android
    checkout: guard-android
    applicationId: dk.cocode.guard
    site: https://android.guard.cocode.dk
    site_dir: website
    default_language: da
    privacy: https://android.guard.cocode.dk/privacy/
    license: GPL-3.0-or-later
    languages: [en, da]
    fdroid: none
    apk_asset: GuardAndroid.apk
```

- [ ] **Step 5: Run** `python3 -m pytest tests/test_registry.py -q` → all PASS.
- [ ] **Step 6: Commit** — `git add tools/registry.py apps.yml tests/test_registry.py && git commit -m "feat: app registry with validation and all 16 apps"`.

### Task 3: Blocks (install, navigation, footer, catalogue link)

**Files:** Create `tools/blocks_text.py`, `tools/blocks.py`, `templates/badges/get-it-on-fdroid-en.png`, `templates/badges/get-it-on-fdroid-da.png`, `templates/badges/README.md`; Test `tests/test_blocks.py`.

**Interfaces — Consumes:** `App` (Task 2). **Produces:**
```python
def install_html(app: App, lang: str) -> str
def install_md(app: App, lang: str) -> str
def nav_html(app: App, lang: str) -> str
def footer_html(app: App, lang: str) -> str
def catalogue_link(app: App) -> str          # F-Droid URL when live, else the APK URL
BADGE_FILE = "img/get-it-on-fdroid-{lang}.png"  # path inside the site dir
```

- [ ] **Step 1: Badges** — download the official badges once: `curl -fsSL -o templates/badges/get-it-on-fdroid-en.png https://fdroid.gitlab.io/artwork/badge/get-it-on.png` and the Danish one from `https://fdroid.gitlab.io/artwork/badge/get-it-on-da.png` (if that URL is not 200, copy the English file and note it). `templates/badges/README.md`: source URLs and "F-Droid badge artwork; served from each site so visitors contact no third party".

- [ ] **Step 2: Write the failing tests**

```python
from tools.blocks import catalogue_link, footer_html, install_html, install_md, nav_html
from tools.registry import parse

BASE = {"id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "d",
        "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "default_language": "da",
        "license": "MIT", "languages": ["en", "da"], "fdroid": "none", "apk_asset": "Demo.apk"}


def app(**over):
    return parse({"apps": [{**BASE, **over}]})[0]


def test_live_app_links_the_fdroid_badge_first():
    html = install_html(app(fdroid="live"), "en")
    assert html.index("f-droid.org/packages/dk.cocode.demo/") < html.index("releases/latest/download/Demo.apk")
    assert 'src="/img/get-it-on-fdroid-en.png"' in html and 'alt="Get it on F-Droid"' in html


def test_app_not_on_fdroid_has_no_dead_badge_link():
    html = install_html(app(fdroid="mr:5"), "da")
    assert "f-droid.org/packages" not in html and "Kommer på F-Droid" in html


def test_obtainium_link_points_at_the_repo():
    assert "obtainium://add/https://github.com/cocodedk/demo-android" in install_html(app(), "en")
    assert "Obtainium" not in install_html(app(obtainium=False), "en")


def test_markdown_block_mirrors_html_order():
    md = install_md(app(fdroid="live"), "en")
    assert md.index("f-droid.org") < md.index("Demo.apk")


def test_nav_has_six_items_in_order_with_language_paths():
    html = nav_html(app(), "en")
    order = ["Demo", "How it works", "Install", "Privacy", "Dansk", "More apps"]
    positions = [html.index(label) for label in order]
    assert positions == sorted(positions)
    assert 'href="/en/privacy/"' in html and 'href="/"' in html and 'lang="da"' in html


def test_footer_names_source_license_and_cocode():
    html = footer_html(app(), "da")
    assert "github.com/cocodedk/demo-android" in html and "MIT" in html and "cocode.dk" in html


def test_catalogue_link_prefers_fdroid_when_live():
    assert catalogue_link(app(fdroid="live")).startswith("https://f-droid.org/packages/")
    assert catalogue_link(app()).endswith("/Demo.apk")
```

- [ ] **Step 3: Run** → FAIL (no module).

- [ ] **Step 4: Implement** `tools/blocks_text.py` (labels) and `tools/blocks.py`.

`tools/blocks_text.py`:
```python
"""Every label the shared blocks use, in English and Danish."""
TEXT = {
    "en": {"badge_alt": "Get it on F-Droid", "coming": "Coming to F-Droid",
           "apk": "Download the APK from GitHub", "obtainium": "Auto-update the GitHub APK with Obtainium",
           "how": "How it works", "install": "Install", "privacy": "Privacy", "more": "More apps",
           "skip": "Skip to content", "source": "Source code", "license": "License", "made": "Made by Cocode",
           "lang_name": "English"},
    "da": {"badge_alt": "Hent den på F-Droid", "coming": "Kommer på F-Droid",
           "apk": "Hent APK-filen fra GitHub", "obtainium": "Opdatér GitHub-APK'en automatisk med Obtainium",
           "how": "Sådan virker det", "install": "Installér", "privacy": "Privatliv", "more": "Flere apps",
           "skip": "Spring til indhold", "source": "Kildekode", "license": "Licens", "made": "Lavet af Cocode",
           "lang_name": "Dansk"},
}
CATALOGUE_URL = "https://cocode.dk/"
```

`tools/blocks.py`:
```python
"""The shared blocks, written from an App. Pure functions: no files, no network."""
from html import escape

from tools.blocks_text import CATALOGUE_URL, TEXT
from tools.registry import App

BADGE_FILE = "img/get-it-on-fdroid-{lang}.png"


def _other(app: App, lang: str) -> str:
    return "en" if lang == "da" else "da"


def _obtainium(app: App) -> str:
    return f"https://apps.obtainium.imranr.dev/redirect?r=obtainium://add/https://github.com/cocodedk/{app.repo}"


def install_html(app: App, lang: str) -> str:
    t = TEXT[lang]
    if app.fdroid_live:
        first = (f'<a class="fdroid" href="{app.fdroid_url}"><img src="/{BADGE_FILE.format(lang=lang)}" '
                 f'alt="{escape(t["badge_alt"])}" width="240" height="93"></a>')
    else:
        first = f'<p class="fdroid-soon">{escape(t["coming"])}</p>'
    items = [f"<li>{first}</li>", f'<li><a href="{app.apk_url}">{escape(t["apk"])}</a></li>']
    if app.obtainium:
        items.append(f'<li><a href="{escape(_obtainium(app))}">{escape(t["obtainium"])}</a></li>')
    return '<ul class="install" role="list">\n  ' + "\n  ".join(items) + "\n</ul>"


def install_md(app: App, lang: str) -> str:
    t = TEXT[lang]
    lines = []
    if app.fdroid_live:
        lines.append(f'[<img src="https://fdroid.gitlab.io/artwork/badge/get-it-on.png" alt="{t["badge_alt"]}" '
                     f'height="80">]({app.fdroid_url})')
    else:
        lines.append(f"- {t['coming']}")
    lines.append(f"- [{t['apk']}]({app.apk_url})")
    if app.obtainium:
        lines.append(f"- [{t['obtainium']}]({_obtainium(app)})")
    return "\n".join(lines)


def nav_html(app: App, lang: str) -> str:
    t, other = TEXT[lang], _other(app, lang)
    home = app.home(lang)
    name = app.name_en if lang == "en" else app.name_da
    return (
        f'<a class="skip" href="#main">{escape(t["skip"])}</a>\n'
        f'<nav class="cocode-nav" aria-label="{escape(name)}">\n'
        f'  <a class="brand" href="{home}">{escape(name)}</a>\n'
        f'  <a href="{home}#how">{escape(t["how"])}</a>\n'
        f'  <a href="{home}#install">{escape(t["install"])}</a>\n'
        f'  <a href="{home}privacy/">{escape(t["privacy"])}</a>\n'
        f'  <a href="{app.home(other)}" hreflang="{other}" lang="{other}">{escape(TEXT[other]["lang_name"])}</a>\n'
        f'  <a href="{CATALOGUE_URL}">{escape(t["more"])}</a>\n'
        "</nav>"
    )


def footer_html(app: App, lang: str) -> str:
    t, home = TEXT[lang], app.home(lang)
    return (
        '<footer class="cocode-footer">\n'
        f'  <a href="https://github.com/cocodedk/{app.repo}">{escape(t["source"])}</a> ·\n'
        f'  <a href="{home}privacy/">{escape(t["privacy"])}</a> ·\n'
        f'  {escape(t["license"])}: {escape(app.license)} ·\n'
        f'  <a href="{CATALOGUE_URL}">{escape(t["made"])} (cocode.dk)</a>\n'
        "</footer>"
    )


def catalogue_link(app: App) -> str:
    return app.fdroid_url if app.fdroid_live else app.apk_url
```

- [ ] **Step 5: Run** `python3 -m pytest tests/test_blocks.py -q` → PASS; `wc -l tools/blocks.py` < 200.
- [ ] **Step 6: Commit** — `git add tools/blocks*.py templates/badges tests/test_blocks.py && git commit -m "feat: shared install, navigation and footer blocks from the registry"`.

### Task 4: Render (`tools/render.py`)

**Files:** Create `tools/render.py`; Test `tests/test_render.py`.

**Interfaces — Consumes:** `App`, `load`, `find` (Task 2); `install_html`, `install_md`, `nav_html`, `footer_html`, `BADGE_FILE` (Task 3). **Produces:**
```python
START = "<!-- cocode-apps:{name}:start -->"; END = "<!-- cocode-apps:{name}:end -->"
def replace_block(text: str, name: str, content: str) -> tuple[str, str]   # (new_text, "ok"|"missing"|"broken")
def targets(app: App, root: Path) -> list[tuple[Path, str, str]]           # (file, block name, content)
def apply(app: App, root: Path, write: bool = True) -> list[str]           # report lines
```

- [ ] **Step 1: Write the failing tests**

```python
from tools.registry import parse
from tools.render import apply, replace_block

S, E = "<!-- cocode-apps:install:start -->", "<!-- cocode-apps:install:end -->"
BASE = {"id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "demo",
        "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "default_language": "da",
        "license": "MIT", "languages": ["en", "da"], "fdroid": "live", "apk_asset": "Demo.apk"}


def test_replaces_only_between_markers():
    text = f"before\n{S}\nold\n{E}\nafter"
    new, state = replace_block(text, "install", "NEW")
    assert state == "ok" and new == f"before\n{S}\nNEW\n{E}\nafter"


def test_missing_markers_change_nothing():
    assert replace_block("plain", "install", "NEW") == ("plain", "missing")


def test_broken_markers_change_nothing():
    for text in (f"{S} only", f"{E} then {S}"):
        assert replace_block(text, "install", "NEW") == (text, "broken")


def test_apply_writes_readme_and_site_and_copies_badges(tmp_path):
    app = parse({"apps": [BASE]})[0]
    (tmp_path / "README.md").write_text(f"# Demo\n{S}\n{E}\n")
    site = tmp_path / "website"
    (site / "en").mkdir(parents=True)
    for page in (site / "index.html", site / "en" / "index.html"):
        page.write_text(f"<main>{S}{E}</main>")
    report = apply(app, tmp_path)
    assert "f-droid.org/packages/dk.cocode.demo/" in (tmp_path / "README.md").read_text()
    assert "Hent den på F-Droid" in (site / "index.html").read_text()
    assert "Get it on F-Droid" in (site / "en" / "index.html").read_text()
    assert (site / "img" / "get-it-on-fdroid-da.png").is_file()
    assert any("missing" in line for line in report)  # nav/footer markers absent in this fixture


def test_dry_run_writes_nothing(tmp_path):
    app = parse({"apps": [BASE]})[0]
    (tmp_path / "README.md").write_text(f"{S}\n{E}")
    apply(app, tmp_path, write=False)
    assert (tmp_path / "README.md").read_text() == f"{S}\n{E}"
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement `tools/render.py`**

```python
"""Write the shared blocks into an app checkout, only between cocode-apps markers."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from tools.blocks import BADGE_FILE, footer_html, install_html, install_md, nav_html
from tools.registry import ROOT, App, find, load

START = "<!-- cocode-apps:{name}:start -->"
END = "<!-- cocode-apps:{name}:end -->"
PROJECTS = Path.home() / "0-projects"


def replace_block(text: str, name: str, content: str) -> tuple[str, str]:
    start, end = START.format(name=name), END.format(name=name)
    s, e = text.find(start), text.find(end)
    if s == -1 and e == -1:
        return text, "missing"
    if s == -1 or e == -1 or e < s or text.count(start) != 1 or text.count(end) != 1:
        return text, "broken"
    return text[: s + len(start)] + "\n" + content + "\n" + text[e:], "ok"


def _pages(app: App, root: Path) -> list[tuple[Path, str, bool]]:
    site = root / app.site_dir
    pages = []
    for lang in ("da", "en"):
        base = site if app.home(lang) == "/" else site / lang
        pages += [(base / "index.html", lang, True), (base / "privacy" / "index.html", lang, False)]
    return pages


def targets(app: App, root: Path) -> list[tuple[Path, str, str]]:
    out = [(root / "README.md", "install", install_md(app, "en"))]
    for page, lang, is_index in _pages(app, root):
        out += [(page, "nav", nav_html(app, lang)), (page, "footer", footer_html(app, lang))]
        if is_index:
            out.append((page, "install", install_html(app, lang)))
    return out


def apply(app: App, root: Path, write: bool = True) -> list[str]:
    report = []
    for path, block, content in targets(app, root):
        if not path.is_file():
            report.append(f"{path.relative_to(root)}: no such file")
            continue
        new, state = replace_block(path.read_text("utf-8"), block, content)
        report.append(f"{path.relative_to(root)} [{block}]: {state}")
        if write and state == "ok":
            path.write_text(new, "utf-8")
    if write and app.fdroid_live:
        for lang in ("en", "da"):
            dest = root / app.site_dir / BADGE_FILE.format(lang=lang)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "templates" / "badges" / f"get-it-on-fdroid-{lang}.png", dest)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write cocode-apps blocks into an app checkout.")
    parser.add_argument("app")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    app = find(load(), args.app)
    if app.private:
        print(f"{app.id}: private, skipped")
        return 0
    for line in apply(app, PROJECTS / app.checkout, write=not args.dry_run):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run** `python3 -m pytest tests/test_render.py -q` → PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat: render shared blocks between markers in an app checkout"` (add the new files first).

### Task 4b: Render the cocode.dk catalogue (`tools/catalogue.py`)

The owner asked for every app's F-Droid download link on cocode.dk; the spec says each catalogue entry
links to F-Droid when the app is live, to its GitHub APK until then, written from `apps.yml`. cocode.dk
is Danish only and lives in `~/0-projects/cocodedk`; its entries are in
`templates/partials/catalogue.html`, one `<li>` per app ending in
`<a class="index__link" href="<site>">…</a>`.

**Files:** Create `tools/catalogue.py`; Test `tests/test_catalogue.py`; Modify `tools/render.py` (a
`--catalogue` flag) and `tests/test_render.py`.

**Interfaces — Consumes:** `App`, `load` (Task 2); `catalogue_link` (Task 3); `replace_block` (Task 4); `Gap` (Task 5 — create `tools/checks/__init__.py` from Task 5 Step 3 now if it is still empty).
**Produces:**
```python
CATALOGUE_FILE = Path.home() / "0-projects/cocodedk/templates/partials/catalogue.html"
def catalogue_html(app: App) -> str          # the download link for one entry (Danish)
def apply_catalogue(apps: list[App], path: Path, write: bool = True) -> list[str]   # report lines
def check_catalogue(app: App, path: Path) -> list[Gap]                               # used by Task 7
```
Each public app's `<li>` carries a marker pair named `get-<id>` (for example
`<!-- cocode-apps:get-guard-android:start --><!-- cocode-apps:get-guard-android:end -->`) right after
its `index__link`. The markers are added once by hand in a cocodedk PR (with a CSS rule for
`.index__get` matching `.index__link`, and cocodedk's own tests run). That PR needs the owner's OK like
every other push; this task only writes the code that fills them.

- [ ] **Step 1: Write the failing tests** (`tests/test_catalogue.py`)

```python
from tools.catalogue import apply_catalogue, catalogue_html, check_catalogue
from tools.registry import parse

BASE = {"id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "demo",
        "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "license": "MIT",
        "languages": ["en", "da"], "fdroid": "live", "apk_asset": "Demo.apk"}
SECRET = {"id": "secret", "name": {"en": "S", "da": "S"}, "private": True}
S, E = "<!-- cocode-apps:get-demo:start -->", "<!-- cocode-apps:get-demo:end -->"


def apps(**over):
    return parse({"apps": [{**BASE, **over}, SECRET]})


def test_live_app_links_fdroid_in_danish():
    html = catalogue_html(apps()[0])
    assert 'href="https://f-droid.org/packages/dk.cocode.demo/"' in html and "Hent på F-Droid" in html


def test_app_not_on_fdroid_links_the_apk():
    html = catalogue_html(apps(fdroid="mr:3")[0])
    assert "releases/latest/download/Demo.apk" in html and "Hent APK" in html and "f-droid" not in html


def test_apply_fills_markers_and_skips_private_apps(tmp_path):
    page = tmp_path / "catalogue.html"
    page.write_text(f"<li>Demo {S}{E}</li>")
    report = apply_catalogue(apps(), page)
    assert "Hent på F-Droid" in page.read_text()
    assert not any("secret" in line for line in report)


def test_missing_marker_is_reported_and_is_an_audit_gap(tmp_path):
    page = tmp_path / "catalogue.html"
    page.write_text("<li>Demo</li>")
    assert any("missing" in line for line in apply_catalogue(apps(), page))
    assert "cocode.dk" in check_catalogue(apps()[0], page)[0].message
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement `tools/catalogue.py`**

```python
"""The download link in each cocode.dk catalogue entry, written from apps.yml (Danish site)."""
from html import escape
from pathlib import Path

from tools.blocks import catalogue_link
from tools.checks import Gap
from tools.registry import App
from tools.render import replace_block

CATALOGUE_FILE = Path.home() / "0-projects" / "cocodedk" / "templates" / "partials" / "catalogue.html"


def catalogue_html(app: App) -> str:
    label = "Hent på F-Droid" if app.fdroid_live else "Hent APK"
    return f'<a class="index__get" href="{escape(catalogue_link(app))}">{label}</a>'


def apply_catalogue(apps: list[App], path: Path, write: bool = True) -> list[str]:
    text, report = path.read_text("utf-8"), []
    for app in apps:
        if app.private:
            continue
        text, state = replace_block(text, f"get-{app.id}", catalogue_html(app))
        report.append(f"cocode.dk catalogue [{app.id}]: {state}")
    if write:
        path.write_text(text, "utf-8")
    return report


def check_catalogue(app: App, path: Path) -> list[Gap]:
    if app.private:
        return []
    if not path.is_file() or f"cocode-apps:get-{app.id}:start" not in path.read_text("utf-8"):
        return [Gap(app.id, "cocode.dk", "the cocode.dk catalogue entry has no download link (marker get-<id>)")]
    return []
```

- [ ] **Step 4: Wire the CLI** — in `tools/render.py` `main`, make `app` optional (`parser.add_argument("app", nargs="?")`) and add `parser.add_argument("--catalogue", action="store_true", help="fill the cocode.dk catalogue links")`. When `--catalogue` is set, import `tools.catalogue` inside `main` (avoids a circular import), print each line of `catalogue.apply_catalogue(load(), catalogue.CATALOGUE_FILE, write=not args.dry_run)`, and return 0. Add to `tests/test_render.py`:

```python
def test_catalogue_flag_needs_no_app(monkeypatch, tmp_path):
    import tools.catalogue as catalogue
    from tools.render import main
    page = tmp_path / "catalogue.html"
    page.write_text("<li></li>")
    monkeypatch.setattr(catalogue, "CATALOGUE_FILE", page)
    assert main(["--catalogue", "--dry-run"]) == 0
```

- [ ] **Step 5: Run** `python3 -m pytest tests/test_catalogue.py tests/test_render.py -q` → PASS.
- [ ] **Step 6: Commit** — `git add tools/catalogue.py tools/render.py tests/test_catalogue.py tests/test_render.py && git commit -m "feat: write each app's download link into the cocode.dk catalogue"`.

### Task 5: Network fetch and web checks (`tools/net.py`, `tools/checks/web.py`)

**Files:** Create `tools/net.py`, fill `tools/checks/__init__.py`, create `tools/checks/web.py`; Test `tests/test_checks_web.py`.

**Interfaces — Produces:**
```python
# tools/checks/__init__.py
@dataclass(frozen=True)
class Gap: app: str; area: str; message: str
Fetch = Callable[[str], tuple[int, str]]
# tools/net.py
def fetch(url: str, timeout: float = 20.0) -> tuple[int, str]    # (status, text); (0, "") on any error
# tools/checks/web.py
def check_site(app: App, fetch: Fetch) -> list[Gap]
def check_release(app: App, fetch: Fetch) -> list[Gap]
def check_fdroid(app: App, fetch: Fetch) -> list[Gap]
```

- [ ] **Step 1: Write the failing tests**

```python
from tools.checks.web import check_fdroid, check_release, check_site
from tools.registry import parse

BASE = {"id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "demo",
        "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "default_language": "da",
        "license": "MIT", "languages": ["en", "da"], "fdroid": "none", "apk_asset": "Demo.apk"}
GOOD_PAGE = ('<link rel="alternate" hreflang="en" href="x">'
             "<!-- cocode-apps:nav:start --><!-- cocode-apps:nav:end -->"
             "<!-- cocode-apps:install:start --><!-- cocode-apps:install:end -->"
             "<!-- cocode-apps:footer:start --><!-- cocode-apps:footer:end -->")


def app(**over):
    return parse({"apps": [{**BASE, **over}]})[0]


def site_fetch(pages):
    return lambda url: pages.get(url, (404, ""))


def test_complete_site_has_no_gaps():
    pages = {f"https://demo.cocode.dk{p}": (200, GOOD_PAGE) for p in ("/", "/en/", "/privacy/", "/en/privacy/")}
    pages["https://demo.cocode.dk/sitemap.xml"] = (200, "<urlset/>")
    assert check_site(app(), site_fetch(pages)) == []


def test_missing_privacy_and_markers_are_gaps():
    pages = {"https://demo.cocode.dk/": (200, "<html>no markers</html>")}
    messages = " | ".join(g.message for g in check_site(app(), site_fetch(pages)))
    assert "privacy" in messages and "install block" in messages and "navigation" in messages


def test_unreachable_site_is_one_gap_not_a_crash():
    gaps = check_site(app(), lambda url: (0, ""))
    assert len(gaps) == 1 and "unreachable" in gaps[0].message


def test_release_asset_must_download():
    assert check_release(app(), lambda url: (200, "")) == []
    assert "Demo.apk" in check_release(app(), lambda url: (404, ""))[0].message


def test_fdroid_state_must_match_fdroid_org():
    listed = lambda url: (200, "{}")  # noqa: E731
    assert "live" in check_fdroid(app(fdroid="mr:5"), listed)[0].message
    assert check_fdroid(app(fdroid="live"), listed) == []
    assert "not listed" in check_fdroid(app(fdroid="live"), lambda url: (404, ""))[0].message
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement**

`tools/checks/__init__.py`:
```python
"""A check returns Gaps: what an app lacks against the standard."""
from collections.abc import Callable
from dataclasses import dataclass

Fetch = Callable[[str], tuple[int, str]]


@dataclass(frozen=True)
class Gap:
    app: str
    area: str
    message: str
```

`tools/net.py`:
```python
"""The only code that touches the network. Tests never call it."""
import urllib.error
import urllib.request

AGENT = "cocode-apps-audit/0.1 (+https://github.com/cocodedk/cocode-apps)"


def fetch(url: str, timeout: float = 20.0) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(400_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, ""
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, ""
```

`tools/checks/web.py`:
```python
"""Checks against live URLs: site, privacy, release asset, F-Droid."""
from tools.checks import Fetch, Gap
from tools.registry import App

MARKERS = {"navigation": "cocode-apps:nav:start", "install block": "cocode-apps:install:start",
           "footer": "cocode-apps:footer:start"}


def check_site(app: App, fetch: Fetch) -> list[Gap]:
    def gap(message: str) -> Gap:
        return Gap(app.id, "site", message)

    status, home = fetch(app.site + "/")
    if status == 0 or status >= 500:
        return [gap(f"site unreachable ({app.site}, status {status})")]
    gaps = [] if status == 200 else [gap(f"home page answers {status}")]
    for label, marker in MARKERS.items():
        if marker not in home:
            gaps.append(gap(f"home page has no shared {label} (marker {marker})"))
    if "hreflang" not in home:
        gaps.append(gap("home page has no hreflang links"))
    for lang in ("da", "en"):
        url = app.site + app.home(lang) + "privacy/"
        if fetch(url)[0] != 200:
            gaps.append(gap(f"privacy page missing: {url}"))
    if fetch(app.site + "/sitemap.xml")[0] != 200:
        gaps.append(gap("no sitemap.xml"))
    return gaps


def check_release(app: App, fetch: Fetch) -> list[Gap]:
    status, _ = fetch(app.apk_url)
    return [] if status == 200 else [Gap(app.id, "release", f"{app.apk_asset} does not download (status {status})")]


def check_fdroid(app: App, fetch: Fetch) -> list[Gap]:
    status, _ = fetch(f"https://f-droid.org/api/v1/packages/{app.application_id}")
    if status == 200 and not app.fdroid_live:
        return [Gap(app.id, "fdroid", f"f-droid.org lists it: set fdroid to live (now {app.fdroid})")]
    if status != 200 and app.fdroid_live:
        return [Gap(app.id, "fdroid", "apps.yml says live but f-droid.org has not listed it")]
    return []
```

- [ ] **Step 4: Run** `python3 -m pytest tests/test_checks_web.py -q` → PASS.
- [ ] **Step 5: Commit** — `git add tools/net.py tools/checks tests/test_checks_web.py && git commit -m "feat: web checks for site, privacy, release and F-Droid state"`.

### Task 6: Repository checks (`tools/checks/repo.py`)

**Files:** Create `tools/checks/repo.py`; Test `tests/test_checks_repo.py`.

**Interfaces — Consumes:** `Gap` (Task 5), `App`. **Produces:**
```python
def check_readme(app: App, root: Path) -> list[Gap]
def check_fastlane(app: App, root: Path) -> list[Gap]
def check_inapp(app: App, root: Path) -> list[Gap]
def check_repo(app: App, root: Path) -> list[Gap]     # all three; one gap if root is missing
```

- [ ] **Step 1: Write the failing tests**

```python
from tools.checks.repo import check_fastlane, check_inapp, check_readme, check_repo
from tools.registry import parse

BASE = {"id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "demo",
        "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk",
        "privacy": "https://demo.cocode.dk/privacy/", "default_language": "da", "license": "MIT",
        "languages": ["en", "da"], "fdroid": "none", "apk_asset": "Demo.apk"}
APP = parse({"apps": [BASE]})[0]


def full_fastlane(root, code="1001"):
    (root / "gradle.properties").write_text(f"VERSION_NAME=0.1.0\nVERSION_CODE={code}\n")
    for loc in ("en-US", "da-DK"):
        d = root / "fastlane/metadata/android" / loc
        (d / "changelogs").mkdir(parents=True)
        for f in ("title.txt", "short_description.txt", "full_description.txt"):
            (d / f).write_text("x")
        (d / "changelogs" / f"{code}.txt").write_text("x")
    img = root / "fastlane/metadata/android/en-US/images"
    (img / "phoneScreenshots").mkdir(parents=True)
    for f in ("icon.png", "featureGraphic.png", "phoneScreenshots/1.png", "phoneScreenshots/2.png"):
        (img / f).write_bytes(b"png")


def test_complete_fastlane_has_no_gaps(tmp_path):
    full_fastlane(tmp_path)
    assert check_fastlane(APP, tmp_path) == []


def test_missing_danish_changelog_and_screenshots_are_gaps(tmp_path):
    full_fastlane(tmp_path)
    (tmp_path / "fastlane/metadata/android/da-DK/changelogs/1001.txt").unlink()
    for shot in (tmp_path / "fastlane/metadata/android/en-US/images/phoneScreenshots").iterdir():
        shot.unlink()
    messages = " | ".join(g.message for g in check_fastlane(APP, tmp_path))
    assert "da-DK" in messages and "screenshots" in messages


def test_non_literal_version_code_is_a_gap(tmp_path):
    full_fastlane(tmp_path)
    (tmp_path / "gradle.properties").write_text("VERSION_CODE=${CODE}\n")
    assert any("VERSION_CODE" in g.message for g in check_fastlane(APP, tmp_path))


def test_readme_needs_the_install_marker(tmp_path):
    (tmp_path / "README.md").write_text("# Demo")
    assert "install block" in check_readme(APP, tmp_path)[0].message


def test_inapp_needs_about_screen_privacy_link_and_both_languages(tmp_path):
    src = tmp_path / "app/src/main"
    (src / "java/dk/cocode/demo/ui").mkdir(parents=True)
    (src / "res/values").mkdir(parents=True)
    (src / "res/values/strings.xml").write_text("<resources/>")
    messages = " | ".join(g.message for g in check_inapp(APP, tmp_path))
    assert "About" in messages and "privacy" in messages and "values-en" in messages


def test_missing_checkout_is_one_gap(tmp_path):
    gaps = check_repo(APP, tmp_path / "nope")
    assert len(gaps) == 1 and "checkout missing" in gaps[0].message
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement `tools/checks/repo.py`**

```python
"""Checks against an app's local checkout: README, fastlane listing, in-app About and privacy link."""
import re
from pathlib import Path

from tools.checks import Gap
from tools.registry import App

LOCALES = ("en-US", "da-DK")
TEXTS = ("title.txt", "short_description.txt", "full_description.txt")


def check_readme(app: App, root: Path) -> list[Gap]:
    readme = root / "README.md"
    if not readme.is_file() or "cocode-apps:install:start" not in readme.read_text("utf-8"):
        return [Gap(app.id, "readme", "README has no shared install block (marker cocode-apps:install:start)")]
    return []


def _version_code(root: Path) -> str | None:
    props = root / "gradle.properties"
    if not props.is_file():
        return None
    match = re.search(r"^VERSION_CODE=(\d+)\s*$", props.read_text("utf-8"), re.M)
    return match.group(1) if match else None


def check_fastlane(app: App, root: Path) -> list[Gap]:
    def gap(message: str) -> Gap:
        return Gap(app.id, "store", message)

    base = root / "fastlane/metadata/android"
    code = _version_code(root)
    gaps = [] if code else [gap("gradle.properties has no literal VERSION_CODE line")]
    for loc in LOCALES:
        for name in TEXTS:
            if not (base / loc / name).is_file():
                gaps.append(gap(f"{loc}/{name} missing"))
        if code and not (base / loc / "changelogs" / f"{code}.txt").is_file():
            gaps.append(gap(f"{loc} changelog for versionCode {code} missing"))
    images = base / "en-US" / "images"
    for name in ("icon.png", "featureGraphic.png"):
        if not (images / name).is_file():
            gaps.append(gap(f"en-US/images/{name} missing"))
    shots = images / "phoneScreenshots"
    count = len(list(shots.glob("*.png")) + list(shots.glob("*.jpg"))) if shots.is_dir() else 0
    if count < 2:
        gaps.append(gap("fewer than two phone screenshots"))
    return gaps


def check_inapp(app: App, root: Path) -> list[Gap]:
    def gap(message: str) -> Gap:
        return Gap(app.id, "app", message)

    main = root / "app/src/main"
    code_files = list(main.rglob("*.kt")) + list(main.rglob("*.java"))
    gaps = []
    if not any("about" in f.stem.lower() for f in code_files):
        gaps.append(gap("no About screen (no source file named *About*)"))
    sources = "".join(f.read_text("utf-8", "replace") for f in code_files + list(main.rglob("*.xml")))
    if not app.privacy or app.privacy not in sources:
        gaps.append(gap(f"the app does not link its privacy policy ({app.privacy or 'no privacy URL in apps.yml'})"))
    other = "en" if app.default_language == "da" else "da"
    if not (main / "res" / f"values-{other}").is_dir():
        gaps.append(gap(f"no res/values-{other} (English and Danish are both required)"))
    return gaps


def check_repo(app: App, root: Path) -> list[Gap]:
    if not root.is_dir():
        return [Gap(app.id, "repo", f"checkout missing: {root}")]
    return check_readme(app, root) + check_fastlane(app, root) + check_inapp(app, root)
```

- [ ] **Step 4: Run** `python3 -m pytest tests/test_checks_repo.py -q` → PASS.
- [ ] **Step 5: Commit** — `git add tools/checks/repo.py tests/test_checks_repo.py && git commit -m "feat: repository checks for README, store listing and in-app About"`.

### Task 7: Audit CLI and STATUS.md (`tools/audit.py`)

**Files:** Create `tools/audit.py`; Test `tests/test_audit.py`; generated `STATUS.md`.

**Interfaces — Consumes:** `load`, `find`, `App` (Task 2); `check_catalogue` (Task 4b); `check_site`, `check_release`, `check_fdroid` (Task 5); `check_repo` (Task 6); `fetch` (Task 5). **Produces:**
```python
def audit_app(app: App, fetch: Fetch, projects: Path) -> list[Gap]
def status_markdown(apps: list[App], gaps: dict[str, list[Gap]], date: str) -> str
def main(argv: list[str] | None = None) -> int
```

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement `tools/audit.py`**

```python
"""Audit apps against the standard and write STATUS.md."""
from __future__ import annotations

import argparse
import datetime
from pathlib import Path

from tools.catalogue import check_catalogue
from tools.checks import Fetch, Gap
from tools.checks.repo import check_repo
from tools.checks.web import check_fdroid, check_release, check_site
from tools.net import fetch as real_fetch
from tools.registry import ROOT, App, find, load

PROJECTS = Path.home() / "0-projects"


def audit_app(app: App, fetch: Fetch, projects: Path) -> list[Gap]:
    if app.private:
        return []
    return (check_site(app, fetch) + check_release(app, fetch) + check_fdroid(app, fetch)
            + check_repo(app, projects / app.checkout)
            + check_catalogue(app, projects / "cocodedk" / "templates" / "partials" / "catalogue.html"))


def status_markdown(apps: list[App], gaps: dict[str, list[Gap]], date: str) -> str:
    lines = [f"# Status of every Cocode Android app ({date})", "",
             "Written by `python3 -m tools.audit all`. Fewer gaps is better; 0 meets the standard.", "",
             "| App | F-Droid | Gaps | What is missing |", "|---|---|---|---|"]
    for app in apps:
        if app.private:
            lines.append(f"| {app.name_en} | private | – | – |")
            continue
        found = gaps.get(app.id, [])
        listed = "<br>".join(f"{g.area}: {g.message}" for g in found) or "—"
        lines.append(f"| {app.name_en} | {app.fdroid} | {len(found)} | {listed} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Cocode apps against the standard.")
    parser.add_argument("app", help="an app id, or 'all'")
    args = parser.parse_args(argv)
    apps = load()
    chosen = apps if args.app == "all" else [find(apps, args.app)]
    gaps = {app.id: audit_app(app, real_fetch, PROJECTS) for app in chosen}
    for app_id, found in gaps.items():
        print(f"{app_id}: {len(found)} gap(s)")
        for g in found:
            print(f"  - {g.area}: {g.message}")
    if args.app == "all":
        today = datetime.date.today().isoformat()
        (ROOT / "STATUS.md").write_text(status_markdown(apps, gaps, today), "utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run** `python3 -m pytest tests/test_audit.py -q` → PASS, then `bash scripts/gate.sh` → all pass.
- [ ] **Step 5: First real audit** — `python3 -m tools.audit all` (this one run uses the network). Read `STATUS.md`; every public app should show gaps (no app has the markers yet). If an app errors instead of reporting, fix the check and add a test for that input before continuing.
- [ ] **Step 6: Commit** — `git add tools/audit.py tests/test_audit.py STATUS.md && git commit -m "feat: audit every app and write STATUS.md"`.

### Task 8: F-Droid status refresh and daily workflow

**Files:** Create `tools/fdroid_status.py`, `.github/workflows/fdroid-status.yml`; Test `tests/test_fdroid_status.py`.

**Interfaces — Produces:** `def refresh(data: dict, fetch: Fetch) -> list[str]` (mutates `data["apps"]` in place, returns ids that turned live); `main()` loads `apps.yml` as a dict, calls `refresh`, writes it back with `yaml.safe_dump(data, sort_keys=False, allow_unicode=True)` when anything changed.

- [ ] **Step 1: Write the failing tests**

```python
from tools.fdroid_status import refresh


def test_listed_app_turns_live_and_others_stay():
    data = {"apps": [
        {"id": "a", "applicationId": "dk.a", "fdroid": "mr:1"},
        {"id": "b", "applicationId": "dk.b", "fdroid": "none"},
        {"id": "p", "name": {"en": "P", "da": "P"}, "private": True},
    ]}
    fetch = lambda url: (200, "{}") if url.endswith("/dk.a") else (404, "")  # noqa: E731
    assert refresh(data, fetch) == ["a"]
    assert data["apps"][0]["fdroid"] == "live" and data["apps"][1]["fdroid"] == "none"


def test_live_app_is_never_downgraded_on_a_bad_answer():
    data = {"apps": [{"id": "a", "applicationId": "dk.a", "fdroid": "live"}]}
    assert refresh(data, lambda url: (0, "")) == [] and data["apps"][0]["fdroid"] == "live"
```

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement `tools/fdroid_status.py`**

```python
"""Ask f-droid.org which apps are live; update apps.yml. Never downgrades a live app."""
import yaml

from tools.checks import Fetch
from tools.net import fetch as real_fetch
from tools.registry import ROOT, parse

API = "https://f-droid.org/api/v1/packages/{}"


def refresh(data: dict, fetch: Fetch) -> list[str]:
    turned = []
    for raw in data.get("apps", []):
        if raw.get("private") or raw.get("fdroid") == "live":
            continue
        if fetch(API.format(raw["applicationId"]))[0] == 200:
            raw["fdroid"] = "live"
            turned.append(raw["id"])
    return turned


def main() -> int:
    path = ROOT / "apps.yml"
    data = yaml.safe_load(path.read_text("utf-8"))
    turned = refresh(data, real_fetch)
    if turned:
        parse(data)  # still valid before writing
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), "utf-8")
    print("now live: " + (", ".join(turned) or "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Workflow** `.github/workflows/fdroid-status.yml` (uses only the checkout action, SHA-pinned as in guard-android; the runner's Python and `pip`):

```yaml
name: F-Droid status
on:
  schedule: [{cron: "17 6 * * *"}]
  workflow_dispatch:
permissions:
  contents: write
  pull-requests: write
jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - run: python3 -m pip install --quiet "PyYAML>=6"
      - run: python3 -m tools.fdroid_status
      - name: Open a PR when an app went live
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          if git diff --quiet apps.yml; then echo "no change"; exit 0; fi
          branch="fdroid-status/$(date +%F)"
          git config user.name "cocode-apps bot"
          git config user.email "bb@cocode.dk"
          git switch -c "$branch"
          git commit -am "chore: mark apps live on F-Droid"
          git push -u origin "$branch"
          gh pr create --fill --body "f-droid.org now lists these apps. Merge, then run \`python3 -m tools.render <app>\` for each app and \`python3 -m tools.render --catalogue\` for cocode.dk, and open their PRs."
```

- [ ] **Step 5: Run** `python3 -m pytest tests/test_fdroid_status.py -q` → PASS.
- [ ] **Step 6: Commit** — `git add tools/fdroid_status.py tests/test_fdroid_status.py .github && git commit -m "feat: daily F-Droid status refresh"`.

### Task 9: The standard and templates (text)

**Files:** Create `standard/about-page.md`, `privacy.md`, `install-block.md`, `navigation.md`, `readme.md`, `store-listing.md`, `release.md`, `website.md`, `support.md`; `templates/about-strings.md`, `templates/privacy-skeleton.html`.

- [ ] **Step 1:** Write each `standard/*.md` from the spec's "The standard" section, one area per file, each with: **What must exist** (bullets copied exactly from the spec), **Where** (paths/URLs, with `<app>` placeholders that the reader fills from `apps.yml`), **How the audit checks it** (name the check function from Tasks 5–6, or "checked by hand" for in-app order and TalkBack), **Example** (guard-android, which meets most of it). `support.md`: "Reserved for the Support phase (money, time, tokens). The About page and the site keep an empty Support slot until then."
- [ ] **Step 2:** `templates/about-strings.md`: the About page section titles and button labels in English and Danish as a table (keys `about_check_updates`, `about_privacy_link`, `about_website`, `about_source`, `about_report`, `about_credits`, `about_made_by`), taking the wording from guard-android's `app/src/main/res/values*/strings.xml` where it has them, and adding `about_check_updates` = "Check for updates" / "Søg efter opdateringer".
- [ ] **Step 3:** `templates/privacy-skeleton.html`: a minimal, accessible page (one `h1`, `main`, skip link, the nav/footer markers) with the nine headings from the spec in order (Summary, What is collected, Servers the app contacts, Permissions, What stays on the phone, Third parties, Your rights, Contact, Changes), each with a one-line HTML comment saying what goes there. English; the Danish headings in a comment block at the top.
- [ ] **Step 4:** `bash scripts/gate.sh` still passes; commit — `git add standard templates && git commit -m "docs: the publishing standard and its templates"`.

### Task 10: The skill

**Files:** Create `skill/SKILL.md`; link it into the owner's skills.

- [ ] **Step 1:** Write `skill/SKILL.md` with front matter `name: cocode-apps` and a description such as "Brings a Cocode Android app up to the shared publishing standard (About page, privacy page, F-Droid install block, navigation, README, store listing, release routine) using the cocode-apps registry, audit and render tools. Use when making an app's site, README, About page or store listing consistent with the other Cocode apps, after an app is accepted on F-Droid, or to see which apps lack what." Body: the five steps (audit → list gaps → fix → render, which includes `render.py --catalogue` so cocode.dk carries the app's F-Droid or APK download link → re-audit and follow every link), when to use `android-setup` (new project) and `fdroid-release` (submitting), the rules from `CLAUDE.md` (owner's OK before any push; private apps; never name Spamhaus in promotional text), and the commands.
- [ ] **Step 2:** Link it: check how `~/.claude-personal/skills/fdroid-release` is installed (`ls -la ~/.claude-personal/skills/ | head`), then link the same way, e.g. `ln -s ~/0-projects/cocode-apps/skill ~/.claude-personal/skills/cocode-apps`. If the work account (`~/.claude/skills`) also links shared skills, link there too.
- [ ] **Step 3:** Commit — `git add skill && git commit -m "feat: the cocode-apps skill"`.

### Task 11: Publish the repository (ask the owner first)

- [ ] **Step 1:** Ask the owner to confirm creating the public repo `cocodedk/cocode-apps`.
- [ ] **Step 2:** `gh repo create cocodedk/cocode-apps --public --source . --remote origin --description "One publishing standard for every Cocode Android app: registry, audit, render, F-Droid status." --push`.
- [ ] **Step 3:** In the repo settings, allow GitHub Actions to create pull requests (Settings → Actions → General → "Allow GitHub Actions to create and approve pull requests"), then run the workflow once by hand: `gh workflow run fdroid-status.yml` and check it finishes green.

## After this plan

Rollout steps 2–6 of the spec (guard-android as reference; the three live apps; the open-MR apps; the rest; Support) each get their own plan, written with the skill once this project exists.
