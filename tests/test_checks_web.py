from tools.checks import Gap
from tools.checks.web import check_fdroid, check_release, check_site
from tools.registry import parse

BASE = {"id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "demo",
        "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "default_language": "da",
        "license": "MIT", "languages": ["en", "da"], "fdroid": "none", "apk_asset": "Demo.apk"}
GOOD_PAGE = ('<link rel="alternate" hreflang="en" href="x">'
             "<!-- cocode-apps:nav:start --><!-- cocode-apps:nav:end -->"
             "<!-- cocode-apps:install:start --><!-- cocode-apps:install:end -->"
             "<!-- cocode-apps:footer:start --><!-- cocode-apps:footer:end -->")


def app(**over):
    return parse({"apps": [{**BASE, **over}]})[0]


def site_fetch(pages):
    return lambda url: pages.get(url, (404, ""))


def test_complete_site_has_no_gaps():
    pages = {f"https://demo.cocode.dk{p}": (200, GOOD_PAGE) for p in ("/", "/en/", "/privacy/", "/en/privacy/")}
    pages["https://demo.cocode.dk/sitemap.xml"] = (200, "<urlset/>")
    assert check_site(app(), site_fetch(pages)) == []


def test_missing_privacy_and_markers_are_gaps():
    pages = {"https://demo.cocode.dk/": (200, "<html>no markers</html>")}
    messages = " | ".join(g.message for g in check_site(app(), site_fetch(pages)))
    assert "privacy" in messages and "install block" in messages and "navigation" in messages


def test_unreachable_site_is_one_gap_not_a_crash():
    gaps = check_site(app(), lambda url: (0, ""))
    assert len(gaps) == 1 and "unreachable" in gaps[0].message


def test_release_asset_must_download():
    assert check_release(app(), lambda url: (200, "")) == []
    assert "Demo.apk" in check_release(app(), lambda url: (404, ""))[0].message


def test_fdroid_state_must_match_fdroid_org():
    def listed(url):
        return 200, "{}"

    assert "live" in check_fdroid(app(fdroid="mr:5"), listed)[0].message
    assert check_fdroid(app(fdroid="live"), listed) == []
    assert "not listed" in check_fdroid(app(fdroid="live"), lambda url: (404, ""))[0].message


def test_unreachable_fdroid_is_one_gap_whatever_apps_yml_says():
    for state in ("live", "none", "mr:5"):
        assert check_fdroid(app(fdroid=state), lambda url: (0, "")) == [
            Gap("demo", "fdroid", "f-droid.org unreachable")]
