---
gate: python3 -m pytest tests/test_registry.py tests/test_blocks.py tests/test_render.py tests/test_checks_web.py tests/test_checks_repo.py -q
---

# 06 — close the gaps between the design and the built tools

## Goal

Specs 01–05 built the plan, but the design (`docs/superpowers/specs/2026-10-06-cocode-apps-design.md`)
asks for eight things the plan left out. This spec adds them to the shared blocks, render and the
audit, so every app gets them from `apps.yml` and the audit reports any app that lacks them:

1. links that work on sites served from a sub-path (the two `github.io` sites);
2. the app icon in the navigation;
3. `aria-current` on the current page's navigation link;
4. touch targets of at least 44 px, and links that wrap into a row on phones;
5. an audit check that the navigation has the six items in order;
6. an audit check for `robots.txt`;
7. an audit check for the share image;
8. an audit check that an old `privacy.html` redirects to `/privacy/`;

plus an audit check of the README's section order.

## Behaviour

Builds on the code on `main` after specs 01–05 (`tools/registry.py`, `tools/blocks.py`,
`tools/render.py`, `tools/checks/web.py`, `tools/checks/repo.py`). Keep every existing test passing
unchanged unless this spec says otherwise. Split a file at a natural seam rather than let it pass
200 lines.

The one exception: a fixture that stands for a *complete* site or README (for example the one in
`test_complete_site_has_no_gaps`) gains what this spec newly requires (the six `data-nav` items, the
icon, the stylesheet, `robots.txt`, the share image, the README sections), so it still has no gaps.
Its assertions stay as they are; only the fixture's pages and the fake `fetch`'s answers grow.

### Sites on a sub-path

- `App.base` (new property): the path of `site` with a trailing slash — `"/"` for
  `https://chess.cocode.dk`, `"/Claude-Email-App/"` for `https://cocodedk.github.io/Claude-Email-App`.
- `App.href(lang)` (new method): `base` joined with `home(lang)` without its leading slash —
  `"/"`, `"/en/"`, `"/Claude-Email-App/"`, `"/Claude-Email-App/da/"`.
- `home(lang)` keeps its meaning (the path inside the site), so `site + home(lang)` in the checks and
  `_pages` in render stay as they are.
- Every link and image path the blocks write uses `href(lang)` or `base` instead of `home(lang)` or a
  bare `/`: the navigation, the footer's privacy link, and the badge `src` (`{base}img/…`).

### The navigation block

- `nav_html(app, lang, current="home")`; `current` is `"home"` or `"privacy"`. Render passes
  `"home"` for each `index.html` and `"privacy"` for each `privacy/index.html`.
- The block starts with `<link rel="stylesheet" href="{base}css/cocode-nav.css">`, then the skip
  link as today.
- The brand link holds the icon before the name:
  `<img src="{base}img/icon.png" alt="" width="32" height="32">` (empty `alt`: the name follows).
  Every site serves its launcher icon at `<site_dir>/img/icon.png`; the audit checks it (below).
- The six links carry `data-nav` in this order: `home` (the brand link), `how`, `install`,
  `privacy`, `lang`, `more`.
- `aria-current="page"` is on the brand link when `current` is `"home"` and on the privacy link when
  it is `"privacy"`; never on more than one link.

### The shared stylesheet

- `templates/cocode-nav.css`, small and site-neutral: no colours or fonts of its own (links inherit;
  the focus outline uses `currentColor`). The skip link is off-screen until focused, then visible at
  the top left. `.cocode-nav` is a flex row that wraps: the brand on its own line on narrow screens,
  the other five links in a wrapping row under it; no hidden menu. Every link in `.cocode-nav` and
  `.cocode-footer` is at least 44 px high and 44 px wide (`min-height`/`min-width`, inline-flex,
  centred).
- `render.apply` with `write=True` copies it to `<site_dir>/css/cocode-nav.css` for every public app
  (live on F-Droid or not), creating `css/`. Not with `--dry-run`. With the badge copy, these are the
  only files written outside the markers; update the render rule in `CLAUDE.md` to say so.

### New audit checks

In the web checks (all through the injectable `fetch`; a status `0` answer is one "unreachable" gap,
never a crash):

- **Navigation order**: on the home page, the `data-nav` values between the nav markers must be
  exactly `home, how, install, privacy, lang, more` in that order. Otherwise one gap naming what was
  found.
- **Icon and stylesheet**: `site + "/img/icon.png"` and `site + "/css/cocode-nav.css"` answer 200;
  one gap per missing file.
- **robots.txt**: `site + "/robots.txt"` answers 200.
- **Share image**: the home page has `<meta property="og:image" content="…">` with an absolute
  `https://` URL that answers 200. One gap when the tag is missing, another when the image does not
  answer 200.
- **Old privacy path**: `site + "/privacy.html"`. `fetch` follows HTTP redirects and returns the
  final page, so the check reads that page. It passes when the answer is 404; or the 200 page carries
  a meta refresh whose URL ends in `privacy/` (`<meta http-equiv="refresh" content="0; url=…privacy/">`);
  or the 200 page is the standard privacy page, which a server redirect lands on: it holds the nav
  markers and its `data-nav="privacy"` link carries `aria-current="page"` (only privacy pages get
  that, and render writes no `privacy.html`). Otherwise the gap is "privacy.html does not redirect
  to /privacy/".

In the repository checks:

- **README section order**: after the install-marker check, the README's level-2 headings must
  include `Features`, `Privacy`, `Build`, `Contributing`, `License` (case-insensitive, other headings
  may sit between) in that order. One gap naming the first one missing or out of order.

### The standard

In `standard/*.md`, every "How the audit checks it" line for these items that says "checked by hand"
now names its check. Keep "checked by hand" for in-app order and TalkBack.

## Acceptance tests

- Registry: `base` and `href` for a root site and for `https://cocodedk.github.io/Claude-Email-App`
  with each `default_language`.
- Blocks: for the github.io app every `href`/`src` in nav, footer and install starts with
  `/Claude-Email-App/` or `https://`, except in-page fragments such as the skip link's `#main`; `nav_html(..., current="privacy")` has exactly one
  `aria-current="page"`, on the privacy link; the `data-nav` order; the icon `img` with empty `alt`;
  the stylesheet `link` first.
- Render: a write copies `css/cocode-nav.css` into the site dir for a not-live app; `--dry-run`
  copies nothing; a privacy page gets the nav with `aria-current` on the privacy link.
- Web checks, each with a fake `fetch`: a good site gives no new gaps; nav out of order; nav item
  missing; no icon; no stylesheet; no `robots.txt`; no `og:image`; `og:image` answering 404;
  `privacy.html` answering 200 without a refresh; `privacy.html` answering 404 (no gap); `privacy.html`
  answering 200 with the standard privacy page, as after a server redirect (no gap); an
  unreachable site still gives exactly one gap.
- Repo check: a README with all five sections in order (no gap), one missing, two swapped.
- `bash scripts/gate.sh` passes (pytest and ruff). Every code file is under 200 lines.

## Out of scope

Changing any app's site, README or icon to meet these checks (the audit lists them; the skill fixes
them per app, with the owner's OK); running the real audit; the in-app About page; the Support slot;
moving `privacy` in `apps.yml` from `privacy.html` to `/privacy/` (that follows each site's move).
