#!/usr/bin/env python3
"""Check macros.qmd on the two LaTeX paths that the HTML build never touches.

1. Static guard: a name given to \\providecommand that LaTeX already defines
   is silently ignored (the #106 bug with \\sb). Typeset every such name under
   \\ifdefined in a minimal document and fail if any is already defined.
2. Brace guard: a one-line \\providecommand, \\renewcommand or \\newcommand
   whose body ends in a delimiter macro must be wrapped in one brace pair.
3. PDF render: render _tests/*.qmd to PDF through the include-in-header path
   and the include-shortcode path, fail on any LaTeX error, and check that
   macros whose meaning differs by path print what they should.

Set CHECK_LATEX_ENGINE (for example pdflatex) to override Quarto's pdf-engine.
"""
import os
import pathlib
import re
import subprocess
import sys
import unicodedata
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROVIDE = re.compile(r"^\\providecommand\*?\{\\([A-Za-z]+)\}", re.M)

# (test document, strings its extracted text must contain)
EXPECTED = {
    "pdf-include-in-header": ["E[X+Y]", "X1,...,Xn"],
    "pdf-shortcode": ["E[X+Y]", "X1,...,Xn"],
    # Box-height tests: an exponent after an f form rises over a tall argument.
    # CTRLSTUCK is the control: an unbraced body must not rise.
    "fform-exponent": [
        "EFRISES",
        "VARRISES",
        "PFRISES",
        "SIGRISES",
        "DODDSRISES",
        "EXPFRISES",
        "CTRLSTUCK",
    ],
    # pdftotext puts a hat after its letter and may reorder scripts, and NFKC
    # folds a script letter to its plain letter, so these strings pin which
    # macro prints which letter, not the script or subscript position.
    # EXPRISES is printed by a box-height test in the page: an exponent after
    # \meanfnoff must rise over a tall argument (the macros#147 brace rule).
    "distribution-models": [
        "EXPRISES",
        "DMEMP,",
        "DFAMSUBP2lin",
        "EDMEMP̂",
        "PFAMY,",
        "PFAMSUBY2lin",
        "MEANSUBμ2P",
        "MEANAPPμP̂(x)2",
        "MEANTRUEμP(x)",
        "MEANTALLμab",
        "GROWTHRISES",
        "VCRISES",
        "GROWTHmY,",
        "GROWTHAPPmY(2n)2",
    ],
}


def static_guard():
    names = sorted(set(PROVIDE.findall((ROOT / "macros.qmd").read_text())))
    lines = [
        r"\documentclass{article}",
        r"\usepackage{amsmath,amssymb}",
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
        engine = "pdflatex"
        res = subprocess.run(
            [engine, "-interaction=nonstopmode", "guard.tex"],
            cwd=tmp, capture_output=True, text=True,
        )
    out = res.stdout
    # A broken TeX install would print no ALREADY-DEFINED lines either,
    # so insist that the guard document compiled before trusting an empty list.
    if res.returncode != 0 or "Transcript written" not in out:
        print("static guard: FAIL, the guard document did not compile")
        print(out[-2000:])
        return False
    bad = re.findall(r"ALREADY-DEFINED (\w+)", out)
    print(f"static guard: {len(names)} \\providecommand names checked")
    for name in bad:
        print(f"  FAIL \\{name} is already defined, so \\providecommand does nothing")
    return not bad


DEFINITION = re.compile(
    r"^\\(?:providecommand|renewcommand|newcommand)\*?\{(\\[A-Za-z]+)\}"
    r"(?:\[\d\])?\{(.*)\}$"
)
DELIMITER_TAIL = re.compile(r"\\(?:paren|sb|cb|angb) ?$")


def closing_index(text, start):
    """Index of the brace that closes the one opened at text[start]."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def opening_index(text, end):
    """Index of the brace that opens the one closed at text[end]."""
    depth = 0
    for i in range(end, -1, -1):
        if text[i] == "}":
            depth += 1
        elif text[i] == "{":
            depth -= 1
            if depth == 0:
                return i
    return -1


def is_unbraced_delimiter_body(body):
    """True if body ends in a delimiter macro and no one brace pair wraps it."""
    if not body.endswith("}"):
        return False
    wrapped = body.startswith("{") and closing_index(body, 0) == len(body) - 1
    start = opening_index(body, len(body) - 1)
    return not wrapped and start > 0 and bool(DELIMITER_TAIL.search(body[:start]))


def unbraced_definitions(text):
    """Names of one-line definitions whose body ends in an unwrapped delimiter."""
    found = []
    for line in text.splitlines():
        m = DEFINITION.match(line)
        if m and is_unbraced_delimiter_body(m.group(2)):
            found.append(m.group(1))
    return found


# Definitions the guard must flag, and ones it must leave alone.
GUARD_SHOULD_FLAG = [
    r"\providecommand{\a}[1]{\P\paren{#1}}",
    r"\providecommand{\a}[1]{{\oddst}'\cb{#1}}",
    r"\renewcommand{\a}[1]{\operatorname{exp}\cb{#1}}",
    r"\providecommand{\a}[1]{\P\paren{\foo{#1_{i}}}}",
]
GUARD_SHOULD_PASS = [
    r"\providecommand{\a}[1]{{\P\paren{#1}}}",
    r"\providecommand{\a}[1]{{\paren{#1}}^{-1}}",
    r"\providecommand{\a}[1]{{\oddst}'\cb{#1}^2}",
]


def guard_self_test():
    """The guard must flag each unbraced fixture and pass each braced one."""
    missed = [d for d in GUARD_SHOULD_FLAG if not unbraced_definitions(d)]
    wrong = [d for d in GUARD_SHOULD_PASS if unbraced_definitions(d)]
    for d in missed:
        print(f"  FAIL guard missed {d}")
    for d in wrong:
        print(f"  FAIL guard flagged {d}")
    return not (missed or wrong)


def brace_guard():
    """Fail on a one-line definition that ends in a delimiter macro unbraced.

    A script after \\mathclose{} attaches to the empty close atom and does not
    rise over a tall argument (macros#147), so one brace pair must wrap such a
    body. Multi-line definitions are not examined.
    """
    bad = unbraced_definitions((ROOT / "macros.qmd").read_text())
    print(f"brace guard: {len(bad)} unbraced delimiter-ending definitions")
    for name in bad:
        print(f"  FAIL {name} needs a braced body, {{...}}, so an exponent rises")
    return guard_self_test() and not bad


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
        text = re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))
        stem_ok = True
        for s in wanted:
            if s not in text:
                print(f"render {stem}: FAIL, extracted text lacks {s!r}; got {text[:200]!r}")
                stem_ok = False
        if stem_ok:
            print(f"render {stem}: rendered")
        ok = ok and stem_ok
    return ok


if __name__ == "__main__":
    good = static_guard()
    good = brace_guard() and good
    good = render_checks() and good
    sys.exit(0 if good else 1)
