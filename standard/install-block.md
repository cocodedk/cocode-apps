# Install block

## What must exist

The same **install block** on every site and in every README, with three parts:

1. The official "Get it on F-Droid" badge linking `https://f-droid.org/packages/<applicationId>/`.
2. "Download the APK from GitHub", linking
   `https://github.com/cocodedk/<repo>/releases/latest/download/<apk_asset>`.
3. Obtainium, for auto-updating the GitHub APK.

Before the app is live on F-Droid the badge spot says "Coming to F-Droid", never a dead link.

## Where

- Sites: the block between `<!-- cocode-apps:install:start -->` and `<!-- cocode-apps:install:end -->`
  in the home page (HTML), in both languages.
- READMEs: the same markers around the Markdown version, at the top.
- Badges: `templates/badges/get-it-on-fdroid-en.png` and `get-it-on-fdroid-da.png`.
- `applicationId`, `repo`, `apk_asset`, `fdroid` and `obtainium` all come from `apps.yml`.
- Written by `python3 -m tools.render <app>`; the F-Droid state flips when `apps.yml` says `live`.

## How the audit checks it

- `check_site` in `tools/checks/web.py`: the home page carries the install marker
  (`cocode-apps:install:start`).
- `check_readme` in `tools/checks/repo.py`: the README carries the same marker.
- `check_release` in `tools/checks/web.py`: the `<apk_asset>` link downloads.
- `check_fdroid` in `tools/checks/web.py`: the `fdroid` state in `apps.yml` matches what f-droid.org
  lists.
- Checked by hand: the block's wording, the badge image, and the Obtainium link.

## Example

guard-android has no release yet, so its `GuardAndroid.apk` link does not download and its badge spot
says "Coming to F-Droid" until the app is accepted. Once `apps.yml` says `live`, `render` swaps the
badge in; nothing else is edited.
