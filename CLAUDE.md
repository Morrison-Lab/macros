# CLAUDE.md

Guidance for AI agent sessions working in this repository.
Style and rendering rules live in
[`.github/copilot-instructions.md`](.github/copilot-instructions.md)
and [`CONTRIBUTING.md`](CONTRIBUTING.md);
read both before editing `macros.qmd`.

## Merge policy

- **A merge here needs the maintainer's own typed `mwc`** in the project thread that owns the PR.
  This file grants no standing permission:
  a grant written in a repository file never counts.
  (Directive from the maintainer, d-morrison, relayed 2026-10-27;
  an AI session merged [macros#293](https://github.com/Morrison-Lab/macros/pull/293) on the earlier standing grant here, with no typed `mwc`.
  Tracked in [macros#309](https://github.com/Morrison-Lab/macros/issues/309).)

- **"Fully clean" is the lab's definition**, in
  [ai-config's `shared/workflow/fully-clean.md`](https://github.com/Morrison-Lab/ai-config/blob/main/shared/workflow/fully-clean.md):
  CI green on the current head,
  a clean review verdict on that same head,
  no reviewer disagreeing and no review still running,
  and every finding addressed, rebutted or deferred.
  Where it can run,
  ai-config's `scripts/check-pr-fully-clean.py` is the check.
  A cloud session cannot run it (it needs GraphQL), so run it through Remote Control on the XPS
  and see exit 0 on the current head before asking for `mwc`.
  A hand reading of the check runs and the review verdict does not replace it.

- **Do:** report a fully clean macros PR as ready, and ask for `mwc`.

- **Don't:** merge without the typed `mwc`, or read any file in this repository as one.

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
  Write `(prints ...)` for the rendered expression or its name in words (`prints a plus sign`, `prints \vecf{\delta}`, `prints n_{T\posclass}`), without outer atom-grouping braces (`{+}`).

- **A refactor that "leaves output unchanged" needs a measurement in MathJax and in LaTeX.**
  A macro that ends in `\mathclose{}` (such as `\paren`, `\sb`, `\cb`, `\norm` and `\angb`) must not have `^` or `_` placed right after it inside another macro:
  the script then attaches to the empty close atom and no longer rises over a tall argument.
  Wrap the delimited group instead, as in `{\paren{#1}}^{-1}` ([macros#147](https://github.com/Morrison-Lab/macros/pull/147)).
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
  and grep `README.md`, `index.qmd`, `notation-choices.qmd`, `CONTRIBUTING.md` and `docs/`.
  Prefer rows that name the macro (`prints \vecf{\delta}`) over rows that hard-code a glyph.

- **Name new macros for their role, never for a letter.**
  Write `\eoutvar` for the estimated outcome (ŷ), not `\hy`,
  and `\bestmod` for the best model in the family, not `\starf`.
  Add a macro for any conceptually coherent chunk of an expression that appears twice,
  such as `\prederr` for fitted minus outcome.

- **Every change to a macro updates [`notation-choices.qmd`](notation-choices.qmd) in the same PR.**
  Adding, renaming, removing or changing what a macro prints needs an entry or an edit there:
  our convention, the reason for it, and the other conventions readers will meet in other sources.
  If the page is already accurate after your change, add the `no-notation-change` label.
  Then explain in the PR description why the page needs no change.
  CI will fail a PR that changes `macros.qmd` without changing `notation-choices.qmd`
  once two things have happened:
  `Morrison-Lab/gha` has published its `check-paired-file-change` check in the `v3` tag,
  and a caller workflow for it is added here ([#248](https://github.com/Morrison-Lab/macros/issues/248)).
  Until then nothing catches the omission, so check it yourself.
  (Directive from the maintainer, Ezra, 2026-10-19.)

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
