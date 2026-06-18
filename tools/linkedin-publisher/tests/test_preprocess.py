import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from linkedin_publisher.preprocess import (strip_markdown, extract_code_blocks,
                                           to_linkedin_text, CODE_MARKER)


def test_collapses_double_newlines():
    out = strip_markdown("Line one.\n\nLine two.\n\nLine three.")
    assert "\n\n" not in out
    assert out == "Line one.\nLine two.\nLine three."


def test_strips_headers_bold_italic_hr():
    md = "## Heading\n**bold** and *italic*\n---\ntext"
    out = strip_markdown(md)
    assert "##" not in out and "**" not in out and "---" not in out
    assert "bold" in out and "italic" in out


def test_keeps_hashtags():
    out = strip_markdown("Follow #love12xfuture today")
    assert "#love12xfuture" in out


def test_extracts_code_blocks_with_markers():
    md = "intro\n```python\nprint(1)\nprint(2)\n```\nouttro"
    text, blocks = extract_code_blocks(md)
    assert len(blocks) == 1
    assert blocks[0] == "print(1)\nprint(2)"
    assert CODE_MARKER.format(0) in text
    assert "```" not in text


def test_to_linkedin_drops_title_and_returns_blocks():
    md = "# My Title\n\nbody para\n\n```js\nx=1\n```\n"
    text, blocks = to_linkedin_text(md)
    assert "My Title" not in text
    assert blocks == ["x=1"]


def test_multiple_code_blocks_ordered():
    md = "a\n```\nfirst\n```\nb\n```\nsecond\n```\nc"
    text, blocks = extract_code_blocks(md)
    assert blocks == ["first", "second"]
    assert text.index(CODE_MARKER.format(0)) < text.index(CODE_MARKER.format(1))
