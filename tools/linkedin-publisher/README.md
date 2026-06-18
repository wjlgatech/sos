# linkedin-publisher

Turn a markdown article into a complete LinkedIn long-form publishing bundle:

- **Cleaned body** — collapses markdown's `\n\n` to single newlines (LinkedIn's Tiptap editor renders every `\n` as a paragraph, so raw markdown produces an empty gap between every sentence), strips `#`/`**`/`*`/`` ` `` syntax, keeps `#hashtags`.
- **Thumbnail** — 1200×627 cover image, auto-fit title + subtitle, brand palette.
- **Infographic** — 1080×1920 portrait with numbered key-point cards.
- **Publish bundle** — a browser-console script that sets the title, pastes the body via a `DataTransfer` paste event, and injects each fenced code block as a real ProseMirror `codeBlock` node (one dark `<pre>`, not one box per line).

## Why a console script and not an API

LinkedIn's public API **cannot create long-form articles** — only share posts. So the final publish step is browser-assisted by design: you open the article editor and run the generated `publish_bundle.js` in DevTools. Everything upstream (cleaning, images, code-block prep) is fully automated and unit-tested.

## Install

```bash
pip install -r requirements.txt   # just Pillow
# or:  pip install -e .            # installs the `linkedin-publish` command
```

## Usage

```bash
python -m linkedin_publisher.cli build path/to/article.md --out out_dir
# or, if installed:
linkedin-publish build article.md --out out_dir --eyebrow OMEGAFOUNDERS
```

Produces in `out_dir/`:

| File | Purpose |
|------|---------|
| `thumbnail.png` | upload as the article cover (native file dialog) |
| `infographic.png` | embed in the body or share as a portrait card |
| `linkedin_body.txt` | spacing-cleaned body for reference |
| `publish_bundle.js` | paste into the editor's DevTools console |
| `INSTRUCTIONS.md` | the 5-step publish checklist |

## Publish steps

1. LinkedIn → **Write article**.
2. Upload `thumbnail.png` as the cover.
3. DevTools console → paste `publish_bundle.js` → Enter.
4. **Mandatory gate:** scroll the article; every code block must render on a dark background. If any code shows as plain text, stop and re-run.
5. Embed `infographic.png`, then **Publish**.

## Library API

```python
from linkedin_publisher import (parse_article, to_linkedin_text,
                                generate_thumbnail, generate_infographic,
                                build_publish_bundle)

md = open("article.md").read()
art = parse_article(md)                      # title, subtitle, sections, key_points
body, code_blocks = to_linkedin_text(md)     # spacing-fixed body + extracted code
generate_thumbnail(art.title, art.subtitle, "thumb.png")
generate_infographic(art.title, art.key_points, "info.png")
js = build_publish_bundle(art.title, body, code_blocks)
```

## Tests

```bash
python -m pytest tests/ -q     # 14 tests: preprocess, extract, images, publish
```

## Design notes / known limits

- The Tiptap injection mirrors fixes hardened over real publishing failures (paragraph-spacing bug, one-box-per-code-line bug). LinkedIn editor internals can change; if injection drifts, the script falls back to plain paste.
- Key-point extraction strips fenced code first so YAML/config never leaks into the infographic; with no "Key Takeaways" section it falls back to section headings.
- Image generation is fully offline (Pillow + DejaVu fonts) — no AI/image API, so output is deterministic and testable.

Part of the **love12xfuture / OmegaFounders** content stack.
