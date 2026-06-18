"""Markdown -> LinkedIn-editor-ready text.

Mirrors the hard-won fixes from LINKEDIN_ARTICLE_POSTING_GUIDE.md:
  - LinkedIn's Tiptap editor treats every \n as a paragraph block, so markdown
    \n\n produces a visible empty gap between every sentence. Collapse to single.
  - Strip markdown syntax (LinkedIn has its own bold/italic buttons).
  - Code blocks must NOT be pasted as plain text; they are extracted and injected
    separately via the ProseMirror codeBlock node. We replace them with markers.
"""
import re
from typing import List, Tuple

CODE_MARKER = "\u2063CODEBLOCK_{}\u2063"  # invisible separator, unlikely to collide


def extract_code_blocks(md: str) -> Tuple[str, List[str]]:
    """Pull fenced ``` code blocks out, leaving an ordered placeholder marker.

    Returns (text_with_markers, [code_block_contents]).
    """
    blocks: List[str] = []

    def _replace(match: re.Match) -> str:
        # group 2 is the inner content (group 1 is optional language hint)
        code = match.group(2)
        code = code.rstrip("\n")
        idx = len(blocks)
        blocks.append(code)
        return CODE_MARKER.format(idx)

    fence = re.compile(r"```([^\n]*)\n(.*?)```", re.DOTALL)
    text = fence.sub(_replace, md)
    return text, blocks


def strip_markdown(text: str) -> str:
    """Strip markdown syntax + collapse blank lines for LinkedIn's editor.

    Order matters. Headers need the space after # so we don't eat #hashtags.
    """
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)  # hr lines
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)          # headers
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)                        # bold
    text = re.sub(r"\*([^*\n]+?)\*", r"\1", text)                       # italic
    text = re.sub(r"`([^`]*)`", r"\1", text)                            # inline code
    text = re.sub(r"^\s*[-*+]\s+", "\u2022 ", text, flags=re.MULTILINE) # bullets
    text = re.sub(r"\n{3,}", "\n\n", text)                              # 3+ -> 2
    text = re.sub(r"\n\n", "\n", text)                                  # 2 -> 1
    return text.strip()


def to_linkedin_text(md: str, drop_title: bool = True) -> Tuple[str, List[str]]:
    """Full pipeline. Returns (paste_text, code_blocks).

    paste_text keeps invisible code markers so publish.py can position the
    code blocks. drop_title removes the leading H1 (LinkedIn has a title field).
    """
    if drop_title:
        md = re.sub(r"\A\s*#\s+.*?(\n|$)", "", md, count=1)
    text, blocks = extract_code_blocks(md)
    text = strip_markdown(text)
    return text, blocks
