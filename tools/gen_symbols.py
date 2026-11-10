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
# Names that macros.qmd defines more than once on purpose; update this count
# when a definition is added twice deliberately.
REDEFINITIONS = 3
# Symbols that do not typeset as the macro name plus placeholders: the two
# halves of an environment need each other, and a macro whose body is a
# TeX primitive that takes an argument has no definition here to read.
SYMBOL_OVERRIDES = {
    "ba": BS + "ba a" + BS + "ea",
    "ea": BS + "ba a" + BS + "ea",
    "ub": BS + "ub{a}",
}

START = re.compile(
    "^" + re.escape(BS) + r"(?:def|providecommand|renewcommand|newcommand)\*?[ \t]*\{?",
    re.M,
)
# A control-sequence name is letters, or one non-letter character (as in the
# tilde and prime macros).
NAME = re.compile(re.escape(BS) + r"([A-Za-z]+|[^A-Za-z])")
ARGS = re.compile(r"\}?[ \t]*(?:\[(\d)\])?[ \t]*(?:#\d)*[ \t\n]*")
ALIAS = re.compile(r"^\{?" + re.escape(BS) + r"([A-Za-z]+)\}?$")


def read_body(text, i):
    """Return the contents of the brace group that opens at text[i]."""
    depth = 0
    j = i
    while j < len(text):
        c = text[j]
        if c == BS:
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1 : j]
        j += 1
    raise ValueError(f"unbalanced braces in the definition at offset {i}")


def count_definition_lines(text):
    """How many definition commands start a line (the completeness target)."""
    return len(START.findall(text))


def parse_definitions(text):
    """Map macro name to (argument count, body); a later definition wins.

    The body may span lines, and the name may be one non-letter character.
    """
    defs = {}
    for m in START.finditer(text):
        nm = NAME.match(text, m.end())
        if not nm:
            continue
        am = ARGS.match(text, nm.end())
        k = am.end()
        if k >= len(text) or text[k] != "{":
            continue
        nargs = int(am.group(1)) if am.group(1) else 0
        defs[nm.group(1)] = (nargs, read_body(text, k))
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


def shown_args(name, defs, seen=()):
    """Number of arguments to show after a macro's name in the symbol column.

    A macro with no arguments whose body is another macro that takes some
    (an alias such as Ef for E) is shown with the arguments of that macro,
    because the typeset symbol would otherwise be missing them.
    """
    nargs, body = defs[name]
    m = ALIAS.match(body.strip())
    if nargs == 0 and m:
        target = m.group(1)
        if target in defs and target not in seen and target != name:
            return shown_args(target, defs, seen + (name,))
    return nargs


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
        nargs = shown_args(first, defs)
        placeholders = "".join("{" + "abcdefghi"[i] + "}" for i in range(nargs))
        rows.append(
            {
                "macros": " ".join(BS + n for n in names),
                "symbol": SYMBOL_OVERRIDES.get(first, BS + first + placeholders),
                "interpretation": interp.get(first, ""),
            }
        )
    rows.sort(key=lambda r: r["macros"].lower())
    return rows


def render(rows):
    import io

    buf = io.StringIO()
    w = csv.DictWriter(buf, ["macros", "symbol", "interpretation"], lineterminator="\n")
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
        n_lines = count_definition_lines(MACROS.read_text(encoding="utf-8"))
        if len(defs) > n_lines:
            print(f"Parsed {len(defs)} names from only {n_lines} definition lines")
            bad = True
        # Redefinitions make n_lines exceed len(defs); count them so a
        # silently skipped definition cannot hide inside that gap.
        if n_lines - len(defs) != REDEFINITIONS:
            print(
                f"{n_lines - len(defs)} definition lines were not parsed or "
                f"redefine a name (expected {REDEFINITIONS} redefinitions)"
            )
            bad = True
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
