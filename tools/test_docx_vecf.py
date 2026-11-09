#!/usr/bin/env python3
"""Check that docx-vecf.lua gives the vector mark a Word fallback (#337).

Pandoc cannot convert the tilde-under that \\vecf draws, so without the filter
the Word output of a page that uses \\vx prints raw TeX. This script converts a
small page that includes macros.qmd to .docx twice, without and with the
filter, using the Pandoc that Quarto bundles, and checks that:

- the control (no filter) warns about the tilde-under and keeps raw TeX, so
  the test can fail;
- the filtered run has no conversion warning, and the Word text has a tilde
  over each plain vector. An estimated vector (\\hvb) keeps only its hat,
  because Word cannot convert two accents on one letter.

Run from the repository root: python3 tools/test_docx_vecf.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILTER = ROOT / "docx-vecf.lua"

# \hvb is a hat over a vector, and \vecf{\hat{\Noise}} has a nested argument;
# the filter must match both by brace depth.
PAGE = r"""
$\vx$

$\vbeta^\top \vx_i$

$\vecf{\hat{\Noise}}$

$\hvb$
"""


def pandoc(args, **kwargs):
    return subprocess.run(
        ["quarto", "pandoc", *args], capture_output=True, text=True, check=True, **kwargs
    )


def to_docx(markdown, out, filters):
    args = ["-f", "markdown", "-t", "docx", "-o", str(out)]
    for f in filters:
        args += ["--lua-filter", str(f)]
    return pandoc(args, input=markdown).stderr


def docx_text(path):
    return pandoc(["-t", "plain", str(path)]).stdout


def main():
    markdown = (ROOT / "macros.qmd").read_text() + "\n" + PAGE
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        plain = Path(tmp) / "plain.docx"
        filtered = Path(tmp) / "filtered.docx"
        control_err = to_docx(markdown, plain, [])
        filtered_err = to_docx(markdown, filtered, [FILTER])
        control_text = docx_text(plain)
        filtered_text = docx_text(filtered)

    if "smash" not in control_err or "smash" not in control_text:
        failures.append("control: the unfiltered run does not show the raw tilde-under, so this test cannot fail")
    for word in ("smash", "underset"):
        if word in filtered_err or word in filtered_text:
            failures.append(f"filtered run still mentions {word}")
    if "Could not convert" in filtered_err:
        failures.append("filtered run still has a conversion warning")
    if filtered_text.count("̃") < 3:
        failures.append("filtered text does not have a combining tilde over each plain vector")
    if "̂" not in filtered_text:
        failures.append("filtered text lost the hat of the estimated vector")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        print("--- filtered text ---")
        print(filtered_text)
        return 1
    print("ok: docx-vecf.lua replaces the tilde-under vector with an over-tilde in Word output")
    return 0


if __name__ == "__main__":
    sys.exit(main())
