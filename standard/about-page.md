# About page and app languages

## What must exist

- An **About page**, reachable from the main screen, with these sections in this order, each title a
  TalkBack heading:
  1. Name and version, plus a "Check for updates" button. It opens the F-Droid page, or the GitHub
     release until the app is live on F-Droid. The app never checks for updates over the network.
  2. What the app does (one paragraph).
  3. The privacy promises in short, plus a "Read the privacy policy" button.
  4. Links: website, source code, report a problem.
  5. Credits and licenses.
  6. Made by Cocode.
  7. Support slot (empty until the Support phase; see [support.md](support.md)).
- English and Danish for all app text. An app may add more languages.

## Where

- Source file with `About` in its name under `app/src/main/` (a screen, activity or composable).
- Strings in `app/src/main/res/values/strings.xml` and `values-da/strings.xml`; the wording for the
  buttons is in [templates/about-strings.md](../templates/about-strings.md).
- The targets come from `apps.yml`: `privacy`, `site`, `repo` (`https://github.com/cocodedk/<repo>`),
  and the F-Droid page `https://f-droid.org/packages/<applicationId>/`.

## How the audit checks it

- `check_inapp` in `tools/checks/repo.py`: an About screen exists (a source file named `*About*`),
  the app's source or resources contain the privacy URL from `apps.yml`, and the second language
  folder (`res/values-da`, or `res/values-en` when Danish is the default) exists.
- Checked by hand: that the About page is reachable from the main screen, section order, TalkBack
  headings, the paragraph's content, the update button's target, that no network update check exists,
  and that all app text is complete in English and Danish (the audit only sees that the second
  language folder exists).

## Example

guard-android is the closest to the standard: it already has an About screen and a listing in both
Danish and English. It is the reference for the layout, the section order and the strings. Like every
app in the 2026-10-06 audit it still lacked the privacy link and the update button, so those are the
two things its About page gains.
