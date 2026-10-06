from tools.blocks import catalogue_link, footer_html, install_html, install_md, nav_html
from tools.catalogue import catalogue_html
from tools.registry import load, parse

BASE = {"id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "d",
        "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "default_language": "da",
        "license": "MIT", "languages": ["en", "da"], "fdroid": "none", "apk_asset": "Demo.apk"}


def app(**over):
    return parse({"apps": [{**BASE, **over}]})[0]


def test_live_app_links_the_fdroid_badge_first():
    html = install_html(app(fdroid="live"), "en")
    assert html.index("f-droid.org/packages/dk.cocode.demo/") < html.index("releases/latest/download/Demo.apk")
    assert 'src="/img/get-it-on-fdroid-en.png"' in html and 'alt="Get it on F-Droid"' in html


def test_app_not_on_fdroid_has_no_dead_badge_link():
    html = install_html(app(fdroid="mr:5"), "da")
    assert "f-droid.org/packages" not in html and "Kommer på F-Droid" in html


def test_obtainium_link_points_at_the_repo():
    assert "obtainium://add/https://github.com/cocodedk/demo-android" in install_html(app(), "en")
    assert "Obtainium" not in install_html(app(obtainium=False), "en")


def test_markdown_block_mirrors_html_order():
    md = install_md(app(fdroid="live"), "en")
    assert md.index("f-droid.org") < md.index("Demo.apk")


def test_nav_has_six_items_in_order_with_language_paths():
    html = nav_html(app(), "en")
    order = ["Demo", "How it works", "Install", "Privacy", "Dansk", "More apps"]
    positions = [html.index(label) for label in order]
    assert positions == sorted(positions)
    assert 'href="/en/privacy/"' in html and 'href="/"' in html and 'lang="da"' in html


def test_footer_names_source_license_and_cocode():
    html = footer_html(app(), "da")
    assert "github.com/cocodedk/demo-android" in html and "MIT" in html and "cocode.dk" in html


def test_catalogue_link_prefers_fdroid_when_live():
    assert catalogue_link(app(fdroid="live")).startswith("https://f-droid.org/packages/")
    assert catalogue_link(app()).endswith("/Demo.apk")


def test_no_block_names_spamhaus():
    for a in (a for a in load() if not a.private):
        texts = [catalogue_html(a)] + [f(a, lang) for f in (install_html, install_md, nav_html, footer_html)
                                       for lang in ("en", "da")]
        assert not any("spamhaus" in text.lower() for text in texts), a.id
