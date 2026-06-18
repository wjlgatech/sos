"""Deterministic thumbnail + infographic generation with Pillow.

No external/AI image API: fully offline, reproducible, unit-testable.
Thumbnail  : 1200 x 627  (LinkedIn article cover ratio)
Infographic: 1080 x 1920 (portrait, story/share friendly)
"""
import os
import textwrap
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

# Brand palette (love12xfuture / OmegaFounders dark theme)
BG_DARK = (13, 17, 28)
BG_PANEL = (22, 28, 44)
ACCENT = (88, 166, 255)
ACCENT2 = (255, 184, 76)
TEXT = (237, 242, 250)
MUTED = (150, 162, 184)

# Cross-platform font candidates, tried in order. First hit wins.
# Linux (DejaVu) → macOS system fonts → Pillow's bundled DejaVuSans.
_PIL_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(ImageFont.__file__)), "fonts")
_FONT_CANDIDATES = {
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        os.path.join(_PIL_FONT_DIR, "DejaVuSans.ttf"),
    ],
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        os.path.join(_PIL_FONT_DIR, "DejaVuSans.ttf"),
    ],
}


def _font(bold: bool, size: int) -> ImageFont.ImageFont:
    for path in _FONT_CANDIDATES["bold" if bold else "regular"]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    # Last resort: Pillow's built-in bitmap font (size is ignored, but never fails).
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w) -> List[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _gradient(size: Tuple[int, int], top, bottom) -> Image.Image:
    w, h = size
    base = Image.new("RGB", size, top)
    top_l = Image.new("RGB", size, bottom)
    mask = Image.new("L", size)
    md = mask.load()
    for y in range(h):
        v = int(255 * (y / max(h - 1, 1)))
        for x in range(w):
            md[x, y] = v
    return Image.composite(top_l, base, mask)


def generate_thumbnail(title: str, subtitle: Optional[str], out_path: str,
                       eyebrow: str = "OMEGAFOUNDERS", size=(1200, 627)) -> str:
    W, H = size
    img = _gradient(size, BG_DARK, BG_PANEL)
    d = ImageDraw.Draw(img)
    # accent rail
    d.rectangle([0, 0, 14, H], fill=ACCENT)
    pad = 70
    # eyebrow
    ef = _font(True, 26)
    d.text((pad, 64), eyebrow.upper(), font=ef, fill=ACCENT)
    # title (auto-fit)
    for ts in (78, 70, 62, 54, 46):
        tf = _font(True, ts)
        lines = _wrap(d, title, tf, W - pad * 2)
        if len(lines) <= 4:
            break
    y = 150
    for ln in lines:
        d.text((pad, y), ln, font=tf, fill=TEXT)
        y += int(ts * 1.18)
    # subtitle
    if subtitle:
        sf = _font(False, 30)
        for ln in _wrap(d, subtitle, sf, W - pad * 2)[:2]:
            d.text((pad, y + 14), ln, font=sf, fill=MUTED)
            y += 40
    # footer
    d.text((pad, H - 56), "love12xfuture", font=_font(True, 26), fill=ACCENT2)
    img.save(out_path)
    return out_path


def generate_infographic(title: str, points: List[str], out_path: str,
                         eyebrow: str = "KEY TAKEAWAYS", size=(1080, 1920)) -> str:
    W, H = size
    img = _gradient(size, BG_DARK, BG_PANEL)
    d = ImageDraw.Draw(img)
    pad = 80
    d.text((pad, 110), eyebrow.upper(), font=_font(True, 34), fill=ACCENT)
    # title
    for ts in (76, 66, 58, 50):
        tf = _font(True, ts)
        tlines = _wrap(d, title, tf, W - pad * 2)
        if len(tlines) <= 4:
            break
    y = 180
    for ln in tlines:
        d.text((pad, y), ln, font=tf, fill=TEXT)
        y += int(ts * 1.16)
    y += 50
    # numbered point cards
    pf = _font(False, 40)
    nf = _font(True, 46)
    card_w = W - pad * 2
    for i, p in enumerate(points[:6], 1):
        plines = _wrap(d, p, pf, card_w - 150)
        card_h = 60 + len(plines) * 52
        d.rounded_rectangle([pad, y, pad + card_w, y + card_h], radius=22, fill=BG_PANEL)
        d.ellipse([pad + 24, y + 24, pad + 84, y + 84], fill=ACCENT)
        nw = d.textlength(str(i), font=nf)
        d.text((pad + 54 - nw / 2, y + 30), str(i), font=nf, fill=BG_DARK)
        ty = y + 28
        for ln in plines:
            d.text((pad + 120, ty), ln, font=pf, fill=TEXT)
            ty += 52
        y += card_h + 28
    d.text((pad, H - 90), "love12xfuture  \u2022  OmegaFounders",
           font=_font(True, 30), fill=ACCENT2)
    img.save(out_path)
    return out_path
