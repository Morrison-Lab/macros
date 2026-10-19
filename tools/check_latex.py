#!/usr/bin/env python3
"""Check macros.qmd on the two LaTeX paths that the HTML build never touches.

1. Static guard: a name given to \\providecommand that LaTeX already defines
   is silently ignored (the #106 bug with \\sb). Typeset every such name under
   \\ifdefined in a minimal document and fail if any is already defined.
2. Brace guard: a \\providecommand, \\renewcommand, \\newcommand or \\def
   whose body ends in, or has a script after, a delimiter group must be
   wrapped in one brace pair.
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
        "PROBRISES",
        "SIGRISES",
        "DODDSRISES",
        "EXPFRISES",
        "NDISTRISES",
        "EPSPRISES",
        "INDICPRISES",
        "DODDSINVRISES",
        "DINVODDSRISES",
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


# Supported: \providecommand, \renewcommand, \newcommand, \def, \gdef and
# \DeclareRobustCommand, anywhere on a line, with the body brace on a later line.
DEFINITION_HEAD = re.compile(
    r"(?<!\\)\\(?:providecommand|renewcommand|newcommand|def|gdef|DeclareRobustCommand)"
    r"\*?\s*(?:\{(\\[A-Za-z]+)\}|(\\[A-Za-z]+))"
    r"(?:\s*\[[^\]]*\])*(?:#\d)*\s*(?=\{)"
)
# xparse definitions have another argument syntax, which the guard does not read.
UNSUPPORTED = re.compile(
    r"\\(?:New|Provide|Declare|NewExpandable)DocumentCommand\b"
)
# Floors against a parse that finds nothing: macros.qmd had 9 delimiter macros
# and 1490 definitions when the guard was written.
MIN_DELIMITER_MACROS = 9
MIN_DEFINITIONS = 400
SCRIPT_STARTS = "^_'"
# An even run of backslashes before % leaves the % a real comment start.
COMMENT = re.compile(r"(?<!\\)((?:\\\\)*)%.*$", re.M)


def group_end(text, start):
    """Index of the brace that closes the one opened at text[start].

    A backslash escapes the next character, so \\{ and \\} do not count.
    """
    depth = 0
    i = start
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def top_level_groups(body):
    """(start, end) of each brace group at depth 0 of body, in order."""
    groups = []
    i = 0
    while i < len(body):
        if body[i] == "\\":
            i += 2
        elif body[i] == "{":
            end = group_end(body, i)
            if end < 0:
                raise ValueError(f"unclosed brace in {body!r}")
            groups.append((i, end))
            i = end + 1
        else:
            i += 1
    return groups


def definitions(text):
    """(name, body) of each definition in text, comments removed."""
    text = COMMENT.sub(r"\1", text)
    found = []
    for m in DEFINITION_HEAD.finditer(text):
        start = m.end()
        end = group_end(text, start)
        if end > 0:
            found.append((m.group(1) or m.group(2), text[start + 1 : end]))
    return found


def delimiter_macros(text):
    """Names of the macros whose body ends in \\mathclose{}."""
    return {
        name for name, body in definitions(text)
        if body.rstrip().endswith(r"\mathclose{}")
    }


def script_after_delimiter(body, tail):
    """True if a script follows a delimiter group at any depth of body."""
    for start, end in top_level_groups(body):
        after = body[end + 1 :].lstrip()
        if tail.search(body[:start]) and after and after[0] in SCRIPT_STARTS:
            return True
        if script_after_delimiter(body[start + 1 : end], tail):
            return True
    return False


def unbraced_delimiter_body(body, delimiters):
    """True if body is a bare delimiter alias, ends in an unwrapped delimiter group,
    or has a script right after a delimiter group at any depth.
    """
    names = "|".join(re.escape(d[1:]) for d in delimiters)
    tail = re.compile(r"\\(?:" + names + r")\s*$")
    body = body.strip()
    if re.fullmatch(r"\\(?:" + names + ")", body):
        return True
    ends = any(
        tail.search(body[:start]) and not body[end + 1 :]
        for start, end in top_level_groups(body)
    )
    return ends or script_after_delimiter(body, tail)


def unbraced_definitions(text, delimiters):
    """Names of definitions in text with an unbraced delimiter-ending body."""
    return [
        name for name, body in definitions(text)
        if unbraced_delimiter_body(body, delimiters)
    ]


# Definitions the guard must flag, and ones it must leave alone.
GUARD_PRELUDE = (
    "\\providecommand{\\paren}[1]{\\mathopen{}\\left(#1\\right)\\mathclose{}}\n"
    "\\providecommand{\\norm}[1]{\\mathopen{}\\left\\|#1\\right\\|\\mathclose{}}\n"
    "\\providecommand{\\angb}[1]{\\mathopen{}\\left\\langle#1\\right\\rangle\\mathclose{} }\n"
)
GUARD_SHOULD_FLAG = [
    r"\providecommand{\a}[1]{\P\paren{#1}}",
    r"\providecommand{\a}[1]{{\oddst}'\paren{#1}}",
    r"\renewcommand{\a}[1]{\operatorname{exp}\paren{#1}}",
    r"\newcommand{\a}[1]{\P\paren{\foo{#1_{i}}}}",
    r"\def\a{\frac{-1}{2}\paren{x}}",
    r"\providecommand{\a}[1]{\P\norm{#1}}",
    "  \\providecommand{\\a}[1]{\\P\\paren{#1}}  % trailing comment",
    "\\providecommand{\\a}[1]{\n  \\P\\paren{#1}\n}",
    r"\providecommand{\a}[1]{\P\paren{\{}}",
    r"\providecommand{\a}[1]{{\oddst}'\paren{#1}^2}",
    r"\newcommand{\a}[2][x]{\P\paren{#1}}",
    r"\providecommand{\a}[1]{\P\paren{#1}} \\% comment with an open {",
    r"\providecommand{\a}[1]{\P\paren{\%}} % comment",
    r"\providecommand{\a}[1]{{\P\paren{#1}^2}}",
    r"\providecommand{\a}[1]{{\P\paren{#1}'}}",
    "\\providecommand{\\a}[1]{\\P \\\\% {\n  \\paren{#1}}",
    "\\providecommand{\\a}[1]\n{\\P\\paren{#1}}",
    r"\def\b{x} \def\a{\P\paren{#1}}",
    r"\gdef\a#1{\P\paren{#1}}",
    r"\def\a{\norm}",
    r"\providecommand{\a}[1]{{\frac{\paren{x}^2}{y}}}",
    r"\providecommand{\a}[1]{\frac{\paren{x}^2}{y}}",
    r"\providecommand{\a}[1]{\P\paren{#1}_{i}}",
    r"\providecommand{\a}[1]{\P\paren{#1} ^2}",
    r"\providecommand{\a}[1]{\P\paren{#1} }",
    r"\DeclareRobustCommand{\a}[1]{\P\paren{#1}}",
    r"\newcommand*{\a}[1]{\P\paren{#1}}",
    r"\providecommand{\a}[1]{\{\P\paren{#1}}",
    r"\providecommand{\a}[1]{\P\angb{#1}}",
]
GUARD_SHOULD_PASS = [
    r"\providecommand{\a}[1]{{\P\paren{#1}}}",
    r"\providecommand{\a}[1]{{\paren{#1}}^{-1}}",
    "\\providecommand{\\a}[1]{{\n  \\P\\paren{#1}\n}}",
    r"\providecommand{\a}[1]{{\P \paren{\{}}}",
    r"\def\a{{\frac{-1}{2}\paren{x}}}",
    r"\providecommand{\a}[1]{\paren{#1} + 1}",
    r"\providecommand{\a}[1]{{\P\paren{#1}}} % comment with an open {",
    r"\providecommand{\a}[1]{{\P \paren{\%}}}",
    r"\providecommand{\a}[1]{{\frac{\paren{#1}}{2}}}",
    r"\\def\a{\P\paren{#1}}",
]


def suspect_parse(delimiters, examined):
    """True if the parse found too little for a zero-unbraced result to mean anything."""
    return len(delimiters) < MIN_DELIMITER_MACROS or examined < MIN_DEFINITIONS


def unsupported_commands(text):
    """Definition commands in text that the guard cannot read."""
    return UNSUPPORTED.findall(COMMENT.sub(r"\1", text))


def guard_self_test():
    """The guard must flag each unbraced fixture and pass each braced one."""
    delimiters = delimiter_macros(GUARD_PRELUDE)
    flag = [d for d in GUARD_SHOULD_FLAG if not unbraced_definitions(d, delimiters)]
    wrong = [d for d in GUARD_SHOULD_PASS if unbraced_definitions(d, delimiters)]
    for d in flag:
        print(f"  FAIL guard missed {d!r}")
    for d in wrong:
        print(f"  FAIL guard flagged {d!r}")
    refusals = [
        label for label, held in [
            ("an empty parse passed the floors", not suspect_parse(set(), 0)),
            ("too few definitions passed the floors", not suspect_parse(
                set(range(MIN_DELIMITER_MACROS)), 0)),
            ("too few delimiter macros passed the floors", not suspect_parse(
                set(), MIN_DEFINITIONS)),
            ("a full parse failed the floors", suspect_parse(
                set(range(MIN_DELIMITER_MACROS)), MIN_DEFINITIONS)),
            ("xparse was not refused", not unsupported_commands(
                r"\NewDocumentCommand{\a}{m}{x}")),
            ("a commented xparse was refused", unsupported_commands(
                r"% \NewDocumentCommand{\a}{m}{x}")),
        ] if held
    ]
    try:
        top_level_groups("{")
        refusals.append("an unclosed brace was not refused")
    except ValueError:
        pass
    for label in refusals:
        print(f"  FAIL {label}")
    return not (flag or wrong or refusals)


def brace_guard():
    """Fail on a definition that ends in a delimiter macro and is not braced.

    A script after \\mathclose{} attaches to the empty close atom and does not
    rise over a tall argument (macros#147), so one brace pair must wrap such a
    body. The delimiter macros are the ones macros.qmd defines with a body that
    ends in \\mathclose{}. A script written directly after a delimiter group is
    the same defect.
    """
    text = (ROOT / "macros.qmd").read_text()
    delimiters = delimiter_macros(text)
    bad = unbraced_definitions(text, delimiters)
    examined = len(definitions(text))
    print(
        f"brace guard: {len(bad)} unbraced delimiter-ending definitions "
        f"({len(delimiters)} delimiter macros, {examined} definitions examined)"
    )
    # A parse that finds nothing would report zero unbraced and pass.
    if suspect_parse(delimiters, examined):
        print(
            f"  FAIL the guard found fewer than {MIN_DELIMITER_MACROS} delimiter "
            f"macros or {MIN_DEFINITIONS} definitions, so the parse is suspect"
        )
        return False
    if unsupported_commands(text):
        print("  FAIL macros.qmd uses a definition command the guard cannot read")
        return False
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
