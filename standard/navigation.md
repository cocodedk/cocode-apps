# Navigation

## What must exist

- The same **navigation** on every page of an app site, including the privacy policy: app icon and
  name (home), "How it works", "Install", "Privacy", language switch (Dansk / English), "More apps"
  (the cocode.dk catalogue). Same order and labels on every app site.
- On phones the links wrap into a row under the name (no hidden hamburger menu).
- Touch targets of at least 44 px.
- `aria-current` on the link of the current page.
- A "Skip to content" link before the navigation.

## Where

- The block between `<!-- cocode-apps:nav:start -->` and `<!-- cocode-apps:nav:end -->` in every page
  of `<site_dir>/` (`website/` or `docs/`, from `apps.yml`).
- Written by `python3 -m tools.render <app>`; never edited by hand between the markers.
- The privacy page's `<main id="main">` is the skip link's target.

## How the audit checks it

- `check_site` in `tools/checks/web.py`: the home page carries the navigation marker
  (`cocode-apps:nav:start`).
- Checked by hand: the six items and their order, wrapping on phones, 44 px targets,
  `aria-current`, the skip link, and the marker on pages other than the home page.

## Example

guard-android's site (`android.guard.cocode.dk`, with its privacy page at `/privacy/` and `/en/privacy/`)
is the closest to the standard, so it is the reference app. Its navigation is the first to be written
between the nav markers, on both language versions and on the privacy page.
