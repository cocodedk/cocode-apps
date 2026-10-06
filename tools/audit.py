"""Audit apps against the standard and write STATUS.md."""
from __future__ import annotations

import argparse
import datetime
from pathlib import Path

from tools.catalogue import check_catalogue
from tools.checks import Fetch, Gap
from tools.checks.repo import check_repo
from tools.checks.web import check_fdroid, check_release, check_site
from tools.net import fetch as real_fetch
from tools.registry import ROOT, App, find, load

PROJECTS = Path.home() / "0-projects"


def audit_app(app: App, fetch: Fetch, projects: Path) -> list[Gap]:
    if app.private:
        return []
    return (check_site(app, fetch) + check_release(app, fetch) + check_fdroid(app, fetch)
            + check_repo(app, projects / app.checkout)
            + check_catalogue(app, [projects / "cocodedk" / "templates" / "partials" / name
                                    for name in ("catalogue.html", "works.html")]))


def status_markdown(apps: list[App], gaps: dict[str, list[Gap]], date: str) -> str:
    lines = [f"# Status of every Cocode Android app ({date})", "",
             "Written by `python3 -m tools.audit all`. Fewer gaps is better; 0 meets the standard.", "",
             "| App | F-Droid | Gaps | What is missing |", "|---|---|---|---|"]
    for app in apps:
        if app.private:
            lines.append(f"| {app.name_en} | private | – | – |")
            continue
        found = gaps.get(app.id, [])
        listed = "<br>".join(f"{g.area}: {g.message}" for g in found) or "—"
        lines.append(f"| {app.name_en} | {app.fdroid} | {len(found)} | {listed} |")
    return "\n".join(lines) + "\n"


def _today() -> str:
    """Today's date where the audit runs (local time), as YYYY-MM-DD."""
    return datetime.datetime.now(datetime.UTC).astimezone().date().isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Cocode apps against the standard.")
    parser.add_argument("app", help="an app id, or 'all'")
    args = parser.parse_args(argv)
    apps = load()
    chosen = apps if args.app == "all" else [find(apps, args.app)]
    gaps = {app.id: audit_app(app, real_fetch, PROJECTS) for app in chosen}
    for app_id, found in gaps.items():
        print(f"{app_id}: {len(found)} gap(s)")
        for g in found:
            print(f"  - {g.area}: {g.message}")
    if args.app == "all":
        (ROOT / "STATUS.md").write_text(status_markdown(apps, gaps, _today()), "utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
