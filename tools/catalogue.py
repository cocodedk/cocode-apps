"""The download link in each cocode.dk catalogue entry, written from apps.yml (Danish site).

An app sits either in the catalogue list (catalogue.html) or among the featured works (works.html);
its `get-<id>` marker pair is in exactly one of the two.
"""
from collections.abc import Sequence
from html import escape
from pathlib import Path

from tools.blocks import catalogue_link
from tools.checks import Gap
from tools.registry import App
from tools.render import replace_block

PARTIALS = Path.home() / "0-projects" / "cocodedk" / "templates" / "partials"
CATALOGUE_FILE = PARTIALS / "catalogue.html"
WORKS_FILE = PARTIALS / "works.html"


def catalogue_html(app: App, cls: str = "index__get") -> str:
    label = "Hent på F-Droid" if app.fdroid_live else "Hent APK"
    return f'<a class="{cls}" href="{escape(catalogue_link(app))}">{label}</a>'


def apply_catalogue(apps: list[App], path: Path, write: bool = True) -> list[str]:
    cls = "work__get" if path.name == "works.html" else "index__get"
    original = path.read_bytes().decode("utf-8")
    text, report = original, []
    for app in apps:
        if app.private:
            continue
        text, state = replace_block(text, f"get-{app.id}", catalogue_html(app, cls))
        report.append(f"cocode.dk catalogue [{app.id}]: {state}")
    if write and text != original:
        path.write_bytes(text.encode("utf-8"))  # bytes: line endings outside the markers stay as they were
    return report


def apply_all(apps: list[App], paths: Sequence[Path], write: bool = True) -> list[str]:
    """Fill every partial that exists; one line per app: ok where its marker is, else the worst state."""
    states: dict[str, list[str]] = {}
    for path in (p for p in paths if p.is_file()):
        for line in apply_catalogue(apps, path, write):
            app_id, state = line.split("[", 1)[1].split("]: ")
            states.setdefault(app_id, []).append(state)
    order = ("ok", "broken", "missing")
    return [f"cocode.dk catalogue [{app_id}]: {next(s for s in order if s in found)}"
            for app_id, found in states.items()]


def check_catalogue(app: App, path: Path | Sequence[Path]) -> list[Gap]:
    if app.private:
        return []
    paths = [path] if isinstance(path, Path) else list(path)
    marker = f"cocode-apps:get-{app.id}:start"
    if not any(p.is_file() and marker in p.read_text("utf-8") for p in paths):
        return [Gap(app.id, "cocode.dk", "the cocode.dk catalogue entry has no download link (marker get-<id>)")]
    return []
