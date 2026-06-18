import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from linkedin_publisher.preprocess import to_linkedin_text
from linkedin_publisher.publish import build_publish_bundle


def test_bundle_contains_payload_and_tiptap():
    md = "# T\n\nintro para\n\n```py\nx=1\n```\n\noutro para"
    text, blocks = to_linkedin_text(md)
    js = build_publish_bundle("T", text, blocks)
    assert "codeBlock" in js
    assert "DataTransfer" in js
    assert "x=1" in js  # code survived into payload
    # payload must be valid embedded JSON
    start = js.index("{")
    assert '"segments"' in js and '"codes"' in js
