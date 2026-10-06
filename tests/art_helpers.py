"""Fixtures for the artwork tests: a tiny app checkout written into tmp_path."""
import base64

NS = 'xmlns:android="http://schemas.android.com/apk/res/android"'
MANIFEST = f'<manifest {NS}><application android:icon="{{icon}}" android:label="x"/></manifest>'
ADAPTIVE = (f'<adaptive-icon {NS}><background android:drawable="{{bg}}"/>'
            '<foreground android:drawable="@drawable/ic_launcher_foreground"/></adaptive-icon>')
FOREGROUND = (f'<vector {NS} android:width="108dp" android:height="108dp" android:viewportWidth="108" '
              'android:viewportHeight="108"><path android:fillColor="#35C47C" android:pathData="M54,28 L76,36z"/></vector>')
APPS = {"apps": [
    {"id": "demo", "name": {"en": "Demo <App>", "da": "Demo"}, "repo": "demo", "checkout": "demo",
     "applicationId": "dk.cocode.demo", "site": "https://demo.cocode.dk", "license": "MIT",
     "languages": ["en"], "fdroid": "none", "apk_asset": "Demo.apk"},
    {"id": "secret", "name": {"en": "Secret", "da": "Secret"}, "private": True},
]}


def put(root, rel: str, content: str | bytes = "") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode())


def app_with_adaptive(root, bg="@color/night", colors='<color name="night">#070B14</color>') -> None:
    main = "app/src/main/"
    put(root, main + "AndroidManifest.xml", MANIFEST.format(icon="@mipmap/ic_launcher"))
    put(root, main + "res/mipmap-anydpi/ic_launcher.xml", ADAPTIVE.format(bg=bg))
    put(root, main + "res/drawable/ic_launcher_foreground.xml", FOREGROUND)
    put(root, main + "res/values/colors.xml", f"<resources>{colors}</resources>")


def uri(data: bytes, mime: str = "png") -> str:
    return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"
