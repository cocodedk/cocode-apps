# Privacy policy

## What must exist

- A privacy policy at `/privacy/` in both languages, with the same headings in every app: summary,
  what is collected, every server the app contacts and why, permissions, what stays on the phone,
  third parties, your rights, contact, changes.
- Old `privacy.html` paths redirect to `/privacy/`.
- The facts are right: the real package name and the real app name.

## Where

- `<app site>/privacy/` in the default language, `<app site>/<other>/privacy/` in the other one
  (`default_language` in `apps.yml`; the page is `<site_dir>/privacy/index.html` and the same under
  `<other>/`).
- The URL in `apps.yml` field `privacy` is the one the app, the README and the site link.
- Start from [templates/privacy-skeleton.html](../templates/privacy-skeleton.html).

## How the audit checks it

- `check_site` in `tools/checks/web.py`: `/privacy/` answers 200 in both languages.
- `check_inapp` in `tools/checks/repo.py`: the app links the privacy URL from `apps.yml`.
- Checked by hand: the nine headings and their order, that every contacted server is listed, the
  `privacy.html` redirect, and the package and app names.

## Example

guard-android serves its policy at `/privacy/` in Danish and at `/en/privacy/` in English, the only
app in the 2026-10-06 audit with the standard path. The audit found other apps with wrong facts
(a wrong package name on one, a wrong app name on another), which is why the facts are checked by hand.
