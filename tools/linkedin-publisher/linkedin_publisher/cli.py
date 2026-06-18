"""CLI: turn a markdown article into a full LinkedIn publishing bundle."""
import argparse
import os
import sys

from . import (parse_article, to_linkedin_text, generate_thumbnail,
               generate_infographic, build_publish_bundle, __version__)


def build(args) -> int:
    with open(args.article, encoding="utf-8") as f:
        md = f.read()

    art = parse_article(md)
    paste_text, code_blocks = to_linkedin_text(md)
    out = args.out or art.slug
    os.makedirs(out, exist_ok=True)

    cleaned_path = os.path.join(out, "linkedin_body.txt")
    with open(cleaned_path, "w", encoding="utf-8") as f:
        f.write(paste_text)

    thumb = generate_thumbnail(art.title, art.subtitle,
                               os.path.join(out, "thumbnail.png"),
                               eyebrow=args.eyebrow)
    points = art.key_points or art.sections
    info = generate_infographic(art.title, points,
                                os.path.join(out, "infographic.png"))

    bundle = build_publish_bundle(art.title, paste_text, code_blocks)
    bundle_path = os.path.join(out, "publish_bundle.js")
    with open(bundle_path, "w", encoding="utf-8") as f:
        f.write(bundle)

    instr = os.path.join(out, "INSTRUCTIONS.md")
    with open(instr, "w", encoding="utf-8") as f:
        f.write(_INSTRUCTIONS.format(title=art.title, n_code=len(code_blocks),
                                     n_points=len(points)))

    print(f"Title      : {art.title}")
    print(f"Subtitle   : {art.subtitle}")
    print(f"Sections   : {len(art.sections)} | Code blocks: {len(code_blocks)} "
          f"| Key points: {len(points)}")
    print(f"Output dir : {out}/")
    for p in (cleaned_path, thumb, info, bundle_path, instr):
        print(f"  - {p}")
    return 0


_INSTRUCTIONS = """# Publish bundle for: {title}

Generated assets:
- thumbnail.png      cover image (1200x627) -> upload as the article cover
- infographic.png    portrait infographic (1080x1920) -> embed in body / share
- linkedin_body.txt  spacing-cleaned body ({n_points} key points extracted)
- publish_bundle.js  console script ({n_code} code block(s) injected as <pre>)

## Steps
1. Open the LinkedIn article editor (linkedin.com -> Write article).
2. Upload thumbnail.png as the cover image (native file dialog).
3. Open DevTools console, paste the contents of publish_bundle.js, press Enter.
4. Verify every code block renders on a DARK background (the mandatory gate).
5. Embed infographic.png where you want it, then click Publish.

LinkedIn's public API cannot create articles, so step 3 is browser-assisted by design.
"""


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="linkedin-publish",
                                description="Markdown article -> LinkedIn publishing bundle")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build the full bundle from a markdown file")
    b.add_argument("article", help="path to the markdown article")
    b.add_argument("--out", help="output directory (default: article slug)")
    b.add_argument("--eyebrow", default="OMEGAFOUNDERS", help="thumbnail eyebrow label")
    b.set_defaults(func=build)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
