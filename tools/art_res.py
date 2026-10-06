"""Android resources for the artwork tool: colours and drawable lookup in an app's `src/main`."""
from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET

RGBA = tuple[int, int, int, float]
DENSITIES = ("xxxhdpi", "xxhdpi", "xhdpi", "hdpi", "mdpi")
RASTER_EXT = (".png", ".webp")
NAMED = {"white": (255, 255, 255, 1.0), "black": (0, 0, 0, 1.0), "transparent": (0, 0, 0, 0.0)}
REF = re.compile(r"^@(?:[\w.]+:)?(mipmap|drawable|color)/([\w.]+)$")
HEX = re.compile(r"^#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
VERSION = re.compile(r"-v(\d+)")


class ArtError(Exception):
    """Something the tool cannot do; the message says what, and the CLI prints it."""


def parse_hex(value: str) -> RGBA | None:
    """`#RGB`, `#ARGB`, `#RRGGBB` or `#AARRGGBB` (Android puts alpha first)."""
    m = HEX.match(value.strip())
    if not m:
        return None
    digits = m.group(1)
    if len(digits) in (3, 4):
        digits = "".join(c * 2 for c in digits)
    if len(digits) == 6:
        digits = "ff" + digits
    a, r, g, b = (int(digits[i : i + 2], 16) for i in (0, 2, 4, 6))
    return r, g, b, round(a / 255, 3)


def css(color: RGBA) -> str:
    r, g, b, a = color
    alpha = f"{a:.3f}".rstrip("0").rstrip(".") if a < 1 else "1"
    return f"rgba({r},{g},{b},{alpha})"


def hex_rgb(color: RGBA) -> str:
    return "#{:02x}{:02x}{:02x}".format(*color[:3])


def parse_ref(value: str | None) -> tuple[str, str] | None:
    m = REF.match((value or "").strip())
    return (m.group(1), m.group(2)) if m else None


class Res:
    """The `res/` folder of one app module (`app/src/main`)."""

    def __init__(self, main: Path):
        self.main = main
        self.res = main / "res"
        self._colors: dict[str, str] | None = None

    def _color_table(self) -> dict[str, str]:
        if self._colors is None:
            table: dict[str, str] = {}
            folders = [d for d in self.res.glob("values*") if d.is_dir() and "night" not in d.name]
            for folder in sorted(folders, key=lambda d: (d.name != "values", d.name)):
                for xml in sorted(folder.glob("*.xml")):
                    try:
                        items = ET.parse(xml).getroot().iter("color")
                    except ET.ParseError:
                        continue
                    for item in items:
                        if item.get("name") and item.text:
                            table.setdefault(item.get("name"), item.text.strip())
            self._colors = table
        return self._colors

    def color(self, value: str | None, depth: int = 0) -> RGBA | None:
        """A literal, an `@color/x` reference or an `@android:color/white`; None when unknown."""
        value = (value or "").strip()
        if not value or depth > 8:
            return None
        if value.startswith("#"):
            return parse_hex(value)
        if value.startswith("@android:color/"):
            return NAMED.get(value.split("/", 1)[1])
        ref = parse_ref(value)
        if ref and ref[0] == "color":
            return self.color(self._color_table().get(ref[1]), depth + 1)
        return None

    def xml_drawable(self, name: str) -> Path | None:
        """`res/{drawable,mipmap}*/<name>.xml`; the highest `-vNN` folder wins, as on a modern device."""
        found = [p for p in self.res.glob(f"*/{name}.xml") if re.match(r"(drawable|mipmap)", p.parent.name)]
        found = [p for p in found if "night" not in p.parent.name]
        if not found:
            return None

        def version(path: Path) -> int:
            m = VERSION.search(path.parent.name)
            return int(m.group(1)) if m else 0

        return max(found, key=lambda p: (version(p), "anydpi" in p.parent.name, p.parent.name == "drawable"))

    def raster(self, name: str, kinds: tuple[str, ...] = ("mipmap", "drawable")) -> Path | None:
        """The largest-density `<name>.png` or `.webp`; an unqualified or `-nodpi` folder comes last."""
        for kind in kinds:
            for density in (*DENSITIES, "nodpi", ""):
                folder = self.res / (f"{kind}-{density}" if density else kind)
                for ext in RASTER_EXT:
                    if (folder / f"{name}{ext}").is_file():
                        return folder / f"{name}{ext}"
        return None
