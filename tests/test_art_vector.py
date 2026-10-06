from xml.etree import ElementTree as ET

from tools.art_res import Res, css, parse_hex, parse_ref
from tools.art_vector import VectorSvg, first_color

NS = 'xmlns:android="http://schemas.android.com/apk/res/android" xmlns:aapt="http://schemas.android.com/aapt"'


def vector(inner: str, size: int = 108) -> ET.Element:
    return ET.fromstring(
        f'<vector {NS} android:width="{size}dp" android:height="{size}dp" '
        f'android:viewportWidth="{size}" android:viewportHeight="{size}">{inner}</vector>'
    )


def res_with_colors(tmp_path, colors: str) -> Res:
    (tmp_path / "res" / "values").mkdir(parents=True)
    (tmp_path / "res" / "values" / "colors.xml").write_text(f"<resources>{colors}</resources>")
    return Res(tmp_path)


def test_android_colors_put_alpha_first():
    assert parse_hex("#80FF0000") == (255, 0, 0, 0.502)
    assert parse_hex("#F00") == (255, 0, 0, 1.0)
    assert parse_hex("#8F00") == (255, 0, 0, 0.533)
    assert parse_hex("#00000000") == (0, 0, 0, 0.0)
    assert parse_hex("red") is None and parse_hex("#12345") is None


def test_css_rgba():
    assert css(parse_hex("#80FF0000")) == "rgba(255,0,0,0.502)"
    assert css(parse_hex("#35C47C")) == "rgba(53,196,124,1)"
    assert css(parse_hex("#00000000")) == "rgba(0,0,0,0)"


def test_color_references_resolve_through_values_folders(tmp_path):
    res = res_with_colors(tmp_path, '<color name="night">#070B14</color><color name="alias">@color/night</color>')
    (tmp_path / "res" / "values-sv").mkdir()
    (tmp_path / "res" / "values-sv" / "extra.xml").write_text('<resources><color name="x">#FFF</color></resources>')
    assert res.color("@color/night") == (7, 11, 20, 1.0)
    assert res.color("@color/alias") == (7, 11, 20, 1.0)
    assert res.color("@color/x") == (255, 255, 255, 1.0)
    assert res.color("@android:color/white") == (255, 255, 255, 1.0)
    assert res.color("@color/missing") is None and res.color("?attr/colorPrimary") is None


def test_parse_ref():
    assert parse_ref("@mipmap/ic_launcher") == ("mipmap", "ic_launcher")
    assert parse_ref("@drawable/x") == ("drawable", "x")
    assert parse_ref("#fff") is None and parse_ref(None) is None


def test_vector_path_becomes_svg_path(tmp_path):
    root = vector(
        '<path android:pathData="M0,0 L10,0\n L10,10z" android:fillColor="#80FF0000" android:fillType="evenOdd"/>'
        '<path android:pathData="M1,1L2,2" android:strokeColor="#FF00FF00" android:strokeWidth="3" '
        'android:strokeAlpha="0.5" android:strokeLineCap="round" android:fillColor="#00000000"/>'
    )
    markup, vw, vh = VectorSvg(Res(tmp_path)).convert(root)
    assert (vw, vh) == (108, 108)
    assert 'd="M0,0 L10,0 L10,10z"' in markup  # whitespace collapsed
    assert 'fill="rgba(255,0,0,0.502)"' in markup and 'fill-rule="evenodd"' in markup
    assert 'stroke="rgba(0,255,0,1)"' in markup and 'stroke-width="3"' in markup
    assert 'stroke-opacity="0.5"' in markup and 'stroke-linecap="round"' in markup


def test_unknown_color_reference_is_skipped_not_painted(tmp_path):
    markup, _, _ = VectorSvg(Res(tmp_path)).convert(
        vector('<path android:pathData="M0,0h5v5z" android:fillColor="?attr/colorPrimary" '
               'android:strokeColor="@color/nope" android:strokeWidth="2"/>')
    )
    assert 'fill="none"' in markup and "stroke=" not in markup


def test_group_transform_follows_androids_order(tmp_path):
    root = vector(
        '<group android:translateX="10" android:translateY="5" android:scaleX="2" android:scaleY="3" '
        'android:rotation="45" android:pivotX="4" android:pivotY="6">'
        '<path android:pathData="M0,0h1v1z" android:fillColor="#000"/></group>'
    )
    markup, _, _ = VectorSvg(Res(tmp_path)).convert(root)
    assert 'transform="translate(14 11) rotate(45) scale(2 3) translate(-4 -6)"' in markup


def test_group_with_only_a_translation_and_a_plain_group(tmp_path):
    root = vector(
        '<group android:translateX="10" android:pivotX="4"><path android:pathData="M0,0h1v1z"/></group>'
        '<group><path android:pathData="M0,0h2v2z"/></group>'
    )
    markup, _, _ = VectorSvg(Res(tmp_path)).convert(root)
    assert 'transform="translate(10 0)"' in markup
    assert "<g>" in markup  # no identity transform written


def test_clip_path_clips_what_follows_inside_its_group(tmp_path):
    root = vector(
        '<group android:translateX="2"><clip-path android:pathData="M0,0h5v5z"/>'
        '<path android:pathData="M0,0h9v9z" android:fillColor="#000"/></group>'
    )
    markup, _, _ = VectorSvg(Res(tmp_path), "t").convert(root)
    assert '<clipPath id="t-clip1"><path d="M0,0h5v5z"/></clipPath>' in markup
    assert '<g clip-path="url(#t-clip1)"><path d="M0,0h9v9z"' in markup
    assert markup.count("<g") == markup.count("</g>")


def test_linear_gradient_fill(tmp_path):
    root = vector(
        '<path android:pathData="M0,0h108v108H0z"><aapt:attr name="android:fillColor">'
        '<gradient android:type="linear" android:startX="0" android:startY="0" android:endX="108" android:endY="108">'
        '<item android:offset="0" android:color="#FF0C1220"/><item android:offset="1" android:color="#80243753"/>'
        "</gradient></aapt:attr></path>"
    )
    res = Res(tmp_path)
    markup, _, _ = VectorSvg(res).convert(root)
    assert '<linearGradient id="v-grad1" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="108" y2="108">' in markup
    assert '<stop offset="0" stop-color="#0c1220" stop-opacity="1"/>' in markup
    assert '<stop offset="1" stop-color="#243753" stop-opacity="0.502"/>' in markup
    assert 'fill="url(#v-grad1)"' in markup
    assert first_color(root, res) == (12, 18, 32, 1.0)


def test_first_color_is_the_first_visible_fill(tmp_path):
    root = vector(
        '<path android:pathData="M0,0h1v1z" android:fillColor="#00000000"/>'
        '<path android:pathData="M0,0h108v108H0z" android:fillColor="#161A22"/>'
        '<path android:pathData="M0,0h2v2z" android:fillColor="#F4B860"/>'
    )
    assert first_color(root, Res(tmp_path)) == (22, 26, 34, 1.0)
