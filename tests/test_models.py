import pytest
from pydantic import ValidationError

from app.models import Fix, ScoreBreakdown, ScoreCard


def test_fix_accepts_valid_severity():
    f = Fix(severity="high", area="seo", message="x")
    assert f.severity == "high"


def test_fix_rejects_bad_severity():
    with pytest.raises(ValidationError):
        Fix(severity="urgent", area="seo", message="x")


def test_scorecard_nests_breakdown():
    c = ScoreCard(
        overall=80,
        grade="B",
        breakdown=ScoreBreakdown(seo=80, accessibility=70, performance=90),
    )
    assert c.breakdown.seo == 80
