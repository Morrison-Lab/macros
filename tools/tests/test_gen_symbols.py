"""Self-test for tools/gen_symbols.py (macros#334)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import gen_symbols as g  # noqa: E402

BS = chr(92)


def make(lines):
    return g.parse_definitions("\n".join(lines))


def test_alias_chain_shares_one_row():
    defs = make(
        [
            BS + "def" + BS + "a{" + BS + "mu}",
            BS + "def" + BS + "b{" + BS + "a}",
            BS + "def" + BS + "c{" + BS + "b}",
        ]
    )
    rows = g.build_rows(defs, {"a": "x"})
    assert len(rows) == 1, rows
    assert rows[0]["macros"] == " ".join(BS + n for n in "abc")


def test_same_body_shares_row_but_arg_count_separates():
    defs = make(
        [
            BS + "def" + BS + "p{" + BS + "alpha}",
            BS + "def" + BS + "q{" + BS + "alpha}",
            BS + "providecommand{" + BS + "r}[1]{" + BS + "alpha_{#1}}",
        ]
    )
    rows = g.build_rows(defs, {})
    assert len(rows) == 2, rows


def test_alias_of_a_macro_with_arguments_shows_them():
    defs = make(
        [
            BS + "providecommand{" + BS + "E}[1]{" + BS + "mathbb{E}[#1]}",
            BS + "def" + BS + "Ef{" + BS + "E}",
        ]
    )
    rows = g.build_rows(defs, {})
    symbols = {r["macros"]: r["symbol"] for r in rows}
    assert symbols[BS + "Ef"] == BS + "Ef{a}", symbols


def test_different_symbols_do_not_merge():
    defs = make([BS + "def" + BS + "p{x}", BS + "def" + BS + "q{y}"])
    assert len(g.build_rows(defs, {})) == 2


def test_non_letter_names_and_multiline_bodies_are_parsed():
    text = "\n".join(
        [
            BS + "def" + BS + "~{" + BS + "approx}",
            BS + "def" + BS + "'{^{" + BS + "top}}",
            BS + "providecommand{" + BS + "1}[1]{" + BS + "text{1}_{#1}}",
            BS + "def" + BS + "multi{" + BS + "a =",
            BS + "deriv{x}" + BS + "deriv{y}}",
        ]
    )
    defs = g.parse_definitions(text)
    assert set(defs) == {"~", "'", "1", "multi"}, defs
    assert defs["1"][0] == 1
    assert "deriv{y}" in defs["multi"][1]


def test_every_definition_line_in_macros_qmd_is_parsed():
    text = g.MACROS.read_text(encoding="utf-8")
    defs = g.parse_definitions(text)
    assert g.count_definition_lines(text) - len(defs) == g.REDEFINITIONS


def test_generated_file_is_current():
    defs = g.parse_definitions(g.MACROS.read_text(encoding="utf-8"))
    interp = g.read_interpretations(g.INTERP)
    text = g.render(g.build_rows(defs, interp))
    assert g.OUT.read_text(encoding="utf-8") == text


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
