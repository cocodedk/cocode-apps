---
gate: python3 -m pytest tests/test_checks_web.py tests/test_checks_repo.py tests/test_audit.py -q
---

# 03 — the checks and the audit CLI

## Goal

One command scores any app, or all of them, against the standard and writes the gaps to
`STATUS.md`. It is read-only towards app repositories, and one broken site or missing checkout is one
gap, never a crash.

## Behaviour

Build **Tasks 5, 6 and 7** of `docs/superpowers/plans/2026-10-06-cocode-apps.md` exactly as written
there: `tools/net.py`, `tools/checks/web.py`, `tools/checks/repo.py`, `tools/audit.py` and the tests
`tests/test_checks_web.py`, `tests/test_checks_repo.py`, `tests/test_audit.py` with the code given in
the plan. `tools/checks/__init__.py` already holds `Gap` (spec 02); leave it as it is. Where this
spec and the plan differ, this spec wins.

- **No real audit in this run.** Skip Task 7 Step 5. Do not run `python3 -m tools.audit` at all (it
  reads the owner's checkouts under `~/0-projects` and the live network), and do not create or commit
  `STATUS.md`: the owner's first real audit writes it after merge. Task 7 Step 6 commits without it.
- **`fetch` never raises.** Besides the plan's `HTTPError`, `URLError`, `TimeoutError` and `OSError`,
  `fetch` also turns `http.client.HTTPException` (which covers `IncompleteRead` and `BadStatusLine`)
  and `ValueError` (a malformed URL) into `(0, "")`. Add `tests/test_net.py`: monkeypatch
  `urllib.request.urlopen` to raise each of `http.client.IncompleteRead(b"")`,
  `http.client.BadStatusLine("x")`, `urllib.error.URLError("x")` and `TimeoutError()` and assert
  `fetch("https://example.invalid/") == (0, "")`; and one fake response with status 200 and a body,
  asserting `(200, body)`.
- **An unreachable F-Droid is not "not listed".** In `check_fdroid`, status `0` (no answer) gives one
  gap `Gap(app.id, "fdroid", "f-droid.org unreachable")` whatever `apps.yml` says; the plan's two
  gaps apply only to real HTTP answers. Add a test for it.

## Acceptance tests

- Every test the plan gives for Tasks 5, 6 and 7 passes, including the Review Focus tests
  `unreachable_site_is_one_gap_not_a_crash`, `missing_checkout_is_one_gap`,
  `private_app_shows_name_only` and `non_literal_version_code_is_a_gap`.
- `tests/test_net.py` and the new `check_fdroid` test pass, and the suite stays offline
  (`tests/conftest.py` refuses any real socket).
- `bash scripts/gate.sh` passes (pytest and ruff). Every code file is under 200 lines.

## Out of scope

`STATUS.md` and the first real audit (the owner runs it); checking the six navigation items in order,
robots, the share image and the `privacy.html` redirect (a later spec); F-Droid status refresh
(spec 04); the standard and skill (spec 05); any change to an app repository or cocode.dk.
