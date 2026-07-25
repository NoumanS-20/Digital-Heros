from app.auditor import parse_html

HAPPY = """
<html><head><title>Example Domain</title>
<meta name="description"
  content="A nice long description well within the fifty to one sixty character sweet spot."></head>
<body><h1>Hello</h1>
<p>alpha beta gamma delta</p>
<img src="a.png" alt="a cat"><img src="b.png"></body></html>
"""


def test_happy_path_extracts_all_fields():
    r = parse_html(HAPPY)
    assert r.title == "Example Domain"
    assert r.meta_description.startswith("A nice long")
    assert r.h1_count == 1
    assert r.images_total == 2
    assert r.images_missing_alt == 1
    assert r.word_count >= 4


def test_missing_tags_yield_defaults():
    r = parse_html("<html><body><img src='x'><img src='y' alt=''></body></html>")
    assert r.title is None
    assert r.meta_description is None
    assert r.h1_count == 0
    assert r.images_total == 2
    assert r.images_missing_alt == 2  # empty alt counts as missing


def test_empty_html_does_not_crash():
    r = parse_html("")
    assert r.title is None
    assert r.h1_count == 0
    assert r.word_count == 0
