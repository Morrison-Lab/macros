#!/usr/bin/env python3
"""Write anchor-index.json: which page of the rendered site holds each id.

anchor-landing.html reads it when a reader arrives at a page whose `#id` the page
no longer holds, because the content moved to another page, and sends them to the
page that holds the id now.  So a link from another site, a bookmark or a search
result keeps working after a definition moves, without the link being rewritten.

Runs as a `post-render` step: it scans every website page in the output directory
(`QUARTO_PROJECT_OUTPUT_DIR`, else `_site`) and writes

    {"version": 1, "ids": {"def-intercept": "algebra-polynomials.html", ...}}

with each page given relative to the site root.  It leaves out

- reveal.js decks, which repeat their page's ids (the reader wants the page);
- ids held by more than one page, such as Quarto's own page chrome,
  since a redirect to one of them would be a guess;
- ids that only number a position on the page, such as code lines (`cb3-12`),
  footnotes (`fn2`), callouts and unnumbered sections (`callout-4`, `section-1.2`),
  and random widget ids: the same id on another page is unrelated content;
- ids inside HTML comments and scripts.

Shared site scaffolding: the canonical copy is in Morrison-Lab/qwt.  The sites
built on it vendor it, with anchor-landing.html, through their
.github/workflows/sync-site-scaffolding.yml (for example Morrison-Lab/mds).
Do not edit a site's copy.

    anchor-index.py [--site DIR] [--out FILE]
"""
import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

POSITIONAL = re.compile(
    r"^(?:cb\d+(?:-\d+)?|fn(?:ref)?\d+(?:-\d+)?|callout-\d+|tabset-\d+(?:-\d+)*"
    r"|(?:toc-)?section-\d+(?:[.-]\d+)*|htmlwidget-.*|ojs-.*"
    r"|.*[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}.*)$",
    re.I,
)
OUT_NAME = "anchor-index.json"


class Ids(HTMLParser):
    """The ids on one page, read with an HTML parser.

    The parser unescapes attribute values and does not read tags inside a
    <script> or <style>, or inside a comment, so those yield no ids.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.deck = False

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name == "id" and value:
                self.ids.add(value)
            elif name == "class" and tag == "div" and value and "reveal" in value.split():
                self.deck = True

    handle_startendtag = handle_starttag


def site_pages(site):
    """The website pages in `site`, as (path relative to the site root, its ids)."""
    for path in sorted(site.rglob("*.html")):
        rel = path.relative_to(site).as_posix()
        # site_libs holds Quarto's assets; a notebook preview repeats its page's ids.
        if rel.startswith("site_libs/") or "/site_libs/" in rel or rel.endswith(".ipynb.html"):
            continue
        parser = Ids()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        parser.close()
        if not parser.deck:
            yield rel, parser.ids


def build(site):
    holders = {}
    for rel, ids in site_pages(site):
        for name in ids:
            if not POSITIONAL.match(name):
                holders.setdefault(name, set()).add(rel)
    ids = {i: next(iter(p)) for i, p in sorted(holders.items()) if len(p) == 1}
    return {"version": 1, "ids": ids}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--site", default=os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "_site"),
                    help="the rendered site (default: $QUARTO_PROJECT_OUTPUT_DIR or _site)")
    ap.add_argument("--out", help=f"where to write the index (default: SITE/{OUT_NAME})")
    args = ap.parse_args(argv)
    site = Path(args.site)
    if not site.is_dir():
        sys.exit(f"anchor-index.py: no rendered site at {site}")
    index = build(site)
    out = Path(args.out) if args.out else site / OUT_NAME
    out.write_text(json.dumps(index, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    print(f"anchor-index.py: {len(index['ids'])} ids -> {out}")


if __name__ == "__main__":
    main()
