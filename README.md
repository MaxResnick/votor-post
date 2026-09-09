# votor-post

Write the post in `post.md` (Typora). Everything else is plumbing.

```
post.md          your prose, headings, and @figure lines
figures/*.html   the figure bodies (algorithm pairs, map, heatmaps)
algorithms/*.txt the pseudocode listings, with <mark> / <mark class="del"> / <mark class="add"> diff spans
template.html    CSS, nav, TOC, and the scripts
build.py         assembles out/index.html (local) and out/votor-diff.html (artifact source)
```

## Loop

```bash
python3 build.py --serve
```

then open http://localhost:8641/ and reload after each save. `--watch` rebuilds without serving; no flag builds once.

## post.md syntax

- `# Heading` is a section (shows in the sidebar TOC); `## Heading` is a subsection.
- `@figure step1: caption text` inserts `figures/step1.html`, numbered in document order. Caption may be empty.
- `@fig(step1)` inline becomes "Figure 1", so figures renumber themselves when reordered.
- Paragraphs, `- ` / `1. ` lists, `**bold**`, `*italic*`, `` `code` ``, `[text](url)`, ``` fences, `> quote`, and raw HTML lines all work.
- Front matter at the top sets title, subtitle, author, author_url, date. Leave `subtitle:` empty to hide it.

## Editing a listing

Each line of `algorithms/<id>.txt` is `NN  text` (line number, two spaces, text; four spaces per indent level).
Wrap changed text in `<mark>…</mark>`, deleted in `<mark class="del">`, added in `<mark class="add">`.
Use `&lt;` for a literal `<`.

## Publishing

Ask Claude to publish `out/votor-diff.html` to the existing artifact URL.
