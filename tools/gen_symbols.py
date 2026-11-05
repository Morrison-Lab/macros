#!/usr/bin/env python3
"""Generate data/symbols-all.csv: one row per distinct symbol.

Macros that expand to the same body with the same number of arguments
print the same symbol, so they share a row (macros#334).
A macro whose whole body is another macro (a pure alias) is first resolved
to that macro, so an alias chain collapses to its end.

Usage:
    python3 tools/gen_symbols.py            # write data/symbols-all.csv
    python3 tools/gen_symbols.py --check    # exit 1 if the file is stale or
                                            # a macro has no interpretation

Why a failing check and not a warning: the page lists every symbol, and a
stale generated file would let a new macro go unlisted (macros#334).
"""
import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

BS = chr(92)
ROOT = Path(__file__).resolve().parent.parent
MACROS = ROOT / "macros.qmd"
INTERP = ROOT / "interpretations.tsv"
OUT = ROOT / "data" / "symbols-all.csv"

DEF = re.compile(
    "^" + re.escape(BS) + r"(?:def|providecommand|renewcommand|newcommand)\*?\s*\{?"
    + re.escape(BS) + r"([A-Za-z]+)\}?\s*(?:\[(\d)\])?\s*(?:#\d)*\s*\{(.*)\}\s*$"
)
ALIAS = re.compile(r"^\{?" + re.escape(BS) + r"([A-Za-z]+)\}?$")


def parse_definitions(text):
    """Map macro name to (argument count, body); a later definition wins."""
    defs = {}
    for line in text.splitlines():
        m = DEF.match(line.rstrip())
        if m:
            defs[m.group(1)] = (int(m.group(2) or 0), m.group(3))
    return defs


def canonical(name, defs, seen=()):
    """Follow pure aliases (body is exactly one other macro) to the end."""
    nargs, body = defs[name]
    m = ALIAS.match(body.strip())
    if m:
        target = m.group(1)
        if target in defs and target not in seen and defs[target][0] == nargs:
            return canonical(target, defs, seen + (name,))
    return name


def read_interpretations(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            name, _, text = line.rstrip("\n").partition("\t")
            out[name.lstrip(BS)] = text
    return out


def build_rows(defs, interp):
    groups = defaultdict(list)
    for name in sorted(defs):
        c = canonical(name, defs)
        groups[defs[c]].append(name)
    rows = []
    for names in groups.values():
        names.sort(key=lambda n: (len(n), n))
        first = names[0]
        rows.append(
            {
                "macros": " ".join(BS + n for n in names),
                "interpretation": interp.get(first, ""),
            }
        )
    rows.sort(key=lambda r: r["macros"].lower())
    return rows


def render(rows):
    import io

    buf = io.StringIO()
    w = csv.DictWriter(buf, ["macros", "interpretation"], lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    defs = parse_definitions(MACROS.read_text(encoding="utf-8"))
    interp = read_interpretations(INTERP)
    rows = build_rows(defs, interp)
    missing = [r["macros"] for r in rows if not r["interpretation"]]
    text = render(rows)
    if args.check:
        bad = False
        if missing:
            print("Rows with no interpretation:", *missing[:20], sep="\n  ")
            bad = True
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT.relative_to(ROOT)} is stale; run tools/gen_symbols.py")
            bad = True
        sys.exit(1 if bad else 0)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {len(rows)} symbols from {len(defs)} macros")


if __name__ == "__main__":
    main()
