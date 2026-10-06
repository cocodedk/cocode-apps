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
    match = re.search(r"^VERSION_CODE=(\d+)\s*$", props.read_text("utf-8"), re.MULTILINE)
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
