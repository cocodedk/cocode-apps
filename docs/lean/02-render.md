---
gate: python3 -m pytest tests/test_blocks.py tests/test_render.py tests/test_catalogue.py -q
---

# 02 — the shared blocks, render, and the cocode.dk catalogue links

## Goal

From `apps.yml` alone, produce the install block (HTML and Markdown), the navigation and the footer
for every app, and write them between `<!-- cocode-apps:<block>:start/end -->` markers in an app
checkout and in the cocode.dk catalogue. No existing text outside the markers ever changes; the one
other write is the badge copy below.

## Behaviour

Build **Tasks 3, 4 and 4b** of `docs/superpowers/plans/2026-10-06-cocode-apps.md` exactly as written
there: `tools/blocks_text.py`, `tools/blocks.py`, `tools/render.py` (with its `--catalogue` flag),
`tools/catalogue.py`, and the tests `tests/test_blocks.py`, `tests/test_render.py` and
`tests/test_catalogue.py` with the code given in the plan. Where this spec and the plan differ, this
spec wins.

- **The badges already exist.** `templates/badges/get-it-on-fdroid-en.png`, `-da.png` and
  `templates/badges/README.md` are on `main` (the official artwork, downloaded once). Skip Task 3
  Step 1; do not download, redraw or replace them.
- **The badge copy is the one exception, and it stays.** Keep the plan's behaviour and its test
  `test_apply_writes_readme_and_site_and_copies_badges` unchanged: when the app is live on F-Droid
  and `write` is true, `apply` also copies the two badge PNGs to
  `<site_dir>/img/get-it-on-fdroid-en.png` and `-da.png` in the checkout (creating `img/`, replacing
  only those two files), so the install block's badge is served by the app's own site. Nothing is
  copied with `--dry-run` or for an app not yet live. No other file outside the markers is written.
- **`Gap`.** Task 4b needs `Gap`: fill `tools/checks/__init__.py` now with the code from Task 5
  Step 3 of the plan (Task 5 then leaves it as it is).
- **Paths stay root-absolute** (`/`, `/img/…`, `/<lang>/privacy/`) exactly as the plan's code and
  tests have them. The two sites served from a `github.io` project path (claude-email-app, fits-qr)
  are a known limitation handled in a later spec; do not special-case them here.
- **The real files are never touched.** Tests use `tmp_path` and monkeypatch `CATALOGUE_FILE`. Do not
  run `python3 -m tools.render` against `~/0-projects`; do not edit any app checkout or the cocodedk
  repository (its markers are added later in a cocodedk PR, with the owner's OK).

## Acceptance tests

- Every test the plan gives for Tasks 3, 4 and 4b passes, including the plan's Review Focus 5 test
  `broken_markers_change_nothing` and `test_catalogue_flag_needs_no_app` (it reads the real
  `apps.yml` from spec 01).
- Add one test: `apply` with `write=False` on a live app, and `apply` on an app with `fdroid: none`,
  leave no `img/` folder in the checkout.
- No install block, catalogue line or label names Spamhaus (add one assertion over every public app
  in `apps.yml`: none of `install_html`, `install_md`, `nav_html`, `footer_html`, `catalogue_html`
  contains "spamhaus", case-insensitive).
- `bash scripts/gate.sh` passes (pytest and ruff). Every code file is under 200 lines.

## Out of scope

The app icon, `aria-current` and touch-target sizes in the navigation (a later spec); fixing the
github.io project-path sites; the cocodedk marker PR; checks and audit (spec 03); F-Droid status
(spec 04); the standard and skill (spec 05); any network access.
