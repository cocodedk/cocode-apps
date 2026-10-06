---
gate: python3 -m pytest tests/test_fdroid_status.py -q
---

# 04 — the daily F-Droid status refresh

## Goal

When f-droid.org starts listing an app, `apps.yml` flips it to `live` without anyone remembering to:
`tools/fdroid_status.py` asks f-droid.org about every app, and a daily GitHub Action opens one pull
request with the change for the owner to merge.

## Behaviour

Build **Task 8, Steps 1–6** of `docs/superpowers/plans/2026-10-06-cocode-apps.md` as written there:
`tools/fdroid_status.py`, `tests/test_fdroid_status.py` and `.github/workflows/fdroid-status.yml`
with the code given in the plan. Where this spec and the plan differ, this spec wins.

- **One open pull request, not one a day.** The workflow pushes to the fixed branch
  `fdroid-status/refresh` (`git switch -C`, then `git push --force -u origin fdroid-status/refresh`)
  and runs `gh pr create` only when `gh pr list --head fdroid-status/refresh --state open --json number
  --jq length` prints `0`. An open PR is updated by the force-push instead.
- **No PEP 668 failure.** Install PyYAML into a virtual environment, not the runner's system Python:
  `python3 -m venv .venv && .venv/bin/pip install --quiet "PyYAML>=6"`, then run
  `.venv/bin/python -m tools.fdroid_status`. Add `.venv/` to `.gitignore`.
- Keep `actions/checkout` pinned to the plan's SHA (`3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1`)
  and no other action.
- The tests never reach the network: every lookup goes through the injectable `fetch`, and the tests
  pass a fake.

## Acceptance tests

- Every test the plan gives for Task 8 passes.
- Add a test that the fake `fetch` is never called for a private app or an app already `live`.
- Add a test of `main()` with `ROOT` and `real_fetch` monkeypatched (a copy of an `apps.yml` in
  `tmp_path`, a fake answering 404 for every app): the file stays byte-for-byte unchanged.
- `.github/workflows/fdroid-status.yml` parses as YAML (`yaml.safe_load`) in a test, and names the
  branch `fdroid-status/refresh`.
- `bash scripts/gate.sh` passes (pytest and ruff). Every code file is under 200 lines.

## Out of scope

The repository setting that lets Actions open pull requests and the first manual workflow run (the
owner does those after merge); render after a flip (the owner runs it); anything else.
