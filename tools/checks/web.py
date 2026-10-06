"""Checks against live URLs: site, privacy, release asset, F-Droid."""
import re
from html import unescape

from tools.checks import Fetch, Gap
from tools.registry import App

MARKERS = {"navigation": "cocode-apps:nav:start", "install block": "cocode-apps:install:start",
           "footer": "cocode-apps:footer:start"}
NAV_END = "cocode-apps:nav:end"
NAV_ORDER = ["home", "how", "install", "privacy", "lang", "more"]


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
    return gaps + _nav_gaps(home, gap) + _file_gaps(app, home, fetch, gap) + _old_privacy_gaps(app, fetch, gap)


def _tags(html: str, name: str) -> list[str]:
    """Tags of one kind; commented-out HTML is not a tag."""
    html = re.sub(r"<!--.*?(?:-->|\Z)", "", html, flags=re.DOTALL)
    return re.findall(rf"""<{name}\b(?:[^>"']|"[^"]*"|'[^']*')*>""", html, re.IGNORECASE)


def _attr(tag: str, name: str) -> str | None:
    """One attribute's value, read by walking the tag's attributes so quoted values are never searched."""
    body = re.sub(r"^<[^\s/>]+", "", tag)
    for key, *values in re.findall(r"""([^\s"'<>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?""", body):
        if key.lower() == name:
            return unescape(next((v for v in values if v), ""))
    return None


def _nav_block(page: str) -> str | None:
    """The text between the nav markers, or None unless both markers are there in order."""
    start = page.find("<!-- " + MARKERS["navigation"])
    end = page.find("<!-- " + NAV_END, start)
    if start == -1 or end == -1:
        return None
    return page[start:end]


def _nav_gaps(home: str, gap) -> list[Gap]:
    if MARKERS["navigation"] not in home:
        return []  # the missing-marker gap already says so
    block = _nav_block(home) or ""
    values = [_attr(tag, "data-nav") for tag in _tags(block, "a")]
    found = [v if v else "(empty)" for v in values if v is not None]
    if found == NAV_ORDER:
        return []
    return [gap(f"navigation items are {', '.join(found) or 'none'}, expected {', '.join(NAV_ORDER)}")]


def _og_image(home: str) -> str | None:
    for tag in _tags(home, "meta"):
        if _attr(tag, "property") == "og:image":
            return _attr(tag, "content")
    return None


def _file_gaps(app: App, home: str, fetch: Fetch, gap) -> list[Gap]:
    gaps = []
    for path, label in (("/img/icon.png", "app icon"), ("/css/cocode-nav.css", "navigation stylesheet"),
                        ("/robots.txt", "robots.txt")):
        if fetch(app.site + path)[0] != 200:
            gaps.append(gap(f"no {label} ({app.site}{path})"))
    image = _og_image(home)
    if not image or not image.startswith("https://"):
        gaps.append(gap("home page has no og:image share image with an absolute https:// URL"))
    elif fetch(image)[0] != 200:
        gaps.append(gap(f"share image does not answer 200 ({image})"))
    return gaps


def _is_refresh_to_privacy(page: str) -> bool:
    for tag in _tags(page, "meta"):
        if (_attr(tag, "http-equiv") or "").lower() == "refresh":
            url = re.search(r"url\s*=\s*(\S+)", _attr(tag, "content") or "", re.IGNORECASE)
            if url and url.group(1).rstrip("'\"").endswith("privacy/"):
                return True
    return False


def _is_standard_privacy_page(page: str) -> bool:
    return any(_attr(tag, "data-nav") == "privacy" and _attr(tag, "aria-current") == "page"
               for tag in _tags(_nav_block(page) or "", "a"))


def _old_privacy_gaps(app: App, fetch: Fetch, gap) -> list[Gap]:
    status, page = fetch(app.site + "/privacy.html")
    if status == 404 or (status == 200 and (_is_refresh_to_privacy(page) or _is_standard_privacy_page(page))):
        return []
    return [gap("privacy.html does not redirect to /privacy/")]


def check_release(app: App, fetch: Fetch) -> list[Gap]:
    status, _ = fetch(app.apk_url)
    return [] if status == 200 else [Gap(app.id, "release", f"{app.apk_asset} does not download (status {status})")]


def check_fdroid(app: App, fetch: Fetch) -> list[Gap]:
    status, _ = fetch(f"https://f-droid.org/api/v1/packages/{app.application_id}")
    if status == 0:
        return [Gap(app.id, "fdroid", "f-droid.org unreachable")]
    if status == 200 and not app.fdroid_live:
        return [Gap(app.id, "fdroid", f"f-droid.org lists it: set fdroid to live (now {app.fdroid})")]
    if status != 200 and app.fdroid_live:
        return [Gap(app.id, "fdroid", "apps.yml says live but f-droid.org has not listed it")]
    return []
