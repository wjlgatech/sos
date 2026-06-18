"""Parse a markdown article into structured pieces for images + metadata."""
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Article:
    title: str
    subtitle: Optional[str]
    sections: List[str] = field(default_factory=list)      # ## headings
    key_points: List[str] = field(default_factory=list)    # best bullets/takeaways
    raw: str = ""

    @property
    def slug(self) -> str:
        s = re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")
        return s[:60]


def _first_h1(md: str) -> str:
    m = re.search(r"^#\s+(.+?)\s*$", md, flags=re.MULTILINE)
    return m.group(1).strip() if m else "Untitled"


def _subtitle(md: str) -> Optional[str]:
    """The dek: first real content line right after the H1.

    Handles italic *..*, bold **..**, or plain text. We do NOT scan for the
    first bold line anywhere, which used to grab a bold phrase deep in the body.
    """
    body = re.sub(r"\A\s*#\s+.*?(\n|$)", "", md, count=1)
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or re.match(r"^[-*_]{3,}$", line):
            continue
        return re.sub(r"[*`]", "", line).strip()[:140]
    return None


def _sections(md: str) -> List[str]:
    heads = re.findall(r"^##\s+(.+?)\s*$", md, flags=re.MULTILINE)
    return [re.sub(r"[*`]", "", h).strip() for h in heads]


_CODEISH = re.compile(r"^(name|uses|run|with|on|jobs|steps|if|env):"  # yaml keys
                      r"|[{}();]|=|\bdef\b|\bclass\b|\bimport\b|^\s*[-#]\s*\w+:",
                      re.IGNORECASE)


def _looks_like_code(txt: str) -> bool:
    return bool(_CODEISH.search(txt)) or txt.count("`") >= 2


def _key_points(md: str, limit: int = 5) -> List[str]:
    """Prefer a Takeaways/Key section's bullets; else clean prose bullets; else
    section headings. Fenced code is stripped first so YAML/config never leaks in."""
    # Strip fenced code blocks before scanning (the day10 'name: Run Claude' bug).
    md_nocode = re.sub(r"```.*?```", "", md, flags=re.DOTALL)
    points: List[str] = []
    lines = md_nocode.splitlines()
    scope = md_nocode
    kw = re.compile(r"^##\s+.*(takeaway|key|lesson|recap|summary)", re.IGNORECASE)
    for i, ln in enumerate(lines):
        if kw.match(ln):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## "):
                j += 1
            scope = "\n".join(lines[i + 1:j])
            break
    for m in re.finditer(r"^\s*[-*+]\s+(.+?)\s*$", scope, flags=re.MULTILINE):
        txt = re.sub(r"[*`#]", "", m.group(1)).strip()
        if 8 <= len(txt) <= 120 and not _looks_like_code(txt):
            points.append(txt)
        if len(points) >= limit:
            break
    if not points:  # fall back to section headings — always clean prose
        points = _sections(md)[:limit]
    return points


def parse_article(md: str) -> Article:
    return Article(
        title=_first_h1(md),
        subtitle=_subtitle(md),
        sections=_sections(md),
        key_points=_key_points(md),
        raw=md,
    )
