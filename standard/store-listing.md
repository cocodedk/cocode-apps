# F-Droid store listing

## What must exist

- Locales `en-US` and `da-DK`, each with a title, a short description and a full description.
- A changelog per versionCode in both languages.
- An icon (512 px), a feature graphic, and at least two phone screenshots.

## Where

`fastlane/metadata/android/` in the app repository:

- `<locale>/title.txt`, `short_description.txt`, `full_description.txt`
- `<locale>/changelogs/<versionCode>.txt`
- `en-US/images/icon.png`, `en-US/images/featureGraphic.png`
- `en-US/images/phoneScreenshots/*.png` (or `.jpg`)

The versionCode is the literal `VERSION_CODE=` line in `gradle.properties`.

## How the audit checks it

- `check_fastlane` in `tools/checks/repo.py`: the three text files in both locales, the changelog for
  the current `VERSION_CODE` in both locales, `icon.png` and `featureGraphic.png` under `en-US`, and
  at least two phone screenshots.
- Checked by hand: the icon's 512 px size, the text quality, the changelogs for older versionCodes,
  and images for `da-DK`.

## Example

guard-android has both `da-DK` and `en-US` listings and a changelog for versionCode 1001, so it is
the only app in the 2026-10-06 audit with a listing in both languages. The audit found no icon or
feature graphic in any app's metadata, and screenshots only in chess-puzzles.
