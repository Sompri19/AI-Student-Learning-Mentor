"""
Safe Markdown renderer for AI Mentor explanations.
AI Student Learning Mentor.

External language models answer in GitHub-flavoured Markdown (headings, bold text,
lists, tables, fenced code blocks). Rendering that text as-is shows the raw syntax to
students, so this module converts it into styled HTML.

Security model
--------------
Rendering happens in two strict steps:

1. The whole answer is HTML-escaped with `html.escape` (quotes included), so any markup
   produced by the model - including ``<script>`` - is neutralised before conversion.
2. Only a curated Markdown subset is then converted into a known-safe set of tags.

Because escaping happens first, raw HTML from the model can never reach the browser:
it is always displayed as literal text. Link targets are additionally restricted to
http/https/mailto schemes, so `javascript:` and data URIs are never emitted as hrefs.
"""
import html
import re
from typing import List, Tuple

from markupsafe import Markup

# Inline code spans are stashed here while the rest of the line is formatted.
_CODE_PLACEHOLDER = "\x00{}\x00"

_SAFE_URL_SCHEMES = re.compile(r"^(https?:|mailto:)", re.IGNORECASE)
_FENCED_CODE = re.compile(r"^```([\w+#.-]*)\s*$")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_HORIZONTAL_RULE = re.compile(r"^(\*{3,}|-{3,}|_{3,})$")
_LIST_ITEM = re.compile(r"^([-*+]|\d+\.)\s+(.*)$")
_TABLE_DIVIDER = re.compile(r"^\|[\s:|-]+\|$")
_INLINE_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC_STAR = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_ITALIC_UNDERSCORE = re.compile(r"(?<!\w)_([^_\n]+)_(?!\w)")


def _format_inline(text: str) -> str:
    """Applies inline Markdown (code, links, bold, italic) to already-escaped text."""
    code_spans: List[str] = []

    def _stash_code(match: "re.Match[str]") -> str:
        code_spans.append(match.group(1))
        return _CODE_PLACEHOLDER.format(len(code_spans) - 1)

    text = _INLINE_CODE.sub(_stash_code, text)

    def _render_link(match: "re.Match[str]") -> str:
        label, url = match.group(1), match.group(2).strip()
        if not _SAFE_URL_SCHEMES.match(url):
            # Never emit an unsafe or relative scheme as a link target.
            return label
        return (
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>'
        )

    text = _LINK.sub(_render_link, text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC_STAR.sub(r"<em>\1</em>", text)
    text = _ITALIC_UNDERSCORE.sub(r"<em>\1</em>", text)

    for index, code in enumerate(code_spans):
        text = text.replace(_CODE_PLACEHOLDER.format(index), f"<code>{code}</code>")

    return text


def _split_row(line: str) -> List[str]:
    """Splits a Markdown table row into its cells."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _render_table(rows: List[str]) -> str:
    """Renders a Markdown table (header row + alignment divider + body rows)."""
    header = _split_row(rows[0])
    body = [_split_row(row) for row in rows[2:]]

    parts = ['<div class="ai-table-scroll"><table><thead><tr>']
    parts.extend(f"<th>{_format_inline(cell)}</th>" for cell in header)
    parts.append("</tr></thead><tbody>")
    for body_row in body:
        parts.append(
            "<tr>" + "".join(f"<td>{_format_inline(cell)}</td>" for cell in body_row) + "</tr>"
        )
    parts.append("</tbody></table></div>")
    return "".join(parts)


def _render_list(lines: List[str], start: int) -> Tuple[str, int]:
    """Renders a (possibly nested) bullet or numbered list starting at `start`."""
    ordered = bool(re.match(r"^\d+\.\s+", lines[start].strip()))
    base_indent = len(lines[start]) - len(lines[start].lstrip())
    items: List[str] = []
    index = start
    total = len(lines)

    while index < total:
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            if index < total and not _LIST_ITEM.match(lines[index].strip()):
                break
            continue

        match = _LIST_ITEM.match(stripped)
        if not match:
            break

        indent = len(line) - len(line.lstrip())
        if indent > base_indent:
            nested, index = _render_list(lines, index)
            if items:
                items[-1] = items[-1] + nested
            else:
                items.append(nested)
            continue
        if indent < base_indent:
            break

        items.append(_format_inline(match.group(2).strip()))
        index += 1

    tag = "ol" if ordered else "ul"
    rendered = f"<{tag}>" + "".join(f"<li>{item}</li>" for item in items) + f"</{tag}>"
    return rendered, index


def _starts_new_block(stripped: str, following: str) -> bool:
    """True when `stripped` cannot continue the paragraph that precedes it."""
    if not stripped:
        return True
    if stripped.startswith(("|", "&gt;")):
        return True
    if _FENCED_CODE.match(stripped) or _HEADING.match(stripped) or _LIST_ITEM.match(stripped):
        return True
    if _HORIZONTAL_RULE.match(stripped):
        return True
    return bool(following and _TABLE_DIVIDER.match(following) and stripped.startswith("|"))


def _render_blocks(lines: List[str]) -> str:
    """Converts escaped Markdown lines into a sequence of safe HTML blocks."""
    blocks: List[str] = []
    index = 0
    total = len(lines)

    while index < total:
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        # Fenced code block
        fence = _FENCED_CODE.match(stripped)
        if fence:
            language = fence.group(1)
            index += 1
            buffer: List[str] = []
            while index < total and not lines[index].strip().startswith("```"):
                buffer.append(lines[index])
                index += 1
            index += 1  # consume the closing fence
            class_attr = f' class="language-{language}"' if language else ""
            body = html.escape("\n".join(buffer))
            blocks.append(f"<pre><code{class_attr}>{body}</code></pre>")
            continue

        # Horizontal rule
        if _HORIZONTAL_RULE.match(stripped):
            blocks.append("<hr>")
            index += 1
            continue

        # Heading
        heading = _HEADING.match(stripped)
        if heading:
            level = len(heading.group(1))
            blocks.append(
                f"<h{level}>{_format_inline(heading.group(2).strip())}</h{level}>"
            )
            index += 1
            continue

        # Table (header row followed by an alignment divider)
        following = lines[index + 1].strip() if index + 1 < total else ""
        if stripped.startswith("|") and _TABLE_DIVIDER.match(following):
            table_rows: List[str] = []
            while index < total and lines[index].strip().startswith("|"):
                table_rows.append(lines[index].strip())
                index += 1
            blocks.append(_render_table(table_rows))
            continue

        # Blockquote (">" is HTML-escaped to "&gt;")
        if stripped.startswith("&gt;"):
            quoted: List[str] = []
            while index < total and lines[index].strip().startswith("&gt;"):
                quoted.append(re.sub(r"^&gt;\s?", "", lines[index].strip()))
                index += 1
            blocks.append(
                "<blockquote>"
                + " ".join(_format_inline(part) for part in quoted)
                + "</blockquote>"
            )
            continue

        # List
        if _LIST_ITEM.match(stripped):
            rendered_list, index = _render_list(lines, index)
            blocks.append(rendered_list)
            continue

        # Paragraph
        buffer = []
        while index < total:
            current = lines[index].strip()
            nxt = lines[index + 1].strip() if index + 1 < total else ""
            if _starts_new_block(current, nxt):
                break
            buffer.append(current)
            index += 1
        blocks.append("<p>" + "<br>".join(_format_inline(part) for part in buffer) + "</p>")

    return "\n".join(blocks)


def render_markdown(text) -> Markup:
    """
    Renders model-generated Markdown into safe HTML.

    The answer is escaped *before* conversion, so any HTML it contains is shown as
    literal text rather than interpreted. Returns a `Markup` object that is safe to
    drop into a Jinja template with the `|safe`-equivalent `markdown` filter.

    Args:
        text: Raw Markdown answer (any type; falsy values render as an empty string).

    Returns:
        Markup: Sanitised HTML fragment.
    """
    if not text:
        return Markup("")

    escaped = html.escape(str(text))
    normalised = escaped.replace("\r\n", "\n").replace("\r", "\n")
    return Markup(_render_blocks(normalised.split("\n")))
