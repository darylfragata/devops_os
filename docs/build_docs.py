#!/usr/bin/env python3
"""Builds docs/index.html from this repo's own markdown files.

Stdlib only, no pip install needed to run it. Re-run after editing any
source file listed in MANIFEST below, then commit the regenerated
docs/index.html alongside your change -- it's generated output, not
hand-maintained, so it can't drift from the markdown it's built from.

Usage: python3 docs/build_docs.py
"""

import html
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = Path(__file__).resolve().parent / "index.html"

# (group, title, path relative to repo root)
MANIFEST = [
    ("Overview", "Introduction", "README.md"),
    ("Overview", "AI Router (CLAUDE.md)", "CLAUDE.md"),
    ("Overview", "Setup & Naming", "setup.md"),
    ("Reference", "Retrieval Questions", "00-System/Retrieval-Questions.md"),
    ("Reference", "Third-Party Skills", "THIRD_PARTY_SKILLS.md"),
]


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


# ---------------------------------------------------------------------------
# Minimal markdown -> HTML. Covers exactly what this repo's docs actually
# use: ATX headers, bold/italic/strikethrough/inline code, fenced code
# blocks, links, unordered/ordered lists (one level of nesting), GFM pipe
# tables, blockquotes, horizontal rules, paragraphs. Not a general-purpose
# CommonMark implementation -- if a new doc uses something not listed here,
# extend this function and re-run the build.
# ---------------------------------------------------------------------------

INLINE_CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
STRIKE_RE = re.compile(r"~~([^~]+)~~")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\s][^*]*?)\*(?!\*)")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]")

# Set once per document by markdown_to_html() before any inline rendering,
# so relative markdown links resolve against the *source* file's directory,
# not docs/index.html's own location.
PATH_TO_PAGE_ID: dict = {}
CURRENT_DOC_DIR = Path(".")


def resolve_link(url: str) -> str:
    if re.match(r"^(https?:|mailto:|#)", url):
        return url
    path_part, _, fragment = url.partition("#")
    if not path_part:
        return url
    try:
        resolved = (REPO_ROOT / CURRENT_DOC_DIR / path_part).resolve()
    except OSError:
        return url

    try:
        rel_to_root = resolved.relative_to(REPO_ROOT).as_posix()
        if rel_to_root in PATH_TO_PAGE_ID:
            return f"#{PATH_TO_PAGE_ID[rel_to_root]}"
        # Not one of the indexed pages (e.g. a schema/*.json file) --
        # point at the real file relative to docs/index.html's own
        # location, not the original (now-wrong) relative path.
        out = f"../{rel_to_root}"
    except ValueError:
        # Outside this repo entirely (e.g. a sibling repo, checked out
        # alongside this one, not inside it). docs/index.html
        # sits at REPO_ROOT/docs/, so escaping to a repo sibling always takes
        # exactly two "../" regardless of the *original* file's own depth.
        try:
            rel_to_parent = resolved.relative_to(REPO_ROOT.parent).as_posix()
            out = f"../../{rel_to_parent}"
        except ValueError:
            return url
    return f"{out}#{fragment}" if fragment else out


def render_inline(text: str) -> str:
    # Placeholder-protect inline code first so ** or _ inside `code` isn't
    # touched by the other inline rules.
    codes = []

    def stash_code(m):
        codes.append(html.escape(m.group(1)))
        return f"\x00{len(codes) - 1}\x00"

    text = INLINE_CODE_RE.sub(stash_code, text)
    text = html.escape(text)
    text = LINK_RE.sub(lambda m: f'<a href="{html.escape(resolve_link(m.group(2)), quote=True)}">{m.group(1)}</a>', text)
    # Obsidian wikilinks are not resolvable from this standalone page, so show
    # the label (or the note name) rather than the raw [[...]] syntax.
    text = WIKILINK_RE.sub(lambda m: f'<span class="wikilink">{m.group(3) or m.group(1).rsplit("/", 1)[-1]}</span>', text)
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = STRIKE_RE.sub(r"<del>\1</del>", text)
    text = ITALIC_RE.sub(r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", text)
    return text


def render_table(lines: list) -> str:
    header = [c.strip() for c in lines[0].strip().strip("|").split("|")]
    rows = [
        [c.strip() for c in line.strip().strip("|").split("|")]
        for line in lines[2:]
    ]
    out = ["<table>", "<thead><tr>"]
    out += [f"<th>{render_inline(c)}</th>" for c in header]
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>" + "".join(f"<td>{render_inline(c)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


CHECKBOX_RE = re.compile(r"^\[( |x|X)\]\s+(.*)$")


def render_list_item_text(text: str) -> str:
    m = CHECKBOX_RE.match(text)
    if m:
        checked = "checked disabled" if m.group(1).lower() == "x" else "disabled"
        return f'<input type="checkbox" {checked}> {render_inline(m.group(2))}'
    return render_inline(text)


LIST_ITEM_RE = re.compile(r"^(\s*)(?:([-*])|(\d+)\.)\s+(.*)$")


def render_list(lines: list) -> str:
    """Renders a block of list-item lines (mixed ordered/unordered, mixed
    indentation) into properly nested <ul>/<ol>. A nested list's opening
    tag goes inside its parent <li>, before that <li> closes -- so a
    parent's </li> is only emitted once we know (by seeing a shallower or
    equal-depth line, or running out of lines) that no deeper child
    follows it."""
    items = []
    for line in lines:
        m = LIST_ITEM_RE.match(line)
        indent = len(m.group(1))
        ordered = m.group(3) is not None
        items.append((indent, "ol" if ordered else "ul", m.group(4)))

    out = []
    stack = []  # [{"indent": int, "tag": "ul"|"ol"}, ...], outermost first

    for indent, tag, text in items:
        while stack and (stack[-1]["indent"] > indent or (stack[-1]["indent"] == indent and stack[-1]["tag"] != tag)):
            out.append("</li>")
            out.append(f"</{stack[-1]['tag']}>")
            stack.pop()
        if not stack or stack[-1]["indent"] < indent:
            out.append(f"<{tag}>")
            stack.append({"indent": indent, "tag": tag})
        else:
            out.append("</li>")  # same indent, same tag: close the previous sibling <li>
        out.append(f"<li>{render_list_item_text(text)}")

    while stack:
        out.append("</li>")
        out.append(f"</{stack[-1]['tag']}>")
        stack.pop()
    return "".join(out)


def markdown_to_html(text: str) -> str:
    text = text.replace("\r\n", "\n")
    # Drop a leading YAML front matter block (--- ... ---) so it isn't shown as text.
    text = re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
    lines = text.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # Fenced code block
        m = re.match(r"^```(\w*)\s*$", line)
        if m:
            lang = m.group(1)
            i += 1
            body = []
            while i < n and not re.match(r"^```\s*$", lines[i]):
                body.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            if lang == "mermaid":
                # Rendered client-side by mermaid.js (see PAGE_TEMPLATE) --
                # it auto-detects any element with class="mermaid" on load.
                out.append(f'<pre class="mermaid">{html.escape(chr(10).join(body))}</pre>')
            else:
                cls = f' class="language-{html.escape(lang)}"' if lang else ""
                out.append(f"<pre><code{cls}>{html.escape(chr(10).join(body))}</code></pre>")
            continue

        # Blank line
        if line.strip() == "":
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^-{3,}\s*$", line) or re.match(r"^\*{3,}\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # Header
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{render_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # Table (header row + separator row)
        if "|" in line and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]) and "-" in lines[i + 1]:
            block = [line]
            i += 1
            block.append(lines[i])
            i += 1
            while i < n and "|" in lines[i] and lines[i].strip() != "":
                block.append(lines[i])
                i += 1
            out.append(render_table(block))
            continue

        # Blockquote
        if line.startswith(">"):
            block = []
            while i < n and lines[i].startswith(">"):
                block.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            out.append(f"<blockquote>{render_inline(' '.join(block))}</blockquote>")
            continue

        # Unordered / ordered list, any depth/type mix -- render_list()
        # sorts out nesting from each line's own indent and marker.
        if LIST_ITEM_RE.match(line):
            block = []
            while i < n and lines[i].strip() != "":
                if LIST_ITEM_RE.match(lines[i]):
                    block.append(lines[i])
                elif lines[i][0] in " \t":
                    # indented continuation of the previous item's text
                    block[-1] = block[-1] + " " + lines[i].strip()
                else:
                    break
                i += 1
            out.append(render_list(block))
            continue

        # Paragraph (consume until blank line or a line starting a new block)
        para = [line]
        i += 1
        while i < n and lines[i].strip() != "" and not re.match(r"^(#{1,4})\s|^```|^\s*[-*]\s+|^\s*\d+\.\s+|^>|^-{3,}\s*$", lines[i]):
            para.append(lines[i])
            i += 1
        out.append(f"<p>{render_inline(' '.join(p.strip() for p in para))}</p>")

    return "\n".join(out)


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>devops_os -- Docs</title>
<script>
// Runs before CSS paints, so a saved theme choice applies immediately --
// no flash of the wrong theme on load. Falls back silently (no explicit
// choice applied) if localStorage is blocked, e.g. a private window.
(function () {{
  try {{
    var saved = localStorage.getItem('theme');
    if (saved === 'dark' || saved === 'light') {{
      document.documentElement.setAttribute('data-theme', saved);
    }}
  }} catch (e) {{}}
}})();
// Shared by the mermaid init (module script, below) and the toggle button --
// resolves the *effective* theme: an explicit choice always wins, otherwise
// falls back to the OS preference.
function resolveTheme() {{
  var explicit = document.documentElement.getAttribute('data-theme');
  if (explicit === 'dark' || explicit === 'light') return explicit;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}}
</script>
<style>
:root {{
  --bg: #ffffff; --fg: #1a1a1a; --muted: #6b7280; --border: #e5e7eb;
  --sidebar-bg: #f8f9fb; --code-bg: #f3f4f6; --accent: #2563eb;
  --accent-bg: #eff6ff;
}}
/* OS preference applies only when no explicit choice has been made below */
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #16181d; --fg: #e6e6e6; --muted: #9aa1ac; --border: #2c2f36;
    --sidebar-bg: #1b1e24; --code-bg: #21242b; --accent: #7aa2f7;
    --accent-bg: #1e293f;
  }}
}}
/* Explicit choice via the toggle button, persisted in localStorage --
   always wins over both the OS preference and the light default above. */
:root[data-theme="dark"] {{
  --bg: #16181d; --fg: #e6e6e6; --muted: #9aa1ac; --border: #2c2f36;
  --sidebar-bg: #1b1e24; --code-bg: #21242b; --accent: #7aa2f7;
  --accent-bg: #1e293f;
}}
#theme-toggle {{
  position: fixed; top: 12px; right: 16px; z-index: 20;
  background: var(--sidebar-bg); color: var(--fg); border: 1px solid var(--border);
  border-radius: 8px; padding: 6px 12px; font-size: 13px; cursor: pointer;
  font-family: inherit;
}}
#theme-toggle:hover {{ background: var(--border); }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--bg); color: var(--fg);
  font: 15px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  display: flex; min-height: 100vh;
}}
nav {{
  width: 260px; flex: 0 0 260px; background: var(--sidebar-bg);
  border-right: 1px solid var(--border); padding: 20px 12px;
  overflow-y: auto; position: sticky; top: 0; height: 100vh;
}}
nav h1 {{ font-size: 15px; margin: 0 8px 16px; }}
nav .group {{ margin-bottom: 14px; }}
nav .group-title {{
  font-size: 11px; text-transform: uppercase; letter-spacing: .05em;
  color: var(--muted); margin: 0 8px 6px; font-weight: 600;
}}
nav a {{
  display: block; padding: 6px 8px; border-radius: 6px; color: var(--fg);
  text-decoration: none; font-size: 13.5px; line-height: 1.3;
}}
nav a:hover {{ background: var(--border); }}
nav a.active {{ background: var(--accent-bg); color: var(--accent); font-weight: 600; }}
main {{ flex: 1; padding: 32px 40px 80px; max-width: 860px; }}
.page {{ display: none; }}
.page.active {{ display: block; }}
h1, h2, h3, h4 {{ line-height: 1.3; }}
h1 {{ font-size: 26px; border-bottom: 1px solid var(--border); padding-bottom: 10px; }}
h2 {{ font-size: 20px; margin-top: 34px; }}
h3 {{ font-size: 16px; margin-top: 26px; }}
h4 {{ font-size: 14px; margin-top: 20px; }}
a {{ color: var(--accent); }}
code {{
  background: var(--code-bg); padding: 2px 5px; border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
}}
pre {{
  background: var(--code-bg); padding: 12px 14px; border-radius: 8px;
  overflow-x: auto; border: 1px solid var(--border);
}}
pre code {{ background: none; padding: 0; }}
pre.mermaid {{
  background: none; border: none; padding: 8px 0; text-align: center;
  overflow-x: auto;
}}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }}
th, td {{ border: 1px solid var(--border); padding: 6px 10px; text-align: left; vertical-align: top; }}
th {{ background: var(--sidebar-bg); }}
blockquote {{
  border-left: 3px solid var(--border); margin: 16px 0; padding: 4px 16px;
  color: var(--muted);
}}
hr {{ border: none; border-top: 1px solid var(--border); margin: 28px 0; }}
ul, ol {{ padding-left: 22px; }}
li {{ margin: 4px 0; }}
li input[type="checkbox"] {{ margin-right: 6px; }}
::selection {{ background: var(--accent-bg); }}
@media (max-width: 720px) {{
  body {{ flex-direction: column; }}
  nav {{ width: auto; flex: none; height: auto; position: static; border-right: none; border-bottom: 1px solid var(--border); }}
  main {{ padding: 20px; }}
}}
</style>
</head>
<body>
<button id="theme-toggle" type="button" aria-label="Toggle dark/light theme"></button>
<nav>
<h1>devops_os</h1>
{NAV_HTML}
</nav>
<main>
{PAGES_HTML}
</main>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  // Sets the diagrams' initial theme only -- toggling light/dark after load
  // doesn't re-render already-drawn diagrams (a real, if minor, limitation).
  mermaid.initialize({{
    startOnLoad: true,
    theme: resolveTheme() === 'dark' ? 'dark' : 'default'
  }});
</script>
<script>
function updateThemeButton() {{
  var btn = document.getElementById('theme-toggle');
  if (!btn) return;
  btn.textContent = resolveTheme() === 'dark' ? '☀️ Light' : '🌙 Dark';
}}
function toggleTheme() {{
  var next = resolveTheme() === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  try {{ localStorage.setItem('theme', next); }} catch (e) {{}}
  updateThemeButton();
}}
document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
updateThemeButton();
function show(id) {{
  document.querySelectorAll('.page').forEach(function (el) {{ el.classList.remove('active'); }});
  document.querySelectorAll('nav a').forEach(function (el) {{ el.classList.remove('active'); }});
  var page = document.getElementById(id);
  var link = document.querySelector('nav a[href="#' + id + '"]');
  if (page) page.classList.add('active');
  if (link) link.classList.add('active');
  else if (page) {{
    // fallback: first page/link if hash doesn't match anything
  }}
}}
function fromHash() {{
  var id = location.hash.replace('#', '') || '{FIRST_ID}';
  show(id);
}}
window.addEventListener('hashchange', fromHash);
fromHash();
</script>
</body>
</html>
"""


def build() -> None:
    global PATH_TO_PAGE_ID, CURRENT_DOC_DIR

    PATH_TO_PAGE_ID = {
        rel_path: slugify(f"{group}-{title}") for group, title, rel_path in MANIFEST
    }

    groups = {}
    pages_html = []
    first_id = None
    for group, title, rel_path in MANIFEST:
        src = REPO_ROOT / rel_path
        text = src.read_text(encoding="utf-8")
        page_id = slugify(f"{group}-{title}")
        if first_id is None:
            first_id = page_id
        groups.setdefault(group, []).append((page_id, title))
        CURRENT_DOC_DIR = Path(rel_path).parent
        body_html = markdown_to_html(text)
        pages_html.append(
            f'<article class="page" id="{page_id}">\n'
            f'<p style="color:var(--muted);font-size:12.5px;margin-top:-8px">Source: <code>{html.escape(rel_path)}</code></p>\n'
            f"{body_html}\n</article>"
        )

    nav_parts = []
    for group, items in groups.items():
        nav_parts.append('<div class="group">')
        nav_parts.append(f'<div class="group-title">{html.escape(group)}</div>')
        for page_id, title in items:
            nav_parts.append(f'<a href="#{page_id}">{html.escape(title)}</a>')
        nav_parts.append("</div>")

    page = PAGE_TEMPLATE.format(
        NAV_HTML="\n".join(nav_parts),
        PAGES_HTML="\n".join(pages_html),
        FIRST_ID=first_id,
    )
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(page)} bytes, {len(MANIFEST)} pages)")


if __name__ == "__main__":
    build()
