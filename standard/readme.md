# README

## What must exist

The same top in every repo: a one-line description, the install block (Markdown), screenshots, and a
privacy summary with a link. Then the same section order: Features, Privacy, Build, Contributing,
License.

## Where

- `README.md` at the repository root.
- The install block sits between `<!-- cocode-apps:install:start -->` and
  `<!-- cocode-apps:install:end -->`; see [install-block.md](install-block.md).
- The privacy link is the `privacy` URL in `apps.yml`.

## How the audit checks it

- `check_readme` in `tools/checks/repo.py`: the README exists and carries the install marker
  (`cocode-apps:install:start`).
- `check_readme` also checks the level-2 headings: `Features`, `Privacy`, `Build`, `Contributing`,
  `License`, in that order.
- Checked by hand: the one-line description, the screenshots, and the privacy summary and link.

## Example

guard-android, the reference app, gets this top first: its own one-line description, then the Markdown
install block written by `render` between the markers, then its screenshots and privacy summary. The
install block is the one part `render` writes; the rest is the app's own text.
