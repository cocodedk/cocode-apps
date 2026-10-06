from tools.registry import parse
from tools.render import apply, replace_block

S, E = "<!-- cocode-apps:install:start -->", "<!-- cocode-apps:install:end -->"
BASE = {"id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "demo",
        "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "default_language": "da",
        "license": "MIT", "languages": ["en", "da"], "fdroid": "live", "apk_asset": "Demo.apk"}


def test_replaces_only_between_markers():
    text = f"before\n{S}\nold\n{E}\nafter"
    new, state = replace_block(text, "install", "NEW")
    assert state == "ok" and new == f"before\n{S}\nNEW\n{E}\nafter"


def test_missing_markers_change_nothing():
    assert replace_block("plain", "install", "NEW") == ("plain", "missing")


def test_broken_markers_change_nothing():
    for text in (f"{S} only", f"{E} then {S}"):
        assert replace_block(text, "install", "NEW") == (text, "broken")


def test_apply_writes_readme_and_site_and_copies_badges(tmp_path):
    app = parse({"apps": [BASE]})[0]
    (tmp_path / "README.md").write_text(f"# Demo\n{S}\n{E}\n")
    site = tmp_path / "website"
    (site / "en").mkdir(parents=True)
    for page in (site / "index.html", site / "en" / "index.html"):
        page.write_text(f"<main>{S}{E}</main>")
    report = apply(app, tmp_path)
    assert "f-droid.org/packages/dk.cocode.demo/" in (tmp_path / "README.md").read_text()
    assert "Hent den på F-Droid" in (site / "index.html").read_text()
    assert "Get it on F-Droid" in (site / "en" / "index.html").read_text()
    assert (site / "img" / "get-it-on-fdroid-da.png").is_file()
    assert any("missing" in line for line in report)  # nav/footer markers absent in this fixture


def test_dry_run_writes_nothing(tmp_path):
    app = parse({"apps": [BASE]})[0]
    (tmp_path / "README.md").write_text(f"{S}\n{E}")
    apply(app, tmp_path, write=False)
    assert (tmp_path / "README.md").read_text() == f"{S}\n{E}"


def test_no_badge_copy_on_dry_run_or_when_not_live(tmp_path):
    live, soon = (parse({"apps": [{**BASE, "fdroid": f}]})[0] for f in ("live", "none"))
    apply(live, tmp_path, write=False)
    apply(soon, tmp_path)
    assert not (tmp_path / "website" / "img").exists()


def test_write_copies_the_stylesheet_even_when_not_live(tmp_path):
    soon = parse({"apps": [{**BASE, "fdroid": "none"}]})[0]
    apply(soon, tmp_path)
    css = tmp_path / "website" / "css" / "cocode-nav.css"
    assert css.is_file() and ".cocode-nav" in css.read_text()


def test_dry_run_copies_no_stylesheet(tmp_path):
    apply(parse({"apps": [BASE]})[0], tmp_path, write=False)
    assert not (tmp_path / "website").exists()


def test_privacy_page_gets_the_nav_with_aria_current_on_privacy(tmp_path):
    app = parse({"apps": [BASE]})[0]
    page = tmp_path / "website" / "privacy" / "index.html"
    page.parent.mkdir(parents=True)
    page.write_text("<!-- cocode-apps:nav:start --><!-- cocode-apps:nav:end -->")
    apply(app, tmp_path)
    html = page.read_text()
    assert html.count('aria-current="page"') == 1 and 'data-nav="privacy" aria-current="page"' in html


def test_catalogue_flag_needs_no_app(monkeypatch, tmp_path):
    from tools import catalogue
    from tools.render import main
    page = tmp_path / "catalogue.html"
    page.write_text("<li></li>")
    monkeypatch.setattr(catalogue, "CATALOGUE_FILE", page)
    monkeypatch.setattr(catalogue, "WORKS_FILE", tmp_path / "works.html")  # absent: skipped
    assert main(["--catalogue", "--dry-run"]) == 0
