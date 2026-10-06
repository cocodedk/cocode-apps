import pytest
from art_helpers import ADAPTIVE, FOREGROUND, MANIFEST, NS, app_with_adaptive, put, uri

from tools.art_icon import find_icon, manifest_icon
from tools.art_res import ArtError


def test_manifest_icon_is_the_applications_icon(tmp_path):
    put(tmp_path, "app/src/main/AndroidManifest.xml", MANIFEST.format(icon="@mipmap/ic_launcher"))
    assert manifest_icon(tmp_path) == "@mipmap/ic_launcher"
    put(tmp_path, "app/src/main/AndroidManifest.xml", MANIFEST.format(icon="@drawable/x"))
    assert manifest_icon(tmp_path) == "@drawable/x"


def test_manifest_icon_is_none_without_a_manifest_or_icon(tmp_path):
    assert manifest_icon(tmp_path) is None
    put(tmp_path, "app/src/main/AndroidManifest.xml", f"<manifest {NS}><application/></manifest>")
    assert manifest_icon(tmp_path) is None


def test_playstore_png_is_preferred_over_everything(tmp_path):
    app_with_adaptive(tmp_path)
    put(tmp_path, "app/src/main/ic_launcher-playstore.png", b"STORE")
    assert uri(b"STORE") in find_icon(tmp_path).body


def test_the_largest_density_raster_wins_among_png_and_webp(tmp_path):
    put(tmp_path, "app/src/main/AndroidManifest.xml", MANIFEST.format(icon="@mipmap/ic_launcher"))
    put(tmp_path, "app/src/main/res/mipmap-mdpi/ic_launcher.png", b"MDPI")
    put(tmp_path, "app/src/main/res/mipmap-xhdpi/ic_launcher.webp", b"XHDPI")
    put(tmp_path, "app/src/main/res/mipmap-hdpi/ic_launcher.png", b"HDPI")
    assert uri(b"XHDPI", "webp") in find_icon(tmp_path).body
    put(tmp_path, "app/src/main/res/mipmap-xxxhdpi/ic_launcher.png", b"XXXHDPI")
    assert uri(b"XXXHDPI") in find_icon(tmp_path).body


def test_drawable_density_folders_count_too(tmp_path):
    put(tmp_path, "app/src/main/AndroidManifest.xml", MANIFEST.format(icon="@drawable/logo"))
    put(tmp_path, "app/src/main/res/drawable-hdpi/logo.png", b"HDPI")
    put(tmp_path, "app/src/main/res/drawable-xxhdpi/logo.png", b"XXHDPI")
    assert uri(b"XXHDPI") in find_icon(tmp_path).body


def test_the_adaptive_icon_beats_legacy_densities_which_are_often_the_studio_default(tmp_path):
    app_with_adaptive(tmp_path)
    put(tmp_path, "app/src/main/res/mipmap-xxxhdpi/ic_launcher.webp", b"ANDROID ROBOT")
    icon = find_icon(tmp_path)
    assert "ANDROID" not in icon.body and 'd="M54,28 L76,36z"' in icon.body


def test_adaptive_icon_with_colour_background_and_vector_foreground(tmp_path):
    app_with_adaptive(tmp_path)
    icon = find_icon(tmp_path)
    assert 'd="M54,28 L76,36z"' in icon.body and 'fill="rgba(53,196,124,1)"' in icon.body
    assert 'fill="rgba(7,11,20,1)"' in icon.body  # the @color/night background layer
    assert icon.background == (7, 11, 20, 1.0)
    assert icon.box == (18, 18, 72, 72)  # the centre 72dp of the 108dp layers


def test_adaptive_icon_with_a_literal_or_vector_background(tmp_path):
    app_with_adaptive(tmp_path, bg="#80112233")
    assert find_icon(tmp_path).background == (17, 34, 51, 0.502)
    app_with_adaptive(tmp_path, bg="@drawable/ic_launcher_background")
    put(tmp_path, "app/src/main/res/drawable/ic_launcher_background.xml", FOREGROUND.replace("#35C47C", "#161A22"))
    icon = find_icon(tmp_path)
    assert icon.background == (22, 26, 34, 1.0) and 'fill="rgba(22,26,34,1)"' in icon.body


def test_adaptive_icon_with_a_raster_foreground(tmp_path):
    app_with_adaptive(tmp_path)
    put(tmp_path, "app/src/main/res/drawable/ic_launcher_foreground.xml", "<resources/>")  # not a vector
    put(tmp_path, "app/src/main/res/mipmap-xxxhdpi/ic_launcher_foreground.png", b"FG")
    put(tmp_path, "app/src/main/res/mipmap-anydpi/ic_launcher.xml",
        ADAPTIVE.format(bg="@color/night").replace("@drawable/ic_launcher_foreground", "@mipmap/ic_launcher_foreground"))
    assert uri(b"FG") in find_icon(tmp_path).body


def test_a_plain_vector_icon_is_rendered_whole(tmp_path):
    put(tmp_path, "app/src/main/AndroidManifest.xml", MANIFEST.format(icon="@drawable/ic_app_icon"))
    put(tmp_path, "app/src/main/res/drawable/ic_app_icon.xml", FOREGROUND.replace("108", "24"))
    icon = find_icon(tmp_path)
    assert icon.box == (0, 0, 24, 24) and icon.background is None and "M54,28" in icon.body


def test_no_icon_names_what_was_looked_for(tmp_path):
    put(tmp_path, "app/src/main/AndroidManifest.xml", MANIFEST.format(icon="@mipmap/ic_launcher"))
    with pytest.raises(ArtError) as error:
        find_icon(tmp_path)
    for word in ("ic_launcher-playstore.png", "AndroidManifest.xml", "@mipmap/ic_launcher", "adaptive", "vector"):
        assert word in str(error.value)


def test_icon_svg_has_the_requested_size_and_an_18_percent_corner(tmp_path):
    app_with_adaptive(tmp_path)
    svg = find_icon(tmp_path).svg(512)
    assert svg.startswith('<svg width="512" height="512" viewBox="0 0 100 100">')
    assert 'rx="18"' in svg and 'viewBox="18 18 72 72"' in svg and "http" not in svg
