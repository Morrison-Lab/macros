# Copilot Instructions

## Quarto rendering

Before requesting review on any change to a `.qmd` file:

1. **Always render the document locally** (`quarto render <file> --to html`; do not run `quarto preview`, which opens a browser) and inspect the HTML output as text.
2. **Verify that math renders correctly** — typeset the changed expressions with `mathjax-full` in node, without a browser (see "Check math without a browser" in `CLAUDE.md`), and confirm the output has no error and the expected size.
3. **Do not push until rendering succeeds** and the output looks as intended.

This step is required because MathJax rendering failures are silent in R/knitr output.
