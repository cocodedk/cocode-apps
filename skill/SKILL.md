---
name: cocode-apps
description: Brings a Cocode Android app up to the shared publishing standard (About page, privacy page, F-Droid install block, navigation, README, store listing, release routine) using the cocode-apps registry, audit and render tools. Use when making an app's site, README, About page or store listing consistent with the other Cocode apps, after an app is accepted on F-Droid, or to see which apps lack what.
---

# cocode-apps

One publishing standard for every Cocode Android app. `apps.yml` holds the facts, `standard/` the
rules, `templates/` the blocks to drop in, `tools/` the audit and render commands. Work from the
`cocode-apps` checkout (`~/0-projects/cocode-apps`); app checkouts are in `~/0-projects/<checkout>`.

## The five steps, per app

1. **Audit** — `python3 -m tools.audit <app>` (or `all`, which also rewrites `STATUS.md`).
2. **List the gaps** — each gap names the area; read that area's file in `standard/`.
3. **Fix** — in-app work (About page, privacy link, strings) goes through that app's own process: a
   lean spec where the app uses graph-loop, otherwise a normal PR. Site, README and store files
   (`fastlane/`) are direct PRs. Start the privacy page from `templates/privacy-skeleton.html` and the
   About strings from `templates/about-strings.md`.
4. **Render** — `python3 -m tools.render <app>` writes the marked blocks (navigation, install, footer)
   into the app's checkout; `python3 -m tools.render --catalogue` does the same for cocode.dk, so the
   catalogue carries the app's F-Droid or APK download link.
5. **Re-audit and follow every link** — run the audit again and check that every link answers HTTP 200.

When F-Droid accepts an app: `python3 -m tools.fdroid_status` refreshes `apps.yml`, then render again.

## Other skills

- `android-setup` — a new project's scaffold. Do not copy it here.
- `fdroid-release` — submitting an app to F-Droid. Do not copy it here.

## Rules

- Get the owner's OK before any push or merge in an app repository or cocode.dk. One branch and one
  PR per repository.
- Private apps appear in `apps.yml` as `id`, `name` and `private: true` only. Put nothing else
  about them in this public repository.
- Never name the blocklist provider in promotional text: install blocks, catalogue entries, store texts.
- `apps.yml` is the one source of app facts; never hard-code one in a tool or template.
- `audit` is read-only; `render` changes only text between its markers and reports files that have none.
- English and Danish for every app-facing text.

## Commands

```sh
bash scripts/gate.sh                     # pytest (+ ruff when installed)
python3 -m tools.audit all               # audit every app, rewrite STATUS.md
python3 -m tools.audit guard-android     # one app
python3 -m tools.render guard-android    # write the marked blocks into that app's checkout
python3 -m tools.render --catalogue      # write the download links into cocode.dk
python3 -m tools.fdroid_status           # refresh F-Droid states in apps.yml
python3 -m tools.art guard-android       # store icon, site icon and feature graphic from the launcher icon
```
