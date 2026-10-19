# Contributing

## `macros.qmd` must contain only macro definitions — no comments

`macros.qmd` is consumed raw across four different paths, and no comment
syntax works in all of them:

| Path | How `macros.qmd` is used | `%` comment | `<!-- -->` comment |
|---|---|---|---|
| `macros-table.qmd` (MathJax embed + searchable table) | parsed line-by-line in R | **breaks** (only `<!--` is stripped; a `%` line is appended to and corrupts the preceding definition) | stripped, OK |
| `macros-header.html` loader (HTML / RevealJS) | parsed line-by-line in JS | skipped, OK | skipped, OK |
| `include-in-header: macros.qmd` (PDF) | inserted raw into the **LaTeX preamble** | OK (LaTeX comment) | **breaks** (`Missing \begin{document}`) |
| `{{< include macros.qmd >}}` shortcode (PDF) | included as **markdown body**, run through pandoc | **breaks** (`Missing $`; pandoc emits the prose + stray `\commands`) | OK (pandoc drops it) |

Because no comment style is safe in every column (`%` breaks the R parser and
the shortcode PDF; `<!-- -->` breaks the include-in-header PDF), **the only
safe choice is no comments at all**. Keep `macros.qmd` as a flat list of
`\def` / `\providecommand` definitions. Put any explanatory notes here instead.

## Adding a new estimand macro group

When you add a new estimand macro group (probability, risk, odds, rate,
hazard, ratio/factor types, …) near the top of `macros.qmd`, add the matching
estimator (hat-wrapped) versions in the estimator section at the bottom,
following these rules:

1. **Zero-arg:** `\def\hfoo{\hat{\foo}}`
2. **One-arg function:** `\providecommand{\hfoof}[1]{\hfoo\paren{#1}}`
3. **One `\def` alias per estimand alias, pointing at the canonical estimator:**
   `\def\hfooalias{\hfoo}` (zero-arg) and `\def\hfoofalias{\hfoof}` (function
   form). For example, `\risk`/`\prev` are estimand aliases of `\prob`, so
   `\hrisk`/`\hprev` are defined as `\def\hrisk{\hprob}` / `\def\hprev{\hprob}`.
4. **Add an entry for every new macro to `interpretations.tsv`** — the
   `macros-table.qmd` build fails if any macro is missing an interpretation.

See [issue #58](https://github.com/d-morrison/macros/issues/58) for background
and motivation on the estimator macros.

## `\h...` vs `\e...` estimator macros

`\hfoo`-style macros (e.g. `\hb`, `\hsurv`, `\hhazratio`) are the legacy
estimator family: they apply the hat accent directly (`\hat{...}` /
`\widehat{...}`), frozen for backward compatibility. Do not rename or
remove them.

`\efoo`-style macros are the parallel, forward-looking family: same
estimators, but composed through the indirection macros `\est{#1}`
(`\hat{#1}`) and `\Est{#1}` (`\widehat{#1}`) instead of applying the accent
directly. If the estimator symbol ever changes, only `\est`/`\Est` need to
change — every `\efoo` macro picks it up automatically, while the `\hfoo`
family stays pinned to `\hat`/`\widehat` forever.

When adding a new estimator macro group, define both:

1. **Legacy (`\h...`):** as above — `\hat{...}` / `\widehat{...}` directly.
2. **Forward-looking (`\e...`):** the same macro name with the leading `h`
   replaced by `e`, composed through `\est`/`\Est` instead of `\hat`/`\widehat`.
   Use `\est` for macros that used `\hat` (single symbols/short expressions)
   and `\Est` for macros that used `\widehat` (operatorname-wrapped
   multi-letter symbols, e.g. `Var`, `Cov`, `SD`, `SE`) — mirror whichever
   width the original `\h...` macro chose. Alias chains mirror too: if
   `\def\hfooalias{\hfoo}`, then `\def\efooalias{\efoo}`.
3. **Add an `interpretations.tsv` entry for every new `\e...` macro too**
   (same rule as above).

See issue #75's follow-up discussion for background on this split.

## Update `notation-choices.qmd` with every macro change

Whenever you add, rename, remove or change the output of a macro in `macros.qmd`,
update [`notation-choices.qmd`](notation-choices.qmd) in the same pull request.
Each entry there states our convention, the reasons for it,
and the other conventions readers will meet in other sources.
CI fails a pull request that changes `macros.qmd` without changing `notation-choices.qmd`.
If the page is already accurate after your change,
explain why in the description and add the `no-notation-change` label.

## Before pushing

Render the site and both demos to make sure nothing broke across the four
consumption paths above:

```bash
quarto render                                  # whole site (HTML)
quarto render demo-include-in-header.qmd --to pdf
quarto render demo-shortcode.qmd --to pdf
```
