# cocode-apps — one publishing standard for every Cocode Android app

Date: 2026-10-06. Owner: Babak Bandpey (bb@cocode.dk). Status: design, for review.

## Why

The owner publishes 16 Android apps (15 public, 1 private) and wants them to read and look like they
come from **one careful publisher**. An audit on 2026-10-06 found almost no cohesion:

- No site or README links to F-Droid, not even the three apps already published there (Battleship,
  chess-puzzles, lifemeter). 8 apps have open fdroiddata merge requests, 5 are not submitted.
- 6 apps have no live privacy page; the rest mix `/privacy/` and `privacy.html`; two pages state
  wrong facts (a wrong package name, a wrong app name).
- 5 apps have an About screen, each laid out differently; none links to its privacy policy.
- Only chess-puzzles has store screenshots; no app has an icon or feature graphic in its F-Droid
  metadata; listings are English only (guard-android also has Danish).
- Download links, APK asset names, site folders (`website/` vs `docs/`), version schemes and license
  detection all differ.

## Goal and success

- Every app has the same structure in the same places: About page, privacy policy, install block,
  navigation, README top, store listing, release routine. Each app keeps its own content, colors and
  screens.
- One fact file (`apps.yml`) is the single source of truth; every site, README, About page target and
  the cocode.dk catalogue says the same thing because they are written from it.
- One command audits any app against the standard and lists its gaps; a skill fixes them.
- When F-Droid publishes an app, one change flips every link to F-Droid — and a daily job makes that
  change itself.

## Decisions (settled with the owner)

| Topic | Decision |
|---|---|
| What "cohesive" means | One recognizable publisher: same structure and routine, each app its own content and look |
| Where it lives | A central project `cocode-apps` (`~/0-projects/cocode-apps`, GitHub `cocodedk/cocode-apps`), public |
| Approach | One standard, one skill, one fact file (option 1 of 3); extends `android-setup` and `fdroid-release`, doesn't replace them |
| Updates | The app never checks for updates over the network; F-Droid (or Obtainium for the GitHub APK) updates it. The About page shows the version and a "Check for updates" button that opens the F-Droid page (the GitHub release until the app is on F-Droid) |
| Languages | English and Danish everywhere as the baseline; an app may add more |
| Private apps | Listed only as name + "private"; no details in this public repo |
| Support (money, time, tokens) | A later phase; the standard reserves a Support slot on the About page and the site now, empty |

## The project

```
cocode-apps/
  apps.yml              the registry: one entry per app (single source of truth)
  standard/             the rulebook, one file per area:
    about-page.md  privacy.md  install-block.md  navigation.md  readme.md
    store-listing.md  release.md  website.md  support.md (placeholder)
  templates/            exact blocks to drop in: About strings (en + da), privacy page skeleton,
                        install block (HTML and Markdown), navigation header/footer, F-Droid badge
  tools/
    audit.py            scores one app or all against the standard -> gaps; writes STATUS.md
    render.py           writes the marked blocks into sites, READMEs and cocode.dk from apps.yml
    fdroid_status.py    asks f-droid.org which apps are live; updates apps.yml
  skill/                the cocode-apps skill: audit -> fix -> render -> verify
  .github/workflows/    daily fdroid_status run that opens a PR when an app goes live
  STATUS.md             generated table: every app, its score and its gaps
```

### `apps.yml` (per app)

`id` (short slug), `name` (en, da), `repo`, `checkout` (local folder under `~/0-projects/`),
`applicationId`, `site` (URL), `site_dir` (`website` or `docs`), `default_language` (`en` or `da`,
the language served at `/`; the other one at `/<lang>/`), `privacy` (URL),
`license` (SPDX), `languages`, `fdroid` (`live` | `mr: <number>` | `none`), `apk_asset` (file name of
the stable release asset), `obtainium` (bool), `private` (bool; when true only `id`, `name` and
`private` are kept). The tools are Python 3 with one dependency, PyYAML, to read it.

## The standard (what every app must have)

### In the app
- **About page**, reachable from the main screen, sections in this order, each title a TalkBack
  heading: name and version + "Check for updates" (opens the F-Droid page, or the GitHub release
  until live); what the app does (one paragraph); the privacy promises in short + "Read the privacy
  policy"; links: website, source code, report a problem; credits and licenses; made by Cocode;
  Support slot (empty until the Support phase).
- English and Danish for all app text.

### Website (`<app>.cocode.dk`)
- **Navigation**, identical on every page incl. the privacy policy: app icon + name (home), "How it
  works", "Install", "Privacy", language switch (Dansk / English), "More apps" (cocode.dk catalogue).
  Same order and labels on every app site. On phones the links wrap into a row under the name (no
  hidden hamburger menu); touch targets ≥ 44 px; `aria-current` on the current page; a "Skip to
  content" link before the navigation.
- **Install block**, identical everywhere: (1) the official "Get it on F-Droid" badge linking
  `https://f-droid.org/packages/<applicationId>/`; (2) "Download the APK from GitHub" linking
  `https://github.com/cocodedk/<repo>/releases/latest/download/<apk_asset>`; (3) Obtainium for
  auto-updating the GitHub APK. Before the app is live on F-Droid the badge spot says "Coming to
  F-Droid" (never a dead link).
- **Privacy policy at `/privacy/`** in both languages, with the same headings in every app: summary,
  what is collected, every server the app contacts and why, permissions, what stays on the phone,
  third parties, your rights, contact, changes. Old `privacy.html` paths redirect to it.
- **Footer**, identical: source, privacy, license, made by Cocode, cocode.dk; plus the SEO basics:
  sitemap, robots, hreflang, a share image.

### README
The same top in every repo: one-line description, the install block (Markdown), screenshots, privacy
summary with a link; then the same section order (Features, Privacy, Build, Contributing, License).

### F-Droid store listing (`fastlane/metadata/android/`)
`en-US` and `da-DK`: title, short and full description, a changelog per versionCode in both; an icon
(512 px), a feature graphic, at least two phone screenshots.

### Release routine
Version as literal lines in `gradle.properties`; a stable `<Name>.apk` asset on every GitHub release;
changelogs in both languages; F-Droid auto-update. When F-Droid accepts an app, `apps.yml` flips it
to `live` and `render.py` updates every badge, the README, the About page target and cocode.dk.

### cocode.dk
Every app's catalogue entry links to F-Droid when live, to its GitHub release until then, written
from `apps.yml` by `render.py`.

## Tools

- **`audit.py <app|all>`** checks, per app: the live site (navigation with the six items in order,
  the install block marker, `/privacy/` 200 in both languages, hreflang, sitemap); the README
  (install block marker); `fastlane/` (locales, changelog for the current versionCode, icon, feature
  graphic, ≥ 2 screenshots); the latest GitHub release (the stable asset exists and downloads);
  in-app (an About screen and a privacy link: string and URL presence in both languages); F-Droid
  status from f-droid.org. Output: a score and gap list per app, written to `STATUS.md`. Read-only:
  it never changes an app repo.
- **`render.py`** replaces only the text between `<!-- cocode-apps:install:start -->` and
  `<!-- cocode-apps:install:end -->` (and the same for navigation and footer) in each site, README and
  the cocode.dk catalogue, from `apps.yml`. It prepares one branch and PR per repo; nothing is pushed
  or merged without the owner's OK.
- **`fdroid_status.py`** queries `https://f-droid.org/api/v1/packages/<applicationId>` for every
  app; a daily GitHub Action in cocode-apps runs it and, when an app turns live, opens a PR that
  updates `apps.yml` (the owner merges; render follows).

## The skill (`cocode-apps`)

Per app: 1) audit; 2) list the gaps; 3) fix — in-app work through that app's own process (a lean
spec where the app uses graph-loop, otherwise a normal PR), site, README and store files as direct
PRs; 4) render; 5) re-audit and follow every link (HTTP 200). It points to `android-setup` for a new
project's scaffold and to `fdroid-release` for submitting to F-Droid, instead of copying them.

## Rollout

1. Build cocode-apps: `apps.yml` for all 16 apps, the standard, the templates, `audit.py`, first
   `STATUS.md`.
2. guard-android as the reference app (closest to the standard already).
3. The three apps live on F-Droid (Battleship, chess-puzzles, lifemeter): working badges and links
   today, and the cocode.dk catalogue.
4. The eight apps with open F-Droid MRs.
5. The five not yet submitted.
6. The Support phase (money, time, tokens).

## Out of scope (for now)

A shared Android library or common UI code; restyling apps' own looks; Google Play; IzzyOnDroid
(noted as a possible later channel); the Support phase content.
