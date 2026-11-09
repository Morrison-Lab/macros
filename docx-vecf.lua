-- Word fallback for the vector mark (\vecf and the macros built on it, such
-- as \vx and \vbeta).
--
-- Pandoc's math converter (texmath) turns TeX into native Word math, and it
-- cannot read the tilde-under that \vecf draws with \smash, \raise and
-- \hbox. It prints such math as raw source, such as
-- `\mathord{\smash[b]{\underset{...`, in place of each vector (#337).
-- It cannot read any under-accent (\underset, \underline, \underbrace) either,
-- and converts only over-accents such as \tilde, which Word draws natively.
--
-- So in Word output only, this filter rewrites each expanded tilde-under
-- vector to the over-accent \tilde{...}. The tilde sits above the letter
-- instead of below it. HTML, slides and PDF keep the tilde-under.
--
-- Pandoc's markdown reader expands the \providecommand definitions of a page
-- that includes macros.qmd, so Math elements reach this filter with \vecf
-- already expanded to the form below.
--
-- Use it in a page's front matter:
--   format:
--     docx:
--       filters:
--         - latex-macros/docx-vecf.lua

-- The tilde-under vector as the reader expands it:
-- VECF_OPEN <arg>} VPHANTOM <arg>}}
local VECF_OPEN = "\\mathord{\\smash[b]{\\underset{\\raise.3ex"
  .. "\\hbox{$\\scriptstyle\\sim$}}{"
local VPHANTOM = "}\\vphantom{"

-- Index just past the brace group whose "{" is at `open`, or nil.
local function group_end(text, open)
  local depth = 0
  local i = open
  while i <= #text do
    local c = text:sub(i, i)
    if c == "\\" then
      i = i + 1
    elseif c == "{" then
      depth = depth + 1
    elseif c == "}" then
      depth = depth - 1
      if depth == 0 then
        return i + 1
      end
    end
    i = i + 1
  end
  return nil
end

-- Replace each expanded tilde-under vector with \tilde{<arg>}, matching
-- braces so an argument such as \hat{\Noise} is handled.
local function replace_vecf(text)
  local out = {}
  local pos = 1
  while true do
    local s = text:find(VECF_OPEN, pos, true)
    if not s then
      break
    end
    local arg_open = s + #VECF_OPEN - 1
    local arg_end = group_end(text, arg_open)
    local after = arg_end and text:sub(arg_end, arg_end + #VPHANTOM - 1)
    local ph_end = after == VPHANTOM
      and group_end(text, arg_end + #VPHANTOM - 1)
    if not ph_end or text:sub(ph_end, ph_end) ~= "}" then
      -- Not a well-formed tilde-under vector: keep this opening as it is
      -- and go on scanning after it.
      table.insert(out, text:sub(pos, s + #VECF_OPEN - 1))
      pos = s + #VECF_OPEN
    else
      local arg = text:sub(arg_open + 1, arg_end - 2)
      local before = text:sub(1, s - 1)
      local in_accent = (before:match("\\hat{$") or before:match("\\widehat{$"))
        and text:sub(ph_end + 1, ph_end + 1) == "}"
      table.insert(out, text:sub(pos, s - 1))
      -- Word cannot convert a second accent on the same letter, or an
      -- accent on a composite argument, so there the mark is dropped and the
      -- outer accent (such as the hat of an estimate) is kept.
      if arg:find("{", 1, true) or in_accent then
        table.insert(out, arg)
      else
        table.insert(out, "\\tilde{" .. arg .. "}")
      end
      pos = ph_end + 1
    end
  end
  table.insert(out, text:sub(pos))
  return table.concat(out)
end

function Math(m)
  if not string.match(FORMAT, "docx") then
    return nil
  end
  local text = replace_vecf(m.text)
  if text ~= m.text then
    m.text = text
    return m
  end
  return nil
end
