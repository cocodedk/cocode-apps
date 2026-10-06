from tools.catalogue import apply_all, apply_catalogue, catalogue_html, check_catalogue
from tools.registry import parse

BASE = {"id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "demo",
        "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "license": "MIT",
        "languages": ["en", "da"], "fdroid": "live", "apk_asset": "Demo.apk"}
SECRET = {"id": "secret", "name": {"en": "S", "da": "S"}, "private": True}
S, E = "<!-- cocode-apps:get-demo:start -->", "<!-- cocode-apps:get-demo:end -->"


def apps(**over):
    return parse({"apps": [{**BASE, **over}, SECRET]})


def test_live_app_links_fdroid_in_danish():
    html = catalogue_html(apps()[0])
    assert 'href="https://f-droid.org/packages/dk.cocode.demo/"' in html and "Hent på F-Droid" in html


def test_app_not_on_fdroid_links_the_apk():
    html = catalogue_html(apps(fdroid="mr:3")[0])
    assert "releases/latest/download/Demo.apk" in html and "Hent APK" in html and "f-droid" not in html


def test_apply_fills_markers_and_skips_private_apps(tmp_path):
    page = tmp_path / "catalogue.html"
    page.write_text(f"<li>Demo {S}{E}</li>")
    report = apply_catalogue(apps(), page)
    assert "Hent på F-Droid" in page.read_text()
    assert not any("secret" in line for line in report)


def test_missing_marker_is_reported_and_is_an_audit_gap(tmp_path):
    page = tmp_path / "catalogue.html"
    page.write_text("<li>Demo</li>")
    assert any("missing" in line for line in apply_catalogue(apps(), page))
    assert "cocode.dk" in check_catalogue(apps()[0], page)[0].message


def test_featured_work_gets_the_work_class_and_counts_as_ok(tmp_path):
    listing, works = tmp_path / "catalogue.html", tmp_path / "works.html"
    listing.write_text("<li>Other</li>")
    works.write_text(f'<a class="work__link" href="x">x</a>{S}{E}')
    report = apply_all(apps(), [listing, works, tmp_path / "absent.html"])
    assert report == ["cocode.dk catalogue [demo]: ok"]
    assert 'class="work__get"' in works.read_text() and "index__get" not in works.read_text()
    assert check_catalogue(apps()[0], [listing, works]) == []


def test_app_in_neither_partial_is_missing(tmp_path):
    listing, works = tmp_path / "catalogue.html", tmp_path / "works.html"
    listing.write_text("<li>Other</li>")
    works.write_text("<article>Other</article>")
    assert apply_all(apps(), [listing, works]) == ["cocode.dk catalogue [demo]: missing"]
    assert check_catalogue(apps()[0], [listing, works])[0].area == "cocode.dk"
