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

## Working on macros

- **Review nits are required here, not optional.**
  Style drift in a shared macro spreads to every notes repository.
  Use `\paren{}` rather than raw parentheses inside a macro,
  and build on existing macros (`\vecf`, `\MSEt`, `\RMSEt`) instead of re-expanding them.
  Re-run the review (a comment that begins with `/review`) after fixing, before asking for `mwc`.

- **Check for an existing key before adding a row to `interpretations.tsv`.**
  `macros-table.qmd` joins macros to that file by name, so a duplicate key renders two rows.
  Grep for the key first, including its leading backslash,
  and afterwards run `cut -f1 interpretations.tsv | sort | uniq -d` to confirm there are no duplicates.

- **A refactor that "leaves output unchanged" needs a measurement in MathJax and in LaTeX.**
  A macro that ends in `\mathclose{}` (such as `\paren`, `\sb`, `\cb`, `\norm` and `\angb`) must not have `^` or `_` placed right after it inside another macro:
  the script then attaches to the empty close atom and no longer rises over a tall argument.
  Wrap the delimited group instead, as in `{\paren{#1}}^{-1}` (macros#147).
  Compare old and new with a tall argument (`\frac{a}{b}`) in `mathjax-full` and in pdflatex (compare `\ht`, `\dp` and `\wd` of a box),
  and include the rejected form as a control to prove the test can fail.

- **Test a new macro with a subscript and an exponent in a compiled PDF.**
  `python3 tools/check_latex.py` does not exercise new macros,
  so also render a test `.qmd` that includes `macros.qmd` through `include-in-header`
  and covers `\condE{...}{...}^2`.
  Brace a macro body that ends in a delimiter macro (`{\E{...}}`).
  Do not defer the PDF check to CI.

- **After changing how a macro prints, scan for the old description in glyphs and in words.**
  Search `interpretations.tsv` for the glyph (decompose with NFD first, so precomposed letters match) and for words such as "tilde", "over", "above" and "hat",
  and grep `README.md`, `index.qmd`, `CONTRIBUTING.md` and `docs/`.
  Prefer rows that name the macro (`prints \vecf{\delta}`) over rows that hard-code a glyph.

- **Name new macros for their role, never for a letter.**
  Write `\eoutvar` for the estimated outcome (ŷ), not `\hy`,
  and `\bestmod` for the best model in the family, not `\starf`.
  Add a macro for any conceptually coherent chunk of an expression that appears twice,
  such as `\prederr` for fitted minus outcome.

- **Notes repositories never define a macro locally, even as a stopgap.**
  Order the work as: macros PR merges, the notes repository bumps its `latex-macros` pin, then the notes use the macro.

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
