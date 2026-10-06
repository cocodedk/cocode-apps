# Profile: cocode-apps, a Python 3 project tested offline with pytest

The lean loop reads the first indented line under `## suite_command`, `## build_command`,
`## artifact` and `## account`.

## suite_command

    bash scripts/gate.sh

The one offline gate: pytest (system `python3` with PyYAML and pytest), then ruff when it is on
`PATH`. `tests/conftest.py` refuses any non-loopback socket, so every network call goes through an
injectable `fetch(url) -> (status, text)` and the tests pass fakes.

## build_command

    python3 -m compileall -q tools tests

There is no build step beyond byte-compiling the tools.

## artifact

    README.md

A set of command-line tools ships no single file; the README names the commands.

## account

    personal

A personal project: the loop spends the personal Claude account and never the work one.

## paths_the_gate_needs

    ~/.local/bin and ~/.local/share/uv/tools/ruff   ruff, read-only (without them the gate skips ruff)
