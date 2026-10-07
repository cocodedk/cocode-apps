"""Checks against an app's local checkout: README, fastlane listing, in-app About and privacy link."""
import re
from pathlib import Path

from tools.checks import Gap
from tools.registry import App

LOCALES = ("en-US", "da-DK")
TEXTS = ("title.txt", "short_description.txt", "full_description.txt")
SECTIONS = ("Features", "Privacy", "Build", "Contributing", "License")


def _headings(text: str) -> list[str]:
    """Level-2 headings a reader sees: not in code fences, not in HTML comments."""
    found, fence, in_comment = [], None, False
    for line in text.splitlines():
        if fence:
            closing = re.fullmatch(r" {0,3}(`+|~+)[ \t]*", line)
            if closing and closing.group(1)[0] == fence[0] and len(closing.group(1)) >= len(fence):
                fence = None
            continue
        if in_comment:
            if "-->" not in line:
                continue
            line, in_comment = line.split("-->", 1)[1], False
        line = re.sub(r"<!--.*?-->", "", line)
        if "<!--" in line:
            line, in_comment = line.split("<!--", 1)[0], True
        opening = re.match(r" {0,3}(`{3,}(?=[^`]*$)|~{3,})", line)
        if opening:
            fence = opening.group(1)
            continue
        heading = re.fullmatch(r" {0,3}##[ \t]+(?!#)(.+?)[ \t#]*", line)
        if heading:
            found.append(heading.group(1))
    return found


def check_readme(app: App, root: Path) -> list[Gap]:
    readme = root / "README.md"
    if not readme.is_file():
        return [Gap(app.id, "readme", "README has no shared install block (marker cocode-apps:install:start)")]
    text = readme.read_text("utf-8")
    gaps = []
    if "cocode-apps:install:start" not in text:
        gaps.append(Gap(app.id, "readme", "README has no shared install block (marker cocode-apps:install:start)"))
    headings = [h.lower() for h in _headings(text)]
    position = 0
    for section in SECTIONS:
        if section.lower() not in headings[position:]:
            problem = "out of order" if section.lower() in headings else "missing"
            gaps.append(Gap(app.id, "readme", f"README section {section} is {problem}"))
            break
        position += headings[position:].index(section.lower()) + 1
    return gaps


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


def _links_privacy(privacy: str, text: str) -> bool:
    """The whole URL, or one file that names the site and builds the privacy path from it."""
    site, _, path = privacy.partition("://")[2].partition("/")
    return privacy in text or ("https://" + site in text and path.rstrip("/").split("/")[-1] in text)


def check_inapp(app: App, root: Path) -> list[Gap]:
    def gap(message: str) -> Gap:
        return Gap(app.id, "app", message)

    main = root / "app/src/main"
    code_files = list(main.rglob("*.kt")) + list(main.rglob("*.java"))
    gaps = []
    if not any("about" in f.stem.lower() for f in code_files):
        gaps.append(gap("no source file named *About* found; check the About screen by hand"))
    texts = [f.read_text("utf-8", "replace") for f in code_files + list(main.rglob("*.xml"))]
    if not app.privacy:
        gaps.append(gap("apps.yml has no privacy URL, so the app's privacy link could not be checked"))
    elif not any(_links_privacy(app.privacy, text) for text in texts):
        gaps.append(gap(f"the privacy URL {app.privacy} was not found in the app's source or resources; "
                        "check the app's actual link by hand"))
    other = "en" if app.default_language == "da" else "da"
    if not (main / "res" / f"values-{other}").is_dir():
        gaps.append(gap(f"no res/values-{other} (English and Danish are both required)"))
    return gaps


def check_repo(app: App, root: Path) -> list[Gap]:
    if not root.is_dir():
        return [Gap(app.id, "repo", f"checkout missing: {root}")]
    return check_readme(app, root) + check_fastlane(app, root) + check_inapp(app, root)
