"""Find an app's launcher icon and turn it into an SVG that renders as the launcher shows it."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.art_res import RGBA, ArtError, Res, css, parse_ref
from tools.art_vector import ANDROID, VectorSvg, attr, first_color

MAIN = Path("app/src/main")
MANIFEST = MAIN / "AndroidManifest.xml"
PLAYSTORE = MAIN / "ic_launcher-playstore.png"
ADAPTIVE_BOX = (18.0, 18.0, 72.0, 72.0)  # of the 108dp layers, the centre 72dp is what a launcher shows
CORNER = 18  # percent of the size
MIME = {".png": "image/png", ".webp": "image/webp"}


@dataclass(frozen=True)
class Icon:
    body: str  # SVG markup in the icon's own coordinates
    box: tuple[float, float, float, float]  # the part of those coordinates that is the icon
    background: RGBA | None = None  # the icon's background colour, when it has one flat colour

    def svg(self, size: int) -> str:
        """An inline `<svg>` of `size` px with rounded corners; it needs no xmlns inside HTML."""
        x, y, w, h = self.box
        return (
            f'<svg width="{size}" height="{size}" viewBox="0 0 100 100">'
            f'<defs><clipPath id="icon-round"><rect width="100" height="100" rx="{CORNER}" ry="{CORNER}"/></clipPath></defs>'
            f'<g clip-path="url(#icon-round)"><svg width="100" height="100" viewBox="{x:g} {y:g} {w:g} {h:g}">'
            f"{self.body}</svg></g></svg>"
        )


def manifest_icon(root: Path) -> str | None:
    """The `android:icon` of the manifest's `<application>`, e.g. `@mipmap/ic_launcher`."""
    path = root / MANIFEST
    if not path.is_file():
        return None
    try:
        app = ET.parse(path).getroot().find("application")
    except ET.ParseError:
        return None
    return app.get(ANDROID + "icon") if app is not None else None


def _uri(path: Path) -> str:
    return f"data:{MIME[path.suffix]};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _vector(res: Res, name: str) -> ET.Element | None:
    path = res.xml_drawable(name)
    if path is None:
        return None
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    return root if root.tag == "vector" else None


def _layer(res: Res, value: str | None, prefix: str) -> tuple[str, RGBA | None] | None:
    """One 108dp layer of an adaptive icon: a colour, a vector drawable or a raster."""
    if colour := res.color(value):
        return f'<rect width="108" height="108" fill="{css(colour)}"/>', colour
    ref = parse_ref(value)
    if not ref:
        return None
    if (vector := _vector(res, ref[1])) is not None:
        markup, vw, vh = VectorSvg(res, prefix).convert(vector)
        return f'<svg width="108" height="108" viewBox="0 0 {vw:g} {vh:g}">{markup}</svg>', first_color(vector, res)
    if raster := res.raster(ref[1]):
        return f'<image width="108" height="108" href="{_uri(raster)}"/>', None
    return None


def _adaptive(res: Res, name: str) -> Icon | None:
    path = res.xml_drawable(name)
    if path is None:
        return None
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    if root.tag != "adaptive-icon":
        return None
    parts = {}
    for layer in ("background", "foreground"):
        el = root.find(layer)
        parts[layer] = _layer(res, attr(el, "drawable"), layer[:2]) if el is not None else None
    if parts["foreground"] is None:
        return None
    back = parts["background"] or ("", None)
    return Icon(back[0] + parts["foreground"][0], ADAPTIVE_BOX, back[1])


def _raster_icon(path: Path) -> Icon:
    return Icon(f'<image width="100" height="100" href="{_uri(path)}"/>', (0, 0, 100, 100))


def find_icon(root: Path) -> Icon:
    """The launcher icon of the app checkout at `root`, or ArtError naming what was looked for.

    Order: the Play Store png; the adaptive icon (what a device on Android 8+ shows, and the legacy
    densities beside it are often only the Android Studio default); a density raster; a plain vector.
    """
    res = Res(root / MAIN)
    if (root / PLAYSTORE).is_file():
        return _raster_icon(root / PLAYSTORE)
    ref = parse_ref(manifest_icon(root))
    if ref:
        icon = _adaptive(res, ref[1])
        if icon:
            return icon
        if raster := res.raster(ref[1]):
            return _raster_icon(raster)
        if (vector := _vector(res, ref[1])) is not None:
            markup, vw, vh = VectorSvg(res, "v").convert(vector)
            return Icon(markup, (0, 0, vw, vh))
    raise ArtError(
        f"no launcher icon found in {root}; looked for {PLAYSTORE}, then android:icon in {MANIFEST} "
        f"({manifest_icon(root) or 'none'}) as an adaptive icon, a png/webp in res/mipmap-*/ or "
        "res/drawable-*/, or a vector drawable"
    )
