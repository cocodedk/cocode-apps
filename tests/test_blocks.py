import re

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


def test_sub_path_site_keeps_every_link_under_its_base():
    a = app(site="https://cocodedk.github.io/Claude-Email-App", fdroid="live")
    for lang in ("en", "da"):
        for html in (nav_html(a, lang), nav_html(a, lang, "privacy"), footer_html(a, lang), install_html(a, lang)):
            links = re.findall(r'(?:href|src)="([^"]*)"', html)
            assert links
            for link in links:
                assert link.startswith(("/Claude-Email-App/", "https://", "#")), link


def test_nav_marks_only_the_current_page():
    home = nav_html(app(), "en")
    assert home.count('aria-current="page"') == 1 and 'data-nav="home" aria-current="page"' in home
    privacy = nav_html(app(), "en", current="privacy")
    assert privacy.count('aria-current="page"') == 1 and 'data-nav="privacy" aria-current="page"' in privacy


def test_nav_has_data_nav_in_order_icon_and_stylesheet_first():
    html = nav_html(app(), "en")
    assert re.findall(r'data-nav="(\w+)"', html) == ["home", "how", "install", "privacy", "lang", "more"]
    assert html.startswith('<link rel="stylesheet" href="/css/cocode-nav.css">\n<a class="skip"')
    assert '<img src="/img/icon.png" alt="" width="32" height="32">Demo' in html


def css_rules():
    from tools.registry import ROOT
    text = re.sub(r"/\*.*?\*/", "", (ROOT / "templates/cocode-nav.css").read_text("utf-8"), flags=re.DOTALL)
    return {" ".join(sel.split()): body for sel, body in re.findall(r"([^{}]+)\{([^}]*)\}", text)}


def test_stylesheet_sizes_wraps_and_shows_the_skip_link():
    rules = css_rules()
    targets = next(body for sel, body in rules.items() if ".cocode-nav a" in sel and ".cocode-footer a" in sel
                   and ":focus" not in sel)
    for prop in ("display: inline-flex", "min-height: 44px", "min-width: 44px", "align-items: center",
                 "justify-content: center"):
        assert prop in targets
    assert "flex-wrap: wrap" in rules[".cocode-nav"] and "display: flex" in rules[".cocode-nav"]
    assert "flex: 1 0 100%" in rules[".cocode-nav .brand"]
    assert "justify-content: flex-start" in rules[".cocode-nav .brand"]
    assert "@media (min-width: 48em)" in rules  # one row on wide screens
    assert re.search(r"left:\s*-\d{4,}px", rules[".skip"])
    assert re.search(r"left:\s*0\b", rules[".skip:focus"])


def test_stylesheet_focus_uses_current_colour_and_nothing_hides_or_colours():
    rules = css_rules()
    focus = next(body for sel, body in rules.items() if ":focus-visible" in sel)
    assert "outline: 2px solid currentColor" in focus
    everything = "".join(rules.values())
    assert not re.search(r"display:\s*none|visibility:\s*hidden|font|#[0-9a-fA-F]{3}|rgb|hsl", everything)
    values = re.findall(r"(?<![\w-])(?:background-)?color:\s*([^;]+);", everything)
    assert set(values) <= {"inherit", "currentColor"}


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
