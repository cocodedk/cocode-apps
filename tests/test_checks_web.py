from tools.checks import Gap
from tools.checks.web import check_fdroid, check_release, check_site
from tools.registry import parse

BASE = {"id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "demo",
        "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "default_language": "da",
        "license": "MIT", "languages": ["en", "da"], "fdroid": "none", "apk_asset": "Demo.apk"}
SITE = "https://demo.cocode.dk"
IMAGE = SITE + "/img/share.png"
ORDER = ("home", "how", "install", "privacy", "lang", "more")


def nav(items=ORDER, current=None):
    here = ' aria-current="page"'
    links = "".join(f'<a href="x" data-nav="{i}"{here if i == current else ""}>x</a>' for i in items)
    return f"<!-- cocode-apps:nav:start -->{links}<!-- cocode-apps:nav:end -->"


def page(items=ORDER, current=None, head=f'<meta property="og:image" content="{IMAGE}">'):
    return ('<link rel="alternate" hreflang="en" href="x">' + head + nav(items, current)
            + "<!-- cocode-apps:install:start --><!-- cocode-apps:install:end -->"
            "<!-- cocode-apps:footer:start --><!-- cocode-apps:footer:end -->")


def app(**over):
    return parse({"apps": [{**BASE, **over}]})[0]


def site_fetch(pages):
    return lambda url: pages.get(url, (404, ""))


def good_pages(changes=None):
    pages = {SITE + p: (200, page()) for p in ("/", "/en/")}
    pages |= {SITE + p: (200, page(current="privacy")) for p in ("/privacy/", "/en/privacy/")}
    pages |= {SITE + p: (200, "x") for p in ("/sitemap.xml", "/img/icon.png", "/css/cocode-nav.css", "/robots.txt")}
    pages[IMAGE] = (200, "png")
    pages |= {k if k.startswith("https://") else SITE + k: v for k, v in (changes or {}).items()}
    return pages


def messages(changes):
    return [g.message for g in check_site(app(), site_fetch(good_pages(changes)))]


def test_complete_site_has_no_gaps():
    assert check_site(app(), site_fetch(good_pages())) == []
    assert check_site(app(), site_fetch(good_pages({"/privacy.html": (404, "")}))) == []


def test_nav_out_of_order_or_missing_an_item_is_one_gap_naming_what_was_found():
    swapped = messages({"/": (200, page(("home", "install", "how", "privacy", "lang", "more")))})
    assert len(swapped) == 1 and "home, install, how" in swapped[0]
    short = messages({"/": (200, page(("home", "how", "install", "privacy", "lang")))})
    assert len(short) == 1 and "home, how, install, privacy, lang," in short[0]
    extra = messages({"/": (200, page(("home", "how", "install", "privacy", "lang", "more", "")))})
    assert len(extra) == 1 and "(empty)" in extra[0]


def test_missing_icon_stylesheet_and_robots_are_one_gap_each():
    for path, word in (("/img/icon.png", "icon"), ("/css/cocode-nav.css", "stylesheet"), ("/robots.txt", "robots")):
        found = messages({path: (404, "")})
        assert len(found) == 1 and word in found[0]


def test_share_image_must_be_declared_and_answer_200():
    missing = messages({"/": (200, page(head=""))})
    assert len(missing) == 1 and "og:image" in missing[0]
    relative = messages({"/": (200, page(head='<meta property="og:image" content="/img/share.png">'))})
    assert len(relative) == 1 and "og:image" in relative[0]
    gone = messages({IMAGE: (404, "")})
    assert len(gone) == 1 and "share image" in gone[0]


def test_old_privacy_html_must_redirect():
    stays = messages({"/privacy.html": (200, "<html>old policy</html>")})
    assert stays == ["privacy.html does not redirect to /privacy/"]
    refresh = '<meta http-equiv="refresh" content="0; url=/privacy/">'
    assert messages({"/privacy.html": (200, f"<head>{refresh}</head>")}) == []
    assert messages({"/privacy.html": (404, "")}) == []
    assert messages({"/privacy.html": (200, page(current="privacy"))}) == []
    assert messages({"/privacy.html": (200, page(current="home"))}) != []


def test_commented_out_html_does_not_count():
    refresh = '<!-- <meta http-equiv="refresh" content="0; url=/privacy/"> -->'
    assert messages({"/privacy.html": (200, refresh)}) != []
    og = f'<!-- <meta property="og:image" content="{IMAGE}"> -->'
    assert any("og:image" in m for m in messages({"/": (200, page(head=og))}))


def test_attribute_text_inside_quoted_values_is_not_an_attribute():
    fake = '<meta name="description" content="Example http-equiv=refresh url=/privacy/">'
    assert messages({"/privacy.html": (200, fake)}) != []
    masked = f'<meta name="d" content="property=og:image"><meta property="og:image" content="{IMAGE}">'
    assert messages({"/": (200, page(head=masked))}) == []


def test_privacy_page_needs_the_privacy_link_inside_a_closed_nav_block():
    outside = ('<!-- cocode-apps:nav:start --><!-- cocode-apps:nav:end -->'
               '<a data-nav="privacy" aria-current="page">x</a>')
    assert messages({"/privacy.html": (200, outside)}) != []
    unclosed = '<!-- cocode-apps:nav:start --><a data-nav="privacy" aria-current="page">x</a>'
    assert messages({"/privacy.html": (200, unclosed)}) != []


def test_unquoted_attributes_and_entities_are_read():
    head = f"<meta content={SITE}/s.png?a=1&amp;b=2 property=og:image>"
    items = "".join(f"<a data-nav={i} href=x>x</a>" for i in ORDER)
    home = ("<!-- cocode-apps:nav:start -->" + items + "<!-- cocode-apps:nav:end -->" + head
            + "hreflang<!-- cocode-apps:install:start --><!-- cocode-apps:footer:start -->")
    assert messages({"/": (200, home), SITE + "/s.png?a=1&b=2": (200, "png")}) == []


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
