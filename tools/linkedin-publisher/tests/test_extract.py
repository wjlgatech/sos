import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from linkedin_publisher.extract import parse_article

MD = """# CLAUDE.md is Your AI's Operating System

**Day 10 of building an AI coaching agent in public.**

## What is it
Some text here.

## Key Takeaways
- First takeaway that is meaningful
- Second takeaway that is also meaningful
- Third one here too
"""


def test_title_and_subtitle():
    a = parse_article(MD)
    assert a.title.startswith("CLAUDE.md")
    assert "Day 10" in a.subtitle


def test_sections_and_points():
    a = parse_article(MD)
    assert "What is it" in a.sections
    assert len(a.key_points) >= 3
    assert any("takeaway" in p.lower() for p in a.key_points)


def test_slug():
    a = parse_article(MD)
    assert " " not in a.slug and a.slug == a.slug.lower()


def test_key_points_ignore_code_block_yaml():
    md = """# T

## How it works
intro

```yaml
- name: Run Claude review
- name: Validate review output
```

## Key Takeaways
- A real human-readable takeaway about agents
- Another genuine lesson worth sharing here
"""
    from linkedin_publisher.extract import parse_article
    a = parse_article(md)
    assert all("name:" not in p for p in a.key_points)
    assert any("takeaway" in p.lower() or "lesson" in p.lower() for p in a.key_points)


def test_subtitle_is_dek_not_deep_bold():
    md = """# Pancakes and AI Architecture

*A complete guide to the agentic loop.*

## Section
Body text here with a **required** bold phrase deep inside.
"""
    from linkedin_publisher.extract import parse_article
    a = parse_article(md)
    assert a.subtitle.startswith("A complete guide to the agentic loop")
    assert "required" not in a.subtitle
