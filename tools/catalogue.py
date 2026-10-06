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
    original = path.read_bytes().decode("utf-8")
    text, report = original, []
    for app in apps:
        if app.private:
            continue
        text, state = replace_block(text, f"get-{app.id}", catalogue_html(app))
        report.append(f"cocode.dk catalogue [{app.id}]: {state}")
    if write and text != original:
        path.write_bytes(text.encode("utf-8"))  # bytes: line endings outside the markers stay as they were
    return report


def check_catalogue(app: App, path: Path) -> list[Gap]:
    if app.private:
        return []
    if not path.is_file() or f"cocode-apps:get-{app.id}:start" not in path.read_text("utf-8"):
        return [Gap(app.id, "cocode.dk", "the cocode.dk catalogue entry has no download link (marker get-<id>)")]
    return []
