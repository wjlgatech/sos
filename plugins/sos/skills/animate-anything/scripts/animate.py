#!/usr/bin/env python3
"""animate.py — the /animate-anything engine: scaffold a 3Blue1Brown-style Manim scene,
lint it against a reverse-engineered style contract, and render it locally.

Design (same principle as the rest of anyagent's ecosystem): **emit the composition, not the
render.** This tool authors a self-contained ManimCommunity scene (Python) and a style verdict;
rendering to MP4 is a local step (`manim -qh scene.py Name`) — no cloud video API, deterministic,
free. Target is ManimCommunity (`pip install manim`, `from manim import *`), NOT Grant's ManimGL
(`from manimlib import *`) — Community is pip-installable under the plain name, fully documented, and
reliably LLM-authorable. Study `github.com/3b1b/videos` as a style corpus only.

Usage:
  animate.py scaffold "<concept>" [--out scene.py] [--name SceneClass]   # concept → scene skeleton
  animate.py lint <scene.py>                                             # 0–100 style score (gate with --gate)
  animate.py contract                                                    # print the 3b1b style contract
Zero third-party deps (stdlib). Rendering needs `manim` + ffmpeg (+ LaTeX for MathTex) — checked, not bundled.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ── The reverse-engineered 3b1b palette (verbatim hex from Grant's manimlib default_config.yml,
#    all present as ManimCommunity named constants). Color encodes ROLE, never garnish. ──
PALETTE = {
    "BLUE_A": "#C7E9F1", "BLUE_B": "#9CDCEB", "BLUE_C": "#58C4DD",  # the 3Blue1Brown blues
    "BLUE_D": "#29ABCA", "BLUE_E": "#1C758A",
    "YELLOW": "#FFFF00", "GOLD": "#F0AC5F", "GREEN": "#83C167",
    "RED": "#FC6255", "MAROON": "#C55F73", "TEAL": "#5CD0B3",
    "GREY_BROWN": "#736357", "WHITE": "#FFFFFF",
}
# The single most identifying trait: a dark WARM-GREY canvas — NOT pure black. Pure black reads
# as "not 3b1b". Grant's manimlib config sets background_color: "#333333".
BACKGROUND = "#333333"
# Accent order + role convention, verbatim from manimlib: COLORMAP_3B1B = [BLUE_E, GREEN, YELLOW, RED].
ROLE = "neutral/given → blue·grey · focus → YELLOW · tension/error → RED · resolved/correct → GREEN"

# ── The STYLE CONTRACT: encodable rules a 3b1b-feeling animation obeys (each is lint-checkable) ──
CONTRACT = [
    ("community-target", "Author against ManimCommunity: `from manim import *` (never `manimlib`)."),
    ("scene-construct", "A `class X(Scene)` with a `def construct(self)` entry point."),
    ("warm-grey-canvas", "background_color = '#333333' — a dark WARM-GREY, never pure black or white. This is the #1 3b1b tell."),
    ("palette-by-role", "Colors from the 3b1b palette AND by role: blue/grey=given · YELLOW=focus · RED=tension · GREEN=resolved."),
    ("introduce-gently", "Introduce with Write (text) / Create (shapes) / FadeIn(shift=…); many items via LaggedStart (lag_ratio≈0.25) — never all at once."),
    ("morph-to-equivalence", "THE load-bearing move: when two forms are equivalent, Transform/ReplacementTransform one INTO the other — NEVER FadeOut(a)→FadeIn(b)."),
    ("pacing", "play → wait → play → wait. A self.wait() after every meaningful change; run_time≥1.5 on the key morph so the eye tracks it."),
    ("one-idea", "One idea on screen per beat; generous negative space (frame mostly empty)."),
    ("meaningful-motion", "Every motion carries meaning (relates two things). No decorative spins/bounces/pulses."),
    ("narrative-arc", "Concrete instance (never start abstract) → build visual intuition → formalize via a morph → the 'aha' collapse."),
]

_SCAFFOLD = '''\
from manim import *

# /animate-anything — 3Blue1Brown-style explainer (ManimCommunity).
# Concept: {concept}
# Render:  manim -pql {stem}.py {name}   (draft)  ·  manim -qh {stem}.py {name}   (final)
config.background_color = "#333333"   # the 3b1b warm-grey canvas — NOT pure black (the #1 tell)

# Palette by ROLE: blue/grey = given · YELLOW = focus · RED = tension · GREEN = resolved.
# The arc: concrete → intuition → morph-to-formalize → aha. One idea per beat; let it breathe.

class {name}(Scene):
    def construct(self):
        # ── 1. HOOK — name the concept, then show a CONCRETE instance (never abstract) ──
        title = Text("{concept}", color=BLUE_C).to_edge(UP)
        self.play(Write(title))
        self.wait()

        # ── 2. CONCRETE — the smallest real example (given → blue) ─────────────
        obj = Circle(color=BLUE_D).set_fill(BLUE_D, opacity=0.4)
        self.play(Create(obj))
        self.wait()

        # ── 3. BUILD INTUITION — label/move so structure appears (faint highlight) ──
        box = SurroundingRectangle(obj, color=GREY_BROWN).set_stroke(width=2).set_fill(GREY_BROWN, opacity=0.2)
        self.play(FadeIn(box, shift=UP * 0.2))
        self.wait()

        # ── 4. FORMALIZE — morph the picture INTO the math (shows equivalence) ──
        #   Swap MathTex(...) → Text("f(x)") if LaTeX isn't installed. run_time lets the eye track it.
        formula = MathTex(r"f(x)", color=YELLOW).scale(1.4).move_to(obj)
        self.play(ReplacementTransform(VGroup(obj, box), formula), run_time=1.6)
        self.wait()

        # ── 5. REVEAL — the 'aha': land the one idea (resolved → gold/green) ────
        self.play(Indicate(formula, color=GOLD))
        self.wait(2)
'''


def slugify(text: str) -> str:
    words = [w.capitalize() for w in re.findall(r"[A-Za-z0-9]+", text)][:4]
    return ("".join(words) or "Explainer") + "Scene"


def cmd_scaffold(args) -> int:
    name = args.name or slugify(args.concept)
    stem = Path(args.out).stem if args.out else "scene"
    code = _SCAFFOLD.format(concept=args.concept.replace('"', "'"), name=name, stem=stem)
    if args.out:
        Path(args.out).write_text(code, encoding="utf-8")
        print(f"✓ scaffolded {args.out} (class {name}) — fill the 5 beats, then: manim -pql {args.out} {name}")
    else:
        sys.stdout.write(code)
    return 0


def _lint(src: str) -> tuple[int, list[tuple[str, bool, str]]]:
    """Score a scene 0–100 against the style contract. Returns (score, [(id, passed, note)])."""
    checks: list[tuple[str, bool, str]] = []

    def add(cid, ok, note):
        checks.append((cid, ok, note))

    add("community-target", "from manim import *" in src and "manimlib" not in src,
        "imports `from manim import *` (Community), not manimlib")
    add("scene-construct", bool(re.search(r"class\s+\w+\s*\(\s*Scene\s*\)", src)) and "def construct" in src,
        "a Scene subclass with construct()")
    # the #1 3b1b tell: warm-grey #333333, NOT pure black (#000) or white
    has_grey = bool(re.search(r"background_color\s*=\s*['\"]#3{2}3{2}3{2}['\"]", src, re.I)) \
        or bool(re.search(r"background_color\s*=\s*['\"]#333['\"]", src))
    bad_bg = bool(re.search(r"background_color\s*=\s*(WHITE|['\"]#?(000000|000|1C1C1C|FFFFFF|FFF)['\"])", src, re.I))
    add("warm-grey-canvas", has_grey and not bad_bg,
        "background_color = '#333333' (warm grey — the signature; not black/white)")
    add("palette-by-role", any(c in src for c in PALETTE) or bool(re.search(r"#(29ABCA|58C4DD|1C758A|736357)", src, re.I)),
        "uses the 3b1b palette constants")
    add("introduce-gently", bool(re.search(r"\b(Write|Create|FadeIn|GrowArrow|GrowFromCenter|LaggedStart)\b", src)),
        "introduces objects with a gentle enter (Write/Create/FadeIn/LaggedStart)")
    has_morph = bool(re.search(r"\b(ReplacementTransform|TransformMatchingTex|Transform)\b", src))
    add("morph-to-equivalence", has_morph,
        "uses a Transform to show equivalence — the load-bearing 3b1b move")
    # anti-slop: adjacent FadeOut→FadeIn of text/tex is a MISSED morph (should be a Transform)
    missed = bool(re.search(r"FadeOut\([^)]*(Tex|formula|eq)[^)]*\)[\s\S]{0,120}?FadeIn\([^)]*(Tex|formula|eq)", src, re.I))
    add("no-missed-morph", not missed,
        "no FadeOut→FadeIn of equations (that's a morph in disguise — use Transform)")
    waits = len(re.findall(r"self\.wait\(", src))
    add("pacing", waits >= 2, f"{waits} self.wait() beat(s) — play→wait→play→wait (need ≥2)")
    busy = [p for p in re.findall(r"self\.play\(([^)]*)\)", src) if p.count(",") >= 4]
    add("one-idea", not busy, "no single play() dumps many objects at once (negative space)")
    add("narrative-arc", src.count("self.play(") >= 3,
        f"{src.count('self.play(')} play beats — a real arc, not a one-shot")
    passed = sum(1 for _, ok, _ in checks if ok)
    score = round(passed / len(checks) * 100)
    return score, checks


def cmd_lint(args) -> int:
    src = Path(args.scene).read_text(encoding="utf-8")
    score, checks = _lint(src)
    print(f"3b1b style score: {score}/100  ({sum(ok for _,ok,_ in checks)}/{len(checks)} checks)")
    for cid, ok, note in checks:
        print(f"  {'✅' if ok else '❌'} {cid:<20} {note}")
    if not any(ok for cid, ok, _ in checks if cid == "morph-to-equivalence"):
        print("  → tip: add a ReplacementTransform to morph one form into another — it's the heart of the 3b1b style.")
    if args.gate and score < args.gate:
        print(f"\n  gate {args.gate}: FAILS ❌ ({score}/100)", file=sys.stderr)
        return 1
    return 0


def cmd_contract(args) -> int:
    print("The 3Blue1Brown style contract (reverse-engineered):\n")
    for cid, rule in CONTRACT:
        print(f"  • [{cid}] {rule}")
    print(f"\n  Palette: {', '.join(f'{k} {v}' for k, v in PALETTE.items())}")
    print(f"  Canvas:  {BACKGROUND} (dark — the manim default)")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="animate.py", description="/animate-anything — 3b1b-style Manim, authored & graded.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scaffold", help="Concept → a 3b1b-style scene skeleton.")
    s.add_argument("concept")
    s.add_argument("--out")
    s.add_argument("--name")
    s.set_defaults(func=cmd_scaffold)
    lt = sub.add_parser("lint", help="Score a scene against the 3b1b style contract.")
    lt.add_argument("scene")
    lt.add_argument("--gate", type=int, default=0, help="Exit non-zero if score < this.")
    lt.set_defaults(func=cmd_lint)
    c = sub.add_parser("contract", help="Print the reverse-engineered style contract.")
    c.set_defaults(func=cmd_contract)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
