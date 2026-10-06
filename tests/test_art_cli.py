import pytest
from art_helpers import APPS, app_with_adaptive, put

from tools import art
from tools.art_icon import find_icon
from tools.registry import parse


def test_feature_graphic_escapes_name_and_tagline_and_uses_no_network(tmp_path):
    app_with_adaptive(tmp_path)
    html = art.feature_graphic_html(find_icon(tmp_path), 'Demo <App> & "Co"', "<script>x</script> it's")
    assert "Demo &lt;App&gt; &amp; &quot;Co&quot;" in html
    assert "&lt;script&gt;x&lt;/script&gt; it&#x27;s" in html and "<script>" not in html
    assert "http" not in html and "{{" not in html
    assert "#070b14" in html  # the icon's background colour


def test_unknown_background_is_a_dark_neutral(tmp_path):
    put(tmp_path, "app/src/main/ic_launcher-playstore.png", b"STORE")
    html = art.feature_graphic_html(find_icon(tmp_path), "Demo", "")
    assert "#1d232a" in html and "color: #ffffff" in html and "<p></p>" in html


def test_text_contrasts_with_the_background():
    assert art.text_color((255, 250, 240, 1.0)) == art.NEAR_BLACK  # light background, dark text
    assert art.text_color((7, 11, 20, 1.0)) == art.WHITE
    assert art.contrast(art.WHITE, (0, 0, 0, 1.0)) == pytest.approx(21)
    assert art.text_color((244, 184, 96, 1.0)) == art.NEAR_BLACK  # amber


def test_tagline_is_the_first_line_of_the_short_description(tmp_path):
    assert art.read_tagline(tmp_path) == ""
    put(tmp_path, "fastlane/metadata/android/en-US/short_description.txt", "\n First line \nsecond\n")
    assert art.read_tagline(tmp_path) == "First line"


@pytest.fixture
def cli(tmp_path, monkeypatch):
    """Registry with a public and a private app; rasterize writes a real PNG of the asked size."""
    from PIL import Image

    calls = []

    def fake_rasterize(html, width, height, out):
        calls.append((html, width, height))
        Image.new("RGBA", (width, height), (10, 20, 30, 255)).save(out)

    monkeypatch.setattr(art, "load", lambda: parse(APPS))
    monkeypatch.setattr(art, "rasterize", fake_rasterize)
    root = tmp_path / "demo"
    app_with_adaptive(root)
    return root, calls


def test_cli_writes_the_three_files_and_nothing_else(cli, capsys):
    root, calls = cli
    put(root, "fastlane/metadata/android/en-US/short_description.txt", "Tiny & fast\nmore")
    put(root, "website/index.html", "keep me")
    assert art.main(["demo", "--root", str(root)]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "wrote fastlane/metadata/android/en-US/images/icon.png",
        "wrote website/img/icon.png",
        "wrote fastlane/metadata/android/en-US/images/featureGraphic.png",
    ]
    from PIL import Image

    images = root / "fastlane/metadata/android/en-US/images"
    for path, size, mode in ((images / "icon.png", (512, 512), "RGBA"), (root / "website/img/icon.png", (512, 512), "RGBA"),
                             (images / "featureGraphic.png", (1024, 500), "RGB")):
        with Image.open(path) as image:
            assert (image.size, image.mode) == (size, mode)
    assert [(w, h) for _, w, h in calls] == [(512, 512), (1024, 500)]
    assert "Demo &lt;App&gt;" in calls[1][0] and "Tiny &amp; fast" in calls[1][0]
    assert (root / "website/index.html").read_text() == "keep me"
    assert sorted(p.name for p in root.rglob("*.png")) == ["featureGraphic.png", "icon.png", "icon.png"]


def test_cli_tagline_option_beats_the_short_description(cli):
    root, calls = cli
    put(root, "fastlane/metadata/android/en-US/short_description.txt", "From file")
    assert art.main(["demo", "--root", str(root), "--tagline", "From option"]) == 0
    assert "From option" in calls[1][0] and "From file" not in calls[1][0]


def test_cli_skips_a_private_app(cli, capsys):
    root, calls = cli
    assert art.main(["secret", "--root", str(root)]) == 0
    assert capsys.readouterr().out == "secret: private, skipped\n" and calls == []


def test_cli_exits_1_naming_what_is_missing_and_writes_nothing(tmp_path, cli, capsys):
    _, calls = cli
    empty = tmp_path / "empty"
    empty.mkdir()
    assert art.main(["demo", "--root", str(empty)]) == 1
    assert "ic_launcher-playstore.png" in capsys.readouterr().err
    assert calls == [] and list(empty.rglob("*")) == []


def test_cli_rejects_a_screenshot_of_the_wrong_size(cli, monkeypatch, capsys):
    from PIL import Image

    root, _ = cli
    monkeypatch.setattr(art, "rasterize", lambda html, w, h, out: Image.new("RGBA", (w + 1, h)).save(out))
    assert art.main(["demo", "--root", str(root)]) == 1
    assert "expected 512x512" in capsys.readouterr().err
    assert not (root / "fastlane/metadata/android/en-US/images").exists()


def test_cli_unknown_app_exits_1(cli, capsys):
    assert art.main(["nope"]) == 1 and "unknown app" in capsys.readouterr().err
