"""Write the shared blocks into an app checkout, only between cocode-apps markers."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from tools.blocks import BADGE_FILE, footer_html, install_html, install_md, nav_html, skip_html
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
        current = "home" if is_index else "privacy"
        own_skip = page.is_file() and START.format(name="skip") in page.read_text("utf-8")
        out += [(page, "nav", nav_html(app, lang, current, skip=not own_skip)), (page, "footer", footer_html(app, lang))]
        if own_skip:
            out.append((page, "skip", skip_html(lang)))
        if is_index:
            out.append((page, "install", install_html(app, lang)))
    return out


def apply(app: App, root: Path, write: bool = True) -> list[str]:
    report = []
    for path, block, content in targets(app, root):
        if not path.is_file():
            report.append(f"{path.relative_to(root)}: no such file")
            continue
        new, state = replace_block(path.read_bytes().decode("utf-8"), block, content)
        report.append(f"{path.relative_to(root)} [{block}]: {state}")
        if write and state == "ok":
            path.write_bytes(new.encode("utf-8"))  # bytes: line endings outside the markers stay as they were
    if write:
        copies = [("cocode-nav.css", "css/cocode-nav.css")]
        if app.fdroid_live:
            copies += [(f"badges/get-it-on-fdroid-{lang}.png", BADGE_FILE.format(lang=lang)) for lang in ("en", "da")]
        for source, target in copies:
            dest = root / app.site_dir / target
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "templates" / source, dest)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write cocode-apps blocks into an app checkout.")
    parser.add_argument("app", nargs="?")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--root", type=Path, help="write into this folder (a worktree, say) instead of the checkout")
    parser.add_argument("--catalogue", action="store_true", help="fill the cocode.dk catalogue links")
    args = parser.parse_args(argv)
    if args.catalogue:
        from tools import catalogue  # here, not at the top: catalogue imports this module

        files = (catalogue.CATALOGUE_FILE, catalogue.WORKS_FILE)
        for line in catalogue.apply_all(load(), files, write=not args.dry_run):
            print(line)
        return 0
    if not args.app:
        parser.error("name an app, or pass --catalogue")
    app = find(load(), args.app)
    if app.private:
        print(f"{app.id}: private, skipped")
        return 0
    for line in apply(app, args.root or PROJECTS / app.checkout, write=not args.dry_run):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
