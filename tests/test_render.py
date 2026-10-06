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
    assert "Hent på F-Droid" in (site / "index.html").read_text()
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


def test_catalogue_flag_needs_no_app(monkeypatch, tmp_path):
    from tools import catalogue
    from tools.render import main
    page = tmp_path / "catalogue.html"
    page.write_text("<li></li>")
    monkeypatch.setattr(catalogue, "CATALOGUE_FILE", page)
    assert main(["--catalogue", "--dry-run"]) == 0
