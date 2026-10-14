#!/usr/bin/env python3
"""Check macros.qmd on the two LaTeX paths that the HTML build never touches.

1. Static guard: a name given to \\providecommand that LaTeX already defines
   is silently ignored (the #106 bug with \\sb). Typeset every such name under
   \\ifdefined in a minimal document and fail if any is already defined.
2. PDF render: render _tests/*.qmd to PDF through the include-in-header path
   and the include-shortcode path, fail on any LaTeX error, and check that
   macros whose meaning differs by path print what they should.

Set CHECK_LATEX_ENGINE (for example pdflatex) to override Quarto's pdf-engine.
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROVIDE = re.compile(r"^\\providecommand\*?\{\\([A-Za-z]+)\}", re.M)

# (test document, strings its extracted text must contain)
EXPECTED = {
    "pdf-include-in-header": ["E[X+Y]", "X1,...,Xn"],
    "pdf-shortcode": ["E[X+Y]", "X1,...,Xn"],
}

# Already defined by unicode-math under xelatex, where it is the script
# alphabet this file wants, so its providecommand is a no-op by design.
ALLOWED = {"mathscr"}


def static_guard():
    names = sorted(set(PROVIDE.findall((ROOT / "macros.qmd").read_text())))
    lines = [
        r"\documentclass{article}",
        r"\usepackage{amsmath,amssymb,unicode-math}",
        r"\begin{document}",
    ]
    for name in names:
        lines.append(
            r"\ifdefined\%s\typeout{ALREADY-DEFINED %s}\fi" % (name, name)
        )
    lines.append(r"\end{document}")
    with tempfile.TemporaryDirectory() as tmp:
        tex = pathlib.Path(tmp) / "guard.tex"
        tex.write_text("\n".join(lines))
        engine = "xelatex" if shutil.which("xelatex") else "pdflatex"
        out = subprocess.run(
            [engine, "-interaction=nonstopmode", "guard.tex"],
            cwd=tmp, capture_output=True, text=True,
        ).stdout
    bad = [n for n in re.findall(r"ALREADY-DEFINED (\w+)", out) if n not in ALLOWED]
    print(f"static guard: {len(names)} \\providecommand names checked")
    for name in bad:
        print(f"  FAIL \\{name} is already defined, so \\providecommand does nothing")
    return not bad


def render_checks():
    ok = True
    env = os.environ.copy()
    engine = env.get("CHECK_LATEX_ENGINE")
    for stem, wanted in EXPECTED.items():
        src = ROOT / "_tests" / f"{stem}.qmd"
        cmd = ["quarto", "render", str(src), "--to", "pdf"]
        if engine:
            cmd += ["-M", f"pdf-engine:{engine}"]
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        pdfs = list((ROOT / "_site").rglob(f"{stem}.pdf")) + list(
            (ROOT / "_tests").glob(f"{stem}.pdf")
        )
        if res.returncode != 0 or not pdfs:
            print(f"render {stem}: FAIL (LaTeX error)")
            print(res.stdout[-2000:] + res.stderr[-2000:])
            ok = False
            continue
        text = subprocess.run(
            ["pdftotext", str(pdfs[0]), "-"], capture_output=True, text=True
        ).stdout
        text = re.sub(r"\s+", "", text)
        for s in wanted:
            if s not in text:
                print(f"render {stem}: FAIL, extracted text lacks {s!r}")
                ok = False
        else:
            print(f"render {stem}: rendered")
    return ok


if __name__ == "__main__":
    good = static_guard()
    good = render_checks() and good
    sys.exit(0 if good else 1)
