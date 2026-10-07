---
gate: python3 -m pytest tests/test_standard.py -q
---

# 05 — the standard, the templates and the skill (text)

## Goal

The rulebook a person or an agent reads before touching an app: one file per area in `standard/`,
two drop-in templates, and the `cocode-apps` skill that walks audit → fix → render → verify.

## Behaviour

Build **Task 9** and **Task 10 Step 1** of `docs/superpowers/plans/2026-10-06-cocode-apps.md`,
with these decisions settled:

- **Which spec section goes where** (the design is
  `docs/superpowers/specs/2026-10-06-cocode-apps-design.md`, section "The standard"):
  `about-page.md` ← "In the app"; `navigation.md` ← the Navigation bullet; `install-block.md` ← the
  Install block bullet; `privacy.md` ← the Privacy policy bullet; `website.md` ← the Footer bullet, the
  SEO basics, the "cocode.dk" section and the English-and-Danish baseline; `readme.md` ← "README";
  `store-listing.md` ← "F-Droid store listing"; `release.md` ← "Release routine"; `support.md` ← the
  placeholder sentence the plan gives.
- **"How the audit checks it"** names the check function from `tools/checks/web.py`,
  `tools/checks/repo.py` or `tools/catalogue.py` that covers the item (read the code on `main`); every
  item no function covers says "checked by hand".
- **"Example"** describes guard-android in words from what the design and
  `docs/audit-2026-10-06.md` say about it. Do not read or copy files from other repositories.
- **`templates/about-strings.md`**: the plan's keys, with exactly this wording:

  | key | English | Danish |
  |---|---|---|
  | about_check_updates | See the latest version | Se den nyeste version |
  | about_privacy_link | Read the privacy policy | Læs privatlivspolitikken |
  | about_website | Open the website | Åbn hjemmesiden |
  | about_source | See the source code on GitHub | Se kildekoden på GitHub |
  | about_report | Report a problem on GitHub | Meld en fejl på GitHub |
  | about_credits | Credits and licenses | Tak og licenser |
  | about_made_by | Made by Cocode (cocode.dk) | Lavet af Cocode (cocode.dk) |

  Below the table, one line: the section titles are the design's About-page sections in order.
- **`templates/privacy-skeleton.html`**: as the plan's Task 9 Step 3, with `<main id="main">` and no
  skip link of its own (the navigation block written between the nav markers carries it). The Danish
  headings in the comment block at the top, in order: Resumé, Hvad der indsamles, Servere appen
  kontakter, Tilladelser, Hvad der bliver på telefonen, Tredjeparter, Dine rettigheder, Kontakt,
  Ændringer.
- **`skill/SKILL.md`**: as the plan's Task 10 Step 1. Do not link it into any skills folder (the owner
  does that after merge).
- Spamhaus is never named in `standard/`, `templates/` or `skill/` (the rule in `CLAUDE.md` may be
  restated in the skill as "never name the blocklist provider in promotional text").

## Acceptance tests

`tests/test_standard.py`:
- `standard/` holds exactly the nine files the plan names, and each of the eight non-placeholder
  files has the four headings **What must exist**, **Where**, **How the audit checks it**, **Example**.
- `templates/about-strings.md` contains every key and both wordings from the table above.
- `templates/privacy-skeleton.html` has one `<h1>`, `<main id="main">`, the nav and footer marker
  pairs, and the nine English headings in order (`h2`).
- `skill/SKILL.md` front matter parses as YAML with `name: cocode-apps` and a non-empty description.
- No file under `standard/`, `templates/` (text files only) or `skill/` contains "spamhaus",
  case-insensitive.
- `bash scripts/gate.sh` passes (pytest and ruff).

## Out of scope

Linking the skill into `~/.claude-personal/skills` (owner, after merge); any change to an app
repository or cocode.dk; any tool code.
