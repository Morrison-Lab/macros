#!/usr/bin/env python3
"""Typeset every symbol in data/symbols-all.csv with mathjax-full (macros#407).

The "Every symbol" table prints each symbol as math, and a symbol that
MathJax rejects shows as an error in the browser while the build stays
green. This writes the macro definitions and the symbols to JSON, then runs
tools/check_symbols_mathjax.js on them, which exits 1 on any rejection.

Usage (mathjax-full must be resolvable, for example through NODE_PATH):
    python3 tools/check_symbols_mathjax.py

No browser is used (CLAUDE.md, "Check math without a browser").
"""
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_symbols as g  # noqa: E402

JS = Path(__file__).resolve().parent / "check_symbols_mathjax.js"


def macro_table(defs):
    """Macros in the form the TeX input jax's `macros` option takes."""
    return {
        name: ([body, nargs] if nargs else body)
        for name, (nargs, body) in defs.items()
    }


def symbols(path):
    with open(path, encoding="utf-8") as f:
        return [row["symbol"] for row in csv.DictReader(f)]


def main():
    defs = g.parse_definitions(g.MACROS.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        macros_json = Path(tmp) / "macros.json"
        symbols_json = Path(tmp) / "symbols.json"
        macros_json.write_text(json.dumps(macro_table(defs)), encoding="utf-8")
        symbols_json.write_text(json.dumps(symbols(g.OUT)), encoding="utf-8")
        result = subprocess.run(
            ["node", str(JS), str(macros_json), str(symbols_json)], check=False
        )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
