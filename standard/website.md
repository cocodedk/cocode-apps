# Website, footer and cocode.dk

## What must exist

- A **footer**, identical on every page: a source link, a privacy link, the license (as text) and one
  "Made by Cocode (cocode.dk)" link.
- The SEO basics: sitemap, robots, hreflang, a share image.
- English and Danish everywhere as the baseline; an app may add more. The default language is served
  at `/`, the other at `/<lang>/`.
- On **cocode.dk**: every app's catalogue entry links to F-Droid when live, to its GitHub release
  until then, written from `apps.yml` by `render --catalogue`.

## Where

- Footer: the block between `<!-- cocode-apps:footer:start -->` and `<!-- cocode-apps:footer:end -->`
  on every page of the site. `render` writes it into the English and Danish home pages and privacy
  pages of `<site_dir>/`; any other page needs it added and updated separately.
- `sitemap.xml` and `robots.txt` at the site root; `hreflang` links in each page's `<head>`; the share
  image referenced from `og:image`.
- cocode.dk: in the cocode.dk checkout (`~/0-projects/cocodedk`), each public app's `get-<id>` block
  belongs in either `templates/partials/catalogue.html` (the catalogue) or `templates/partials/works.html`
  (the featured apps), one block per public app.
- Site folder, URL and languages come from `apps.yml` (`site`, `site_dir`, `default_language`).

## How the audit checks it

- `check_site` in `tools/checks/web.py`: the footer marker (`cocode-apps:footer:start`), `hreflang`
  on the home page, and `sitemap.xml` answering 200.
- `check_catalogue` in `tools/catalogue.py`: the catalogue has a `get-<id>` block for the app.
- `check_site` also checks that `robots.txt` answers 200, that the home page has an `og:image` share
  image with an absolute `https://` URL that answers 200, and what `privacy.html` returns (a 404, a meta
  refresh to `privacy/` or the standard privacy page pass); whether it really redirects is checked by hand.
- Checked by hand: the footer's source, privacy and Cocode links and its displayed license, both
  languages on every page, and the catalogue link's target.

## Example

guard-android's site (`android.guard.cocode.dk`) is the reference app's site, serving both languages
(its English privacy page is at `/en/privacy/`). Its catalogue entry on cocode.dk shows "Hent installationsfilen"
until the app is live on F-Droid, then "Hent på F-Droid". The 2026-10-06 audit found nine sites
without sitemap and robots, four without a share image and three without hreflang across the apps.
