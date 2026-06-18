"""linkedin_publisher — turn a markdown article into a LinkedIn-ready bundle.

Pipeline:
  markdown article  ->  cleaned paste text + extracted code blocks
                    ->  generated thumbnail (1200x627) + infographic (1080x1920)
                    ->  browser-console publish bundle (Tiptap/ProseMirror injection)

LinkedIn's public API cannot create long-form articles, so the final publish
step is browser-assisted: the tool produces the exact console script to run in
the open LinkedIn article editor.
"""
from .preprocess import strip_markdown, extract_code_blocks, to_linkedin_text
from .extract import parse_article, Article
from .images import generate_thumbnail, generate_infographic
from .publish import build_publish_bundle

__version__ = "0.1.0"
__all__ = [
    "strip_markdown", "extract_code_blocks", "to_linkedin_text",
    "parse_article", "Article",
    "generate_thumbnail", "generate_infographic",
    "build_publish_bundle",
]
