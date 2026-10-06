---
gate: python3 -m pytest tests/test_registry.py -q
---

# 01 — the registry: `apps.yml` and `tools/registry.py`

## Goal

One file, `apps.yml`, holds every fact about the 16 Cocode Android apps, and `tools/registry.py`
loads and validates it into `App` objects. Every later tool reads app facts only through this
module (CLAUDE.md: "`apps.yml` is the single source of truth").

## Behaviour

Build **Task 2** of `docs/superpowers/plans/2026-10-06-cocode-apps.md` exactly as written there:
the `App` dataclass and its interface, `RegistryError`, `parse`, `load`, `find`, `ROOT`, the tests
in `tests/test_registry.py` and the implementation given in the plan. Where this spec and the plan
differ, this spec wins.

### The facts in `apps.yml`

Follow the plan's Step 4 rules and the audit in `docs/audit-2026-10-06.md`. These facts are settled
here, so nothing is guessed:

| id | name (en = da) | repo | checkout | applicationId | site | license | fdroid | apk_asset |
|---|---|---|---|---|---|---|---|---|
| guard-android | Guard for Android | guard-android | guard-android | dk.cocode.guard | https://android.guard.cocode.dk | GPL-3.0-or-later | none | GuardAndroid.apk |
| babakcast | BabakCast | BabakCast | BabakCast | com.cocode.babakcast | https://cast.cocode.dk | Apache-2.0 | mr:49562 | BabakCast.apk |
| babakplayer | BabakPlayer | BabakPlayer | BabakPlayer | com.cocode.babakplayer | https://player.cocode.dk | Apache-2.0 | mr:49561 | BabakPlayer.apk |
| battleship | Battleship | Battleship | Battleship | com.cocode.battleship | https://battleship.cocode.dk | Apache-2.0 | live | Battleship.apk |
| claude-email-app | Claude Email App | Claude-Email-App | Claude-Email-App | com.cocode.claudeemailapp | https://cocodedk.github.io/Claude-Email-App | Apache-2.0 | none | Claude-Email-App.apk |
| linkqrwallet | Link QR Wallet | LinkQRWallet | LinkQRWallet | com.cocode.linkqrwallet | https://qr.cocode.dk | MIT | mr:49558 | LinkQRWallet.apk |
| metrologist | Metrologist | Metrologist | measure-app | com.cocode.measureapp | https://measure.cocode.dk | Apache-2.0 | none | Metrologist.apk |
| chess-puzzles | Chess Puzzles | chess-puzzles | chess-puzzles | dk.cocode.chess | https://chess.cocode.dk | Apache-2.0 | live | ChessPuzzles.apk |
| fits-qr | FITS | fits-qr | fits-qr | dk.fits.contact | https://cocodedk.github.io/fits-qr | Apache-2.0 | none | FITS-QR.apk |
| lifemeter | LifeMeter | lifemeter | lifemeter | dk.cocode.lifemeter | https://lifemeter.cocode.dk | Apache-2.0 | live | LifeMeter.apk |
| markdown | Markdown | markdown | markdown-viewer | dk.cocode.markdown | https://markdown.cocode.dk | Apache-2.0 | none | Markdown.apk |
| parvaz | Parvaz | parvaz | parvaz | dk.cocode.parvaz | https://parvaz.cocode.dk | MIT | mr:49559 | Parvaz.apk |
| persian-calendar | Persian Calendar | persian-calendar | Calendar | com.cocode.calendar | https://calendar.cocode.dk | MIT | mr:49564 | persian-calendar.apk |
| tms-measurement-app | TMS Measurement | tms-measurement-app | TMSMeasurement | com.cocode.tmsmeasurement | https://tms.cocode.dk | MIT | mr:49545 | TMSMeasurement.apk |
| weather-android | Weather | weather-android | weather-android | dk.cocode.weather | https://weather.cocode.dk | Apache-2.0 | mr:49432 | Weather.apk |
| exercise-log | Exercise Log | (private) | | | | | | |

- `privacy`: `<site>/privacy.html` for babakcast, babakplayer, battleship, metrologist,
  chess-puzzles, lifemeter, persian-calendar and tms-measurement-app; `<site>/privacy/` for
  guard-android; omitted for the other six public apps.
- `site_dir`: `docs` for linkqrwallet, persian-calendar and tms-measurement-app; `website` otherwise.
- `default_language`: `da` for guard-android; `en` otherwise.
- `languages`: guard-android `[en, da]`, babakplayer `[en, fa]`, tms-measurement-app
  `[en, ar, fa, zh]`, `[en]` for the others.
- `obtainium` is left out (the default, `true`).
- exercise-log is private: exactly `id: exercise-log`, `name: {en: Exercise Log, da: Exercise Log}`,
  `private: true`, nothing else. No other fact about it appears anywhere in the repository.
- Order the entries as in the table. No comments in `apps.yml` (spec 04 rewrites it with
  `yaml.safe_dump`).

## Acceptance tests

- Every test in the plan's Task 2 Step 1 passes, including `test_shipped_registry_loads`
  (16 apps, one private).
- Add `test_shipped_registry_facts`: `find(load(), "persian-calendar")` has checkout `Calendar` and
  `site_dir` `docs`; `find(load(), "battleship").fdroid_live` is true; `find(load(), "babakcast").fdroid`
  is `"mr:49562"`; `find(load(), "guard-android").home("da") == "/"`; every public app's `apk_url`
  ends with `/releases/latest/download/` followed by its `apk_asset`.
- `bash scripts/gate.sh` passes (pytest and ruff).
- `tools/registry.py` is under 200 lines.

## Out of scope

Blocks, render, checks, audit and F-Droid status (specs 02–04); the standard and the skill (spec 05);
any change to an app repository or to cocode.dk; any network access.
