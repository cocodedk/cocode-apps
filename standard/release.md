# Release routine

## What must exist

- The version as literal lines in `gradle.properties` (not read from an environment variable).
- A stable `<Name>.apk` asset on every GitHub release, so
  `releases/latest/download/<apk_asset>` always works.
- Changelogs in both languages for every versionCode.
- F-Droid auto-update.
- When F-Droid accepts an app, `apps.yml` flips it to `live`. Then run `render` for the app (badges,
  install block, README, navigation, footer) and, separately, `render --catalogue` for cocode.dk. The
  in-app About page's update-button target changes through an app code change, not through `render`.

## Where

- `gradle.properties` (`VERSION_CODE=`, `VERSION_NAME=`) and the release workflow in
  `.github/workflows/` of the app repository.
- `fastlane/metadata/android/<locale>/changelogs/<versionCode>.txt`.
- `apk_asset` and `fdroid` in `apps.yml`; the daily `fdroid-status` workflow in this repository
  proposes the flip to `live`.
- Setting up a new project is `android-setup`; submitting to F-Droid is `fdroid-release`.

## How the audit checks it

- `check_fastlane` in `tools/checks/repo.py`: `gradle.properties` has a literal `VERSION_CODE` line,
  and both locales have a changelog for it.
- `check_release` in `tools/checks/web.py`: the stable asset downloads from the latest release.
- `check_fdroid` in `tools/checks/web.py`: the `fdroid` state in `apps.yml` matches f-droid.org.
- Checked by hand: `VERSION_NAME`, the F-Droid auto-update setting, and the flip-and-render step after
  acceptance.

## Example

guard-android keeps `VERSION_CODE=1001` in `gradle.properties` and ships both changelogs for it. Its
GitHub release (`v0.1.0`) publishes `GuardAndroid.apk`, so `releases/latest/download/GuardAndroid.apk`
downloads. The audit found other apps taking the version from an environment variable and three different
versionCode schemes across the apps.
