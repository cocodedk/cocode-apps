import pytest

from tools.registry import RegistryError, find, load, parse

PUBLIC = {
    "id": "demo", "name": {"en": "Demo", "da": "Demo"}, "repo": "demo-android", "checkout": "demo-android",
    "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "site_dir": "website",
    "default_language": "da", "privacy": "https://demo.cocode.dk/privacy/", "license": "Apache-2.0",
    "languages": ["en", "da"], "fdroid": "mr:123", "apk_asset": "Demo.apk",
}


def one(**over):
    return parse({"apps": [{**PUBLIC, **over}]})[0]


def test_public_app_parses_with_derived_urls():
    app = one()
    assert app.application_id == "dk.cocode.demo"
    assert app.fdroid_url == "https://f-droid.org/packages/dk.cocode.demo/"
    assert app.apk_url == "https://github.com/cocodedk/demo-android/releases/latest/download/Demo.apk"
    assert not app.fdroid_live and one(fdroid="live").fdroid_live


def test_home_paths_follow_default_language():
    app = one()
    assert app.home("da") == "/" and app.home("en") == "/en/"


def test_private_app_keeps_name_only():
    app = parse({"apps": [{"id": "secret", "name": {"en": "S", "da": "S"}, "private": True}]})[0]
    assert app.private and app.repo == ""


def test_private_app_with_details_is_rejected():
    with pytest.raises(RegistryError, match="private"):
        parse({"apps": [{"id": "secret", "name": {"en": "S", "da": "S"}, "private": True, "repo": "x"}]})


@pytest.mark.parametrize("field", ["repo", "checkout", "applicationId", "site", "license", "fdroid", "apk_asset"])
def test_missing_required_field_is_rejected(field):
    data = {**PUBLIC}
    del data[field]
    with pytest.raises(RegistryError, match=field):
        parse({"apps": [data]})


@pytest.mark.parametrize("value", ["published", "mr:", "mr:abc", "LIVE"])
def test_bad_fdroid_value_is_rejected(value):
    with pytest.raises(RegistryError, match="fdroid"):
        one(fdroid=value)


def test_duplicate_ids_are_rejected():
    with pytest.raises(RegistryError, match="duplicate"):
        parse({"apps": [PUBLIC, PUBLIC]})


def test_non_https_site_and_non_apk_asset_are_rejected():
    with pytest.raises(RegistryError, match="https"):
        one(site="http://demo.cocode.dk")
    with pytest.raises(RegistryError, match=".apk"):
        one(apk_asset="Demo.zip")


def test_find_unknown_app_raises():
    with pytest.raises(RegistryError, match="unknown"):
        find([one()], "nope")


def test_shipped_registry_loads():
    apps = load()
    assert len(apps) == 16
    assert sum(a.private for a in apps) == 1


def test_shipped_registry_facts():
    apps = load()
    assert find(apps, "persian-calendar").checkout == "Calendar"
    assert find(apps, "persian-calendar").site_dir == "docs"
    assert find(apps, "battleship").fdroid_live
    assert find(apps, "babakcast").fdroid == "mr:49562"
    assert find(apps, "guard-android").home("da") == "/"
    for app in apps:
        if not app.private:
            assert app.apk_url.endswith("/releases/latest/download/" + app.apk_asset)
