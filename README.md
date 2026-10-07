# cocode-apps

One publishing standard for every Cocode Android app: a registry of app facts (`apps.yml`), a
rulebook (`standard/`), drop-in `templates/`, and `tools/` that audit each app against the standard
and write the shared install, navigation and footer blocks into its site, README and the cocode.dk
catalogue. The design is in
[docs/superpowers/specs/2026-10-06-cocode-apps-design.md](docs/superpowers/specs/2026-10-06-cocode-apps-design.md).

```sh
bash scripts/gate.sh                     # the gate: pytest (+ ruff when installed)
python3 -m tools.audit all --fresh       # audit every app (shallow clones of GitHub), rewrite STATUS.md
python3 -m tools.audit guard-android     # one app
python3 -m tools.render guard-android    # write the marked blocks into that app's checkout
python3 -m tools.fdroid_status           # refresh F-Droid states in apps.yml
```

Private apps are listed by name only.
