"""Checks against live URLs: site, privacy, release asset, F-Droid."""
from tools.checks import Fetch, Gap
from tools.registry import App

MARKERS = {"navigation": "cocode-apps:nav:start", "install block": "cocode-apps:install:start",
           "footer": "cocode-apps:footer:start"}


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
    return gaps


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
