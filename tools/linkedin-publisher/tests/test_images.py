import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from linkedin_publisher.images import generate_thumbnail, generate_infographic


def test_thumbnail_dimensions():
    with tempfile.TemporaryDirectory() as d:
        p = generate_thumbnail("A Reasonably Long Title About Agents",
                               "A subtitle line", os.path.join(d, "t.png"))
        assert Image.open(p).size == (1200, 627)


def test_infographic_dimensions_and_points():
    with tempfile.TemporaryDirectory() as d:
        p = generate_infographic("Title Here",
                                 ["point one here", "point two here", "point three"],
                                 os.path.join(d, "i.png"))
        assert Image.open(p).size == (1080, 1920)


def test_handles_empty_points():
    with tempfile.TemporaryDirectory() as d:
        p = generate_infographic("Title", [], os.path.join(d, "i.png"))
        assert os.path.exists(p)
