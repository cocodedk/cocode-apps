"""Store and site artwork for one app, drawn from the app's own launcher icon.

Writes icon.png (512x512) into the fastlane images and the site's img folder, and a 1024x500
featureGraphic.png. Headless Chrome rasterizes an HTML page; nothing is fetched from the network.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

from tools.art_icon import Icon, find_icon
from tools.art_res import RGBA, ArtError, hex_rgb
from tools.registry import ROOT, App, RegistryError, find, load
from tools.render import PROJECTS

TEMPLATE = ROOT / "templates" / "feature-graphic.html"
IMAGES = Path("fastlane/metadata/android/en-US/images")
SHORT_DESCRIPTION = Path("fastlane/metadata/android/en-US/short_description.txt")
NEUTRAL: RGBA = (0x1D, 0x23, 0x2A, 1.0)
WHITE: RGBA = (255, 255, 255, 1.0)
NEAR_BLACK: RGBA = (0x10, 0x14, 0x18, 1.0)
ICON_PAGE = '<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:transparent}}svg{{display:block}}</style>{svg}'


def luminance(color: RGBA) -> float:
    """WCAG 2 relative luminance."""
    def channel(v: int) -> float:
        s = v / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in color[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: RGBA, b: RGBA) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def text_color(background: RGBA) -> RGBA:
    """White or near-black, whichever reads better on `background`."""
    return WHITE if contrast(WHITE, background) >= contrast(NEAR_BLACK, background) else NEAR_BLACK


def read_tagline(root: Path) -> str:
    """The first line of the en-US short description, or nothing."""
    path = root / SHORT_DESCRIPTION
    if not path.is_file():
        return ""
    lines = [line.strip() for line in path.read_text("utf-8").splitlines() if line.strip()]
    return lines[0] if lines else ""


def name_size(name: str) -> int:
    """Font size in px: a long name steps down so it fits the text column in at most two lines."""
    return 76 if len(name) <= 10 else 66 if len(name) <= 14 else 58 if len(name) <= 22 else 48


def fill(template: str, values: dict[str, str], raw: tuple[str, ...] = ("icon",)) -> str:
    """Replace `{{key}}`; every value is HTML-escaped except those named in `raw` (our own SVG markup)."""
    def value(m: re.Match) -> str:
        v = values[m.group(1)]
        return v if m.group(1) in raw else escape(v, quote=True)

    return re.sub(r"\{\{(\w+)\}\}", value, template)


def feature_graphic_html(icon: Icon, name: str, tagline: str) -> str:
    bg = icon.background or NEUTRAL
    values = {"name": name, "tagline": tagline, "bg": hex_rgb(bg), "fg": hex_rgb(text_color(bg)),
              "name_size": str(name_size(name)), "icon": icon.svg(280)}
    return fill(TEMPLATE.read_text("utf-8"), values)


def icon_html(icon: Icon) -> str:
    return ICON_PAGE.format(svg=icon.svg(512))


def rasterize(html: str, width: int, height: int, out: Path) -> None:
    """Screenshot `html` at width x height with headless Chrome into `out`."""
    chrome = next((p for n in ("google-chrome-stable", "google-chrome", "chromium") if (p := shutil.which(n))), None)
    if not chrome:
        raise ArtError("google-chrome-stable not found on PATH; it rasterizes the artwork")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        page.write_text(html, "utf-8")
        cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
               f"--user-data-dir={tmp}/profile", f"--screenshot={out}", f"--window-size={width},{height}", page.as_uri()]
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    if not out.is_file():
        raise ArtError(f"chrome wrote no screenshot (exit {done.returncode}): {done.stderr.strip()[-300:]}")


def render_png(html: str, width: int, height: int, out: Path, opaque: bool) -> None:
    """rasterize, then check the size with PIL and store RGB (opaque) or RGBA."""
    rasterize(html, width, height, out)
    from PIL import Image  # here, so only a real render needs it

    with Image.open(out) as image:
        if image.size != (width, height):
            raise ArtError(f"chrome wrote {image.size[0]}x{image.size[1]}, expected {width}x{height}")
        converted = image.convert("RGB" if opaque else "RGBA")
    converted.save(out, "PNG", optimize=True)


def make(app: App, root: Path, tagline: str | None = None) -> list[str]:
    """Write the three files into `root`; returns one report line per file."""
    icon = find_icon(root)
    line = read_tagline(root) if tagline is None else tagline.strip()
    targets = [(root / IMAGES / "icon.png", "icon"), (root / app.site_dir / "img" / "icon.png", "icon"),
               (root / IMAGES / "featureGraphic.png", "feature")]
    with tempfile.TemporaryDirectory() as tmp:  # render first; a failed render leaves the app untouched
        built = {"icon": Path(tmp) / "icon.png", "feature": Path(tmp) / "featureGraphic.png"}
        render_png(icon_html(icon), 512, 512, built["icon"], opaque=False)
        render_png(feature_graphic_html(icon, app.name_en, line), 1024, 500, built["feature"], opaque=True)
        for dest, key in targets:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(built[key], dest)
    return [f"wrote {dest.relative_to(root)}" for dest, _ in targets]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Draw an app's store icon and feature graphic from its launcher icon.")
    parser.add_argument("app")
    parser.add_argument("--root", type=Path, help="the app folder (default: its checkout under ~/0-projects)")
    parser.add_argument("--tagline", help="text under the name (default: the en-US short description)")
    args = parser.parse_args(argv)
    try:
        app = find(load(), args.app)
        if app.private:
            print(f"{app.id}: private, skipped")
            return 0
        root = args.root or PROJECTS / app.checkout
        if not root.is_dir():
            raise ArtError(f"no such folder: {root}")
        for line in make(app, root, args.tagline):
            print(line)
    except (ArtError, RegistryError) as error:
        print(f"art: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
