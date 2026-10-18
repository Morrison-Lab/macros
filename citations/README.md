# Numbered citations

Shared citation settings for the lab's Quarto notes sites.

- A bracketed citation, `[@key]`, prints as a number: `[1]`, or `[1, p. 5]` with a locator.
- An in-text citation, `@key`, prints the author name and the number: `James and Witten [1]`, `Hastie et al. [2]`.

## Use

A site that carries this repository as the `latex-macros` submodule adds to its `_quarto.yml`:

```yaml
csl: latex-macros/citations/numeric-author.csl
filters:
  - latex-macros/citations/numeric-citations.lua
```

Keep any filters the site already lists, in their existing order.

## Files

- `numeric-author.csl` is the IEEE style (CC BY-SA 3.0, by Michael Berkowitz and contributors) with the author name added before the number in each in-text citation.
- `numeric-citations.lua` is a Pandoc filter that runs before citeproc.
  It marks every citation that is not an in-text `@key` as author-suppressed, so citeproc prints only the number.

The filter must run before citeproc.
Quarto does this for a `filters:` entry; with the plain Pandoc command line, put `--lua-filter` before `--citeproc`.
