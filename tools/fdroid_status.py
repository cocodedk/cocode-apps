"""Ask f-droid.org which apps are live; update apps.yml. Never downgrades a live app."""
import yaml

from tools.checks import Fetch
from tools.net import fetch as real_fetch
from tools.registry import ROOT, parse

API = "https://f-droid.org/api/v1/packages/{}"


def refresh(data: dict, fetch: Fetch) -> list[str]:
    turned = []
    for raw in data.get("apps", []):
        if raw.get("private") or raw.get("fdroid") == "live":
            continue
        if fetch(API.format(raw["applicationId"]))[0] == 200:
            raw["fdroid"] = "live"
            turned.append(raw["id"])
    return turned


def main() -> int:
    path = ROOT / "apps.yml"
    data = yaml.safe_load(path.read_text("utf-8"))
    turned = refresh(data, real_fetch)
    if turned:
        parse(data)  # still valid before writing
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), "utf-8")
    print("now live: " + (", ".join(turned) or "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
