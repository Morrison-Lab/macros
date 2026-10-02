# CLAUDE.md

Guidance for AI agent sessions working in this repository.
Style and rendering rules live in
[`.github/copilot-instructions.md`](.github/copilot-instructions.md)
and [`CONTRIBUTING.md`](CONTRIBUTING.md);
read both before editing `macros.qmd`.

## Standing merge policy (`mwc`)

- **Standing `mwc` is active by default in `Morrison-Lab/macros`**:
  AI agent sessions may squash-merge a pull request here
  once it is fully clean,
  without asking first,
  unless told otherwise for a specific PR or session.
  (Directive from the maintainer, d-morrison, 2026-10-02.)

- **"Fully clean" is the lab's definition**, in
  [ai-config's `shared/workflow/fully-clean.md`](https://github.com/Morrison-Lab/ai-config/blob/main/shared/workflow/fully-clean.md):
  CI green on the current head,
  a clean review verdict on that same head,
  no reviewer disagreeing and no review still running,
  and every finding addressed, rebutted or deferred.
  Where it can run,
  ai-config's `scripts/check-pr-fully-clean.py` is the check.

- **Why:** this repository is shared notation for several lab sites,
  so a new macro often blocks work downstream until it merges.

- **The grant removes the asking, not the bar.**
  A PR that is not fully clean still waits,
  and a reviewer's skip notice is not a clean verdict.

- **Do:** merge a fully clean macros PR,
  and say in the same reply that you merged it and why it qualified.

- **Don't:** read this as covering a PR in another repository,
  such as the downstream bump of a `latex-macros` submodule.

<!-- ai-config:begin (managed by Morrison-Lab/ai-config scripts/wire-repo-config.py) -->
## Cross-project agent rules (ai-config)

This repository follows the maintainer's cross-project agent rules in
[Morrison-Lab/ai-config](https://github.com/Morrison-Lab/ai-config).
If your harness has not already loaded them (Claude Code loads them through
the ai-config plugin), read
[AGENTS.md](https://github.com/Morrison-Lab/ai-config/blob/main/AGENTS.md)
before starting work, and follow it alongside this file.
This file's own instructions add to those rules, and win only where they are
more specific.
<!-- ai-config:end -->
