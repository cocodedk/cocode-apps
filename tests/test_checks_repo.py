from tools.checks.repo import check_fastlane, check_inapp, check_readme, check_repo
from tools.registry import parse

BASE = {"id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "demo",
        "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk",
        "privacy": "https://demo.cocode.dk/privacy/", "default_language": "da", "license": "MIT",
        "languages": ["en", "da"], "fdroid": "none", "apk_asset": "Demo.apk"}
APP = parse({"apps": [BASE]})[0]


def full_fastlane(root, code="1001"):
    (root / "gradle.properties").write_text(f"VERSION_NAME=0.1.0\nVERSION_CODE={code}\n")
    for loc in ("en-US", "da-DK"):
        d = root / "fastlane/metadata/android" / loc
        (d / "changelogs").mkdir(parents=True)
        for f in ("title.txt", "short_description.txt", "full_description.txt"):
            (d / f).write_text("x")
        (d / "changelogs" / f"{code}.txt").write_text("x")
    img = root / "fastlane/metadata/android/en-US/images"
    (img / "phoneScreenshots").mkdir(parents=True)
    for f in ("icon.png", "featureGraphic.png", "phoneScreenshots/1.png", "phoneScreenshots/2.png"):
        (img / f).write_bytes(b"png")


def test_complete_fastlane_has_no_gaps(tmp_path):
    full_fastlane(tmp_path)
    assert check_fastlane(APP, tmp_path) == []


def test_missing_danish_changelog_and_screenshots_are_gaps(tmp_path):
    full_fastlane(tmp_path)
    (tmp_path / "fastlane/metadata/android/da-DK/changelogs/1001.txt").unlink()
    for shot in (tmp_path / "fastlane/metadata/android/en-US/images/phoneScreenshots").iterdir():
        shot.unlink()
    messages = " | ".join(g.message for g in check_fastlane(APP, tmp_path))
    assert "da-DK" in messages and "screenshots" in messages


def test_non_literal_version_code_is_a_gap(tmp_path):
    full_fastlane(tmp_path)
    (tmp_path / "gradle.properties").write_text("VERSION_CODE=${CODE}\n")
    assert any("VERSION_CODE" in g.message for g in check_fastlane(APP, tmp_path))


def test_readme_needs_the_install_marker(tmp_path):
    (tmp_path / "README.md").write_text("# Demo")
    assert "install block" in check_readme(APP, tmp_path)[0].message


def test_inapp_needs_about_screen_privacy_link_and_both_languages(tmp_path):
    src = tmp_path / "app/src/main"
    (src / "java/dk/cocode/demo/ui").mkdir(parents=True)
    (src / "res/values").mkdir(parents=True)
    (src / "res/values/strings.xml").write_text("<resources/>")
    messages = " | ".join(g.message for g in check_inapp(APP, tmp_path))
    assert "About" in messages and "privacy" in messages and "values-en" in messages


def test_missing_checkout_is_one_gap(tmp_path):
    gaps = check_repo(APP, tmp_path / "nope")
    assert len(gaps) == 1 and "checkout missing" in gaps[0].message
