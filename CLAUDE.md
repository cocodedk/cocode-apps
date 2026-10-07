# CLAUDE.md — cocode-apps

The central publishing standard for every Cocode Android app: one registry (`apps.yml`), one
rulebook (`standard/`), drop-in `templates/`, and `tools/` that audit apps and write the shared
blocks into their sites, READMEs and the cocode.dk catalogue. Public repository.

**The design is the authority:** `docs/superpowers/specs/2026-10-06-cocode-apps-design.md`.
**The plan to build it:** `docs/superpowers/plans/2026-10-06-cocode-apps.md`.
**The starting facts:** `docs/audit-2026-10-06.md` (16 apps, what each has and lacks).

## Rules

- `apps.yml` is the single source of truth for app facts. Never hard-code an app fact in a tool,
  template or standard file.
- **Private apps** appear in `apps.yml` with `id`, `name` and `private: true` only. Nothing else
  about them goes into this public repo.
- Tools are Python 3. The audit and render tools need only PyYAML; artwork generation (`tools.art`) also
  needs Pillow and Chrome or Chromium. Tests use pytest and are **offline**: every HTTP request goes
  through an injectable `fetch(url) -> (status, text)` and tests pass a fake; `audit --fresh` also
  contacts GitHub through `git clone`, which tests replace.
- `audit.py` never changes an app repository; `audit all` rewrites this repository's `STATUS.md`.
- `render.py` changes only text between `<!-- cocode-apps:<block>:start -->` and
  `<!-- cocode-apps:<block>:end -->` markers. If a file has no markers it reports that and changes
  nothing. The only files it writes outside the markers are the F-Droid badge images and
  `css/cocode-nav.css` in `<site_dir>`, never with `--dry-run`.
- Nothing is pushed to, or merged in, an app repository or cocode.dk without the owner's OK. One
  branch and PR per repository.
- Spamhaus's terms forbid its name in promotional material: never name it in install blocks,
  catalogue entries or store texts.
- English and Danish are the baseline for every app-facing text.
- Code files under 200 lines. Conventional Commits. Never `--no-verify`.

## Commands

```sh
bash scripts/gate.sh                     # the gate: pytest (+ ruff when installed)
python3 -m tools.audit all --fresh       # audit every app (shallow clones of GitHub), rewrite STATUS.md
python3 -m tools.audit guard-android     # one app
python3 -m tools.render guard-android    # write the marked blocks into that app's checkout
python3 -m tools.fdroid_status           # refresh F-Droid states in apps.yml
python3 -m tools.art guard-android       # store icon, site icon and feature graphic from the launcher icon
```

graph-loop builds the specs in `docs/lean/` one per run; its profile is [profile-python.md](profile-python.md).

App checkouts live in `~/0-projects/<checkout>` (the `checkout` field in `apps.yml`).
