"""Convert between Canvas HTML and Markdown."""

import re
from typing import Optional
import html


def html_to_markdown(html_content: str) -> str:
    """Convert Canvas HTML to Markdown.

    This is a simple converter that handles common Canvas HTML patterns.
    For complex content, consider using markdownify library.

    NOTE: HTML tables are preserved as-is to maintain accessibility features
    (captions, scope attributes, thead/tbody structure) that cannot be
    expressed in markdown table syntax.
    """
    if not html_content:
        return ""

    text = html_content

    # Preserve HTML tables as-is (accessibility features can't be expressed in markdown)
    html_tables = []
    def save_html_table(m):
        html_tables.append(m.group(0))
        return f"__HTML_TABLE_{len(html_tables)-1}__"
    text = re.sub(r'<table[^>]*>.*?</table>', save_html_table, text, flags=re.DOTALL | re.IGNORECASE)

    # Decode HTML entities
    text = html.unescape(text)

    # Remove style and script tags completely
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Headers
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h5[^>]*>(.*?)</h5>', r'##### \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h6[^>]*>(.*?)</h6>', r'###### \1\n', text, flags=re.DOTALL | re.IGNORECASE)

    # Bold and italic
    text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)

    # Links
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.DOTALL | re.IGNORECASE)

    # Images
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/?>', r'![\2](\1)', text, flags=re.IGNORECASE)
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*/?>', r'![](\1)', text, flags=re.IGNORECASE)

    # Lists - handle nested lists by processing multiple times
    # Unordered lists
    text = re.sub(r'<ul[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</ul>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', text, flags=re.DOTALL | re.IGNORECASE)

    # Ordered lists (simplified - doesn't maintain numbering)
    text = re.sub(r'<ol[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</ol>', '\n', text, flags=re.IGNORECASE)

    # Blockquotes
    text = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', lambda m: '> ' + m.group(1).replace('\n', '\n> '), text, flags=re.DOTALL | re.IGNORECASE)

    # Code blocks
    text = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'```\n\1\n```', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.DOTALL | re.IGNORECASE)

    # Horizontal rules
    text = re.sub(r'<hr[^>]*/?>', '\n---\n', text, flags=re.IGNORECASE)

    # Paragraphs and line breaks
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<br[^>]*/?>', '\n', text, flags=re.IGNORECASE)

    # Divs and spans (just extract content)
    text = re.sub(r'<div[^>]*>(.*?)</div>', r'\1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', text, flags=re.DOTALL | re.IGNORECASE)

    # Note: Tables are preserved as HTML (extracted earlier) - no conversion needed

    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    text = text.strip()

    # Restore preserved HTML tables
    for i, table in enumerate(html_tables):
        text = text.replace(f"__HTML_TABLE_{i}__", f"\n\n{table}\n\n")

    # Final cleanup of any extra newlines from table restoration
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    return text


def markdown_to_html(markdown_content: str) -> str:
    """Convert Markdown to HTML for Canvas.

    This is a simple converter. For complex content, consider using
    the markdown library.

    NOTE: HTML tables are preserved as-is to maintain accessibility features
    (captions, scope attributes, thead/tbody structure).
    """
    if not markdown_content:
        return ""

    text = markdown_content

    # Preserve HTML tables as-is (extract before any processing)
    # Use a placeholder that looks like HTML so paragraph logic doesn't wrap it
    html_tables = []
    def save_html_table(m):
        html_tables.append(m.group(0))
        return f"<__HTML_TABLE_{len(html_tables)-1}__/>"
    text = re.sub(r'<table[^>]*>.*?</table>', save_html_table, text, flags=re.DOTALL | re.IGNORECASE)

    # Code blocks (do first to protect content)
    code_blocks = []
    def save_code_block(m):
        code_blocks.append(m.group(1))
        return f"__CODE_BLOCK_{len(code_blocks)-1}__"
    text = re.sub(r'```\n?(.*?)\n?```', save_code_block, text, flags=re.DOTALL)

    # Inline code
    inline_codes = []
    def save_inline_code(m):
        inline_codes.append(m.group(1))
        return f"__INLINE_CODE_{len(inline_codes)-1}__"
    text = re.sub(r'`([^`]+)`', save_inline_code, text)

    # Headers
    text = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', text, flags=re.MULTILINE)
    text = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', text, flags=re.MULTILINE)
    text = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)

    # Bold and italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    # Links and images
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" />', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    # Horizontal rules
    text = re.sub(r'^---+$', '<hr />', text, flags=re.MULTILINE)

    # Lists (simplified)
    lines = text.split('\n')
    in_ul = False
    in_ol = False
    result_lines = []

    for line in lines:
        stripped = line.strip()

        # Unordered list
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_ul:
                result_lines.append('<ul>')
                in_ul = True
            result_lines.append(f'<li>{stripped[2:]}</li>')
        # Ordered list
        elif re.match(r'^\d+\. ', stripped):
            if not in_ol:
                result_lines.append('<ol>')
                in_ol = True
            content = re.sub(r'^\d+\. ', '', stripped)
            result_lines.append(f'<li>{content}</li>')
        else:
            if in_ul:
                result_lines.append('</ul>')
                in_ul = False
            if in_ol:
                result_lines.append('</ol>')
                in_ol = False
            result_lines.append(line)

    if in_ul:
        result_lines.append('</ul>')
    if in_ol:
        result_lines.append('</ol>')

    text = '\n'.join(result_lines)

    # Blockquotes
    text = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)

    # Paragraphs - wrap non-tag lines
    lines = text.split('\n')
    result_lines = []
    para_buffer = []

    def flush_para():
        if para_buffer:
            content = ' '.join(para_buffer)
            result_lines.append(f'<p>{content}</p>')
            para_buffer.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_para()
        elif stripped.startswith('<') and not stripped.startswith('<a') and not stripped.startswith('<strong') and not stripped.startswith('<em') and not stripped.startswith('<img'):
            flush_para()
            result_lines.append(line)
        else:
            para_buffer.append(stripped)

    flush_para()
    text = '\n'.join(result_lines)

    # Restore code blocks
    for i, code in enumerate(code_blocks):
        escaped_code = html.escape(code)
        text = text.replace(f"__CODE_BLOCK_{i}__", f'<pre><code>{escaped_code}</code></pre>')

    # Restore inline code
    for i, code in enumerate(inline_codes):
        escaped_code = html.escape(code)
        text = text.replace(f"__INLINE_CODE_{i}__", f'<code>{escaped_code}</code>')

    # Restore HTML tables (preserved exactly as they were)
    for i, table in enumerate(html_tables):
        text = text.replace(f"<__HTML_TABLE_{i}__/>", table)

    return text
