---
name: animate-anything
description: Turn any concept into a 3Blue1Brown-style animated explainer — a real ManimCommunity scene, authored in Grant Sanderson's reverse-engineered style, style-gated (0–100), and rendered to MP4 locally. Use when the user wants to "animate/explain <concept>", "make a 3blue1brown / manim video", "visualize this math", or "turn this idea into an animation". Triggers on 'animate', '3blue1brown', '3b1b', 'manim', 'explainer video', 'visualize <concept>'. NOT for generative/photoreal video (use a video model) or a UI micro-interaction (use CSS/Motion). Bundled engine: this skill's `scripts/animate.py` + `examples/`.
---

# /animate-anything — a concept → a 3Blue1Brown-style explainer

Point it at an idea; get back a **real Manim scene** authored in Grant Sanderson's style, checked
against a reverse-engineered **style contract**, and rendered to an MP4 — all locally, no cloud video
API. The engine and golden examples travel **with this skill** (`scripts/animate.py`, `examples/`);
the full ranked animation catalog + a Docker/CI render path live in the home repo:
**github.com/wjlgatech/animate-anything**.

## The principle: emit the composition, render locally

The tool authors a self-contained ManimCommunity scene (Python) + a style verdict; rendering to MP4
is a local step (`manim -qh scene.py Name`) — deterministic, free, no paid video model. Target is
**ManimCommunity** (`pip install manim`, `from manim import *`), *not* Grant's ManimGL
(`from manimlib import *`): Community is pip-installable under the plain name, fully documented at
docs.manim.community, and reliably LLM-authorable. Study `github.com/3b1b/videos` as a **style corpus
only** — it's not a dependency.

## The loop (scaffold → author → lint → render)

Run the bundled engine from this skill's directory (paths are relative to this `SKILL.md`):

```bash
# 0) once: the render toolchain (checked, never bundled) — a venv avoids PEP-668 blocks
python3 -m venv ~/.manim-venv && ~/.manim-venv/bin/pip install manim   # + ffmpeg ; + LaTeX only for MathTex
#   or zero-install rendering via Docker: see the home repo's Dockerfile (manim+LaTeX+ffmpeg baked in)

# 1) SCAFFOLD — concept → a 3b1b-style skeleton with the 5-beat arc
python3 scripts/animate.py scaffold "eigenvectors" --out scene.py

# 2) AUTHOR — fill the beats, obeying the style contract below (this is where you, the agent, work)

# 3) LINT — a computed 0–100 style score; gate it (exit 1 below the bar)
python3 scripts/animate.py lint scene.py --gate 80

# 4) RENDER — locally
~/.manim-venv/bin/manim -pql scene.py EigenvectorsScene    # draft (854×480, fast)
~/.manim-venv/bin/manim -qh  scene.py EigenvectorsScene    # final (1080p60)
```

`python3 scripts/animate.py contract` prints the full contract. Golden references (both lint 100/100):
`examples/odd_squares.py` (renders without LaTeX) and `examples/geometric_series.py` (MathTex, needs LaTeX).

## The 3Blue1Brown style contract (reverse-engineered, lint-checked)

Grounded in Grant's `manimlib/default_config.yml` (colors), `constants.py` (`COLORMAP_3B1B`), and real
scene code in `3b1b/videos` (e.g. `_2024/transformers/attention.py`). The linter checks each item.

- **Warm-grey canvas — the #1 tell.** `config.background_color = "#333333"`. **Never pure black** (reads
  as "not 3b1b") or white.
- **Palette by role, not garnish.** The 3b1b constants — blues `BLUE_A #C7E9F1 · BLUE_B #9CDCEB ·
  BLUE_C/BLUE #58C4DD · BLUE_D #29ABCA · BLUE_E #1C758A`, plus `YELLOW GOLD GREEN RED MAROON TEAL
  GREY_BROWN`. Role (`COLORMAP_3B1B = [BLUE_E, GREEN, YELLOW, RED]`): **blue/grey = given · YELLOW =
  focus · RED = tension · GREEN/GOLD = resolved.** Highlights = thin stroke (2–3) + faint fill (≤0.25).
- **Introduce gently.** `Write` (text), `Create` (shapes), `FadeIn(shift=…)` (groups); many items via
  `LaggedStart(..., lag_ratio≈0.25)` — a cascade, never a mass appearance.
- **Morph to show equivalence — the load-bearing move.** When two forms are the same, `Transform` /
  `ReplacementTransform` / `TransformMatchingTex` **one into the other** — **never `FadeOut(a)` then
  `FadeIn(b)`** (the AI-slop tell the linter flags). Give the key morph `run_time ≥ 1.5`.
- **Pacing: play → wait → play → wait.** A `self.wait()` after every meaningful change; `self.wait(2)`
  after the reveal. Unhurried because nothing new appears during a wait and only one thing moves per play.
- **One idea per beat; generous negative space.** No decorative spins/bounces — every motion relates two things.
- **Narrative arc.** Open on a **concrete instance** (never "let X be…") → build intuition → **morph**
  into the formal symbols → the "aha" collapse.

## Honest edges

- **MathTex needs LaTeX.** `Text(...)` (Pango) renders without it; swap `MathTex → Text` if no LaTeX,
  or render via the home repo's Docker image (LaTeX baked in).
- **Community ≠ Grant's exact renders.** Community reproduces his *style* faithfully; bit-identical
  output needs ManimGL. For an agent, Community wins.
- **The linter is a heuristic gate**, not a taste oracle — it catches the encodable tells (canvas,
  morph, pacing, palette, arc). *What* to animate is still your judgment.
- **Not a video model.** This produces a hand-crafted vector explainer, not generative footage.
