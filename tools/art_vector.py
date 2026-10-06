"""Android vector drawables to SVG markup (paths, groups with transforms, clip paths, gradients)."""
from __future__ import annotations

import re
from html import escape
from xml.etree import ElementTree as ET

from tools.art_res import RGBA, Res, css, hex_rgb

ANDROID = "{http://schemas.android.com/apk/res/android}"
AAPT = "{http://schemas.android.com/aapt}"


def attr(el: ET.Element, name: str) -> str | None:
    return el.get(ANDROID + name)


def num(value: str | None, default: float = 0.0) -> float:
    m = re.match(r"^\s*(-?\d*\.?\d+)", value or "")
    return float(m.group(1)) if m else default


def g(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"


def esc(value: str) -> str:
    return escape(value, quote=True)


def gradient_of(el: ET.Element, name: str) -> ET.Element | None:
    for child in el:
        if child.tag == AAPT + "attr" and child.get("name") == "android:" + name:
            return child.find("gradient")
    return None


def gradient_stops(grad: ET.Element, res: Res) -> list[tuple[float, RGBA]]:
    stops = [(num(attr(i, "offset")), res.color(attr(i, "color"))) for i in grad.findall("item")]
    stops = [(o, c) for o, c in stops if c]
    if stops:
        return stops
    ends = [(0.0, "startColor"), (0.5, "centerColor"), (1.0, "endColor")]
    return [(o, c) for o, c in ((o, res.color(attr(grad, n))) for o, n in ends) if c]


def first_color(root: ET.Element, res: Res) -> RGBA | None:
    """The first visible fill in a vector: its flat colour when it is one flat sheet (a background)."""
    for path in root.iter("path"):
        colour = res.color(attr(path, "fillColor"))
        if colour is None and (grad := gradient_of(path, "fillColor")) is not None:
            stops = gradient_stops(grad, res)
            colour = stops[0][1] if stops else None
        if colour and colour[3] > 0:
            return colour
    return None


class VectorSvg:
    """Converts one `<vector>`; `prefix` keeps ids unique when several vectors share one SVG."""

    def __init__(self, res: Res, prefix: str = "v"):
        self.res, self.prefix, self.defs, self._n = res, prefix, [], 0

    def convert(self, root: ET.Element) -> tuple[str, float, float]:
        """(markup, viewport width, viewport height); the markup is meant for a viewBox of those."""
        vw = num(attr(root, "viewportWidth")) or num(attr(root, "width"), 24)
        vh = num(attr(root, "viewportHeight")) or num(attr(root, "height"), 24)
        body = self._children(root)
        return ("<defs>" + "".join(self.defs) + "</defs>" if self.defs else "") + body, vw, vh

    def _id(self, kind: str) -> str:
        self._n += 1
        return f"{self.prefix}-{kind}{self._n}"

    def _children(self, parent: ET.Element) -> str:
        out, clips = [], 0
        for el in parent:
            if el.tag == "path":
                out.append(self._path(el))
            elif el.tag == "group":
                out.append(self._group(el))
            elif el.tag == "clip-path" and attr(el, "pathData"):  # clips what follows, like Android
                cid = self._id("clip")
                self.defs.append(f'<clipPath id="{cid}"><path d="{esc(" ".join(attr(el, "pathData").split()))}"/></clipPath>')
                out.append(f'<g clip-path="url(#{cid})">')
                clips += 1
        return "".join(out) + "</g>" * clips

    def _group(self, el: ET.Element) -> str:
        tx, ty, px, py = (num(attr(el, n)) for n in ("translateX", "translateY", "pivotX", "pivotY"))
        sx, sy, rot = num(attr(el, "scaleX"), 1), num(attr(el, "scaleY"), 1), num(attr(el, "rotation"))
        parts = []
        if rot or sx != 1 or sy != 1:  # Android: translate(pivot + shift) rotate scale translate(-pivot)
            if tx or ty or px or py:
                parts.append(f"translate({g(px + tx)} {g(py + ty)})")
            if rot:
                parts.append(f"rotate({g(rot)})")
            if sx != 1 or sy != 1:
                parts.append(f"scale({g(sx)} {g(sy)})")
            if px or py:
                parts.append(f"translate({g(-px)} {g(-py)})")
        elif tx or ty:  # the pivot only matters to a rotation or a scale
            parts.append(f"translate({g(tx)} {g(ty)})")
        transform = f' transform="{" ".join(parts)}"' if parts else ""
        return f"<g{transform}>{self._children(el)}</g>"

    def _path(self, el: ET.Element) -> str:
        data = attr(el, "pathData")
        if not data:
            return ""
        a = {"d": " ".join(data.split()), "fill": self._paint(el, "fillColor") or "none"}
        if stroke := self._paint(el, "strokeColor"):
            a["stroke"], a["stroke-width"] = stroke, g(num(attr(el, "strokeWidth")))
        for name, svg in (("fillAlpha", "fill-opacity"), ("strokeAlpha", "stroke-opacity"),
                          ("strokeLineCap", "stroke-linecap"), ("strokeLineJoin", "stroke-linejoin"),
                          ("strokeMiterLimit", "stroke-miterlimit")):
            if attr(el, name) not in (None, ""):
                a[svg] = attr(el, name)
        if attr(el, "fillType") == "evenOdd":
            a["fill-rule"] = "evenodd"
        return "<path " + " ".join(f'{k}="{esc(v)}"' for k, v in a.items()) + "/>"

    def _paint(self, el: ET.Element, name: str) -> str | None:
        colour = self.res.color(attr(el, name))
        if colour:
            return css(colour)
        grad = gradient_of(el, name)
        return self._gradient(grad) if grad is not None else None

    def _gradient(self, grad: ET.Element) -> str | None:
        stops = gradient_stops(grad, self.res)
        kind = attr(grad, "type") or "linear"
        if not stops:
            return None
        if len(stops) == 1 or kind not in ("linear", "radial"):
            return css(stops[0][1])
        gid = self._id("grad")
        if kind == "radial":
            head = (f'<radialGradient id="{gid}" gradientUnits="userSpaceOnUse" cx="{g(num(attr(grad, "centerX")))}" '
                    f'cy="{g(num(attr(grad, "centerY")))}" r="{g(num(attr(grad, "gradientRadius"), 1))}">')
            tail = "</radialGradient>"
        else:
            head = (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{g(num(attr(grad, "startX")))}" '
                    f'y1="{g(num(attr(grad, "startY")))}" x2="{g(num(attr(grad, "endX")))}" y2="{g(num(attr(grad, "endY")))}">')
            tail = "</linearGradient>"
        body = "".join(f'<stop offset="{g(o)}" stop-color="{hex_rgb(c)}" stop-opacity="{g(c[3])}"/>' for o, c in stops)
        self.defs.append(head + body + tail)
        return f"url(#{gid})"
