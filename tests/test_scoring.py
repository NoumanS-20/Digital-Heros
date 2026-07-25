from app.models import Metrics
from app.scoring import evaluate


def _m(**kw):
    base = dict(
        http_status=200, response_time_ms=100, title="A great page title here",
        meta_description="d" * 80, h1_count=1, images_total=4,
        images_missing_alt=0, word_count=500,
    )
    base.update(kw)
    return Metrics(**base)


def test_perfect_page_scores_grade_a_no_fixes():
    card, fixes = evaluate(_m())
    assert card.overall >= 90
    assert card.grade == "A"
    assert fixes == []


def test_missing_alt_is_high_severity_first_and_halves_a11y():
    card, fixes = evaluate(_m(images_missing_alt=2))
    assert fixes[0].severity == "high"
    assert fixes[0].area == "accessibility"
    assert card.breakdown.accessibility == 50


def test_fixes_sorted_high_to_low():
    _, fixes = evaluate(_m(title="short", images_missing_alt=1, word_count=10))
    order = {"high": 0, "medium": 1, "low": 2}
    severities = [f.severity for f in fixes]
    assert severities == sorted(severities, key=lambda s: order[s])
    assert "high" in severities and "low" in severities
