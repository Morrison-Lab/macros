// Typeset every symbol in data/symbols-all.csv with mathjax-full and exit 1
// if MathJax rejects any (macros#407). No browser: mathjax-full runs in node.
// Usage: node tools/check_symbols_mathjax.js macros.json symbols.json
// The two JSON files come from tools/check_symbols_mathjax.py.
const fs = require("fs");
const { mathjax } = require("mathjax-full/js/mathjax.js");
const { TeX } = require("mathjax-full/js/input/tex.js");
const { SVG } = require("mathjax-full/js/output/svg.js");
const { liteAdaptor } = require("mathjax-full/js/adaptors/liteAdaptor.js");
const { RegisterHTMLHandler } = require("mathjax-full/js/handlers/html.js");
const { AllPackages } = require("mathjax-full/js/input/tex/AllPackages.js");

const macros = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const symbols = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
// MathJax prints an undefined macro as text unless noundefined is off, and
// the format error handler below makes every error throw.
const packages = AllPackages.filter((p) => p !== "noundefined" && p !== "autoload");
const tex = new TeX({
  packages,
  macros,
  formatError: (jax, err) => {
    throw err;
  },
});
const doc = mathjax.document("", {
  InputJax: tex,
  OutputJax: new SVG({ fontCache: "none" }),
});

// Controls that must fail, so a run that rejects nothing cannot pass by
// failing to detect anything.
const controls = ["\\definitelyundefinedmacro{a}", "\\frac{a}"];
const bad = [];
for (const c of controls) {
  try {
    doc.convert(c, { display: false });
    bad.push(["CONTROL DID NOT FAIL", c]);
  } catch (e) {
    // expected
  }
}
for (const s of symbols) {
  try {
    doc.convert(s, { display: false });
  } catch (e) {
    bad.push([s, String(e.message).slice(0, 120)]);
  }
}
console.log(`typeset ${symbols.length} symbols; ${bad.length} failures`);
for (const [s, msg] of bad) console.log(`  ${s}: ${msg}`);
process.exit(bad.length ? 1 : 0);
