-- Print bracketed citations as numbers, [n], and in-text citations as
-- "Author [n]". Runs before citeproc with numeric-author.csl, whose citation
-- layout prints the author name before the number; this filter suppresses the
-- name in every citation except a narrative @key.
function Cite(c)
  for _, cit in ipairs(c.citations) do
    if cit.mode == "AuthorInText" then return nil end
  end
  for _, cit in ipairs(c.citations) do
    cit.mode = "SuppressAuthor"
  end
  return c
end
