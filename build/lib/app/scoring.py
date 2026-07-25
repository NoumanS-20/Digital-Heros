from __future__ import annotations

from app.models import Fix, Metrics, ScoreBreakdown, ScoreCard

WEIGHT_SEO = 0.40
WEIGHT_A11Y = 0.35
WEIGHT_PERF = 0.25

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _grade(overall: int) -> str:
    if overall >= 90:
        return "A"
    if overall >= 75:
        return "B"
    if overall >= 60:
        return "C"
    if overall >= 40:
        return "D"
    return "F"


def evaluate(m: Metrics) -> tuple[ScoreCard, list[Fix]]:
    fixes: list[Fix] = []

    # SEO: four equally weighted rules
    seo_passed = 0
    if m.title and 10 <= len(m.title) <= 60:
        seo_passed += 1
    elif not m.title:
        fixes.append(Fix(severity="high", area="seo",
            message="Page has no <title> — add a descriptive 10–60 character title."))
    else:
        fixes.append(Fix(severity="low", area="seo",
            message=f"Title is {len(m.title)} chars — aim for 10–60 for clean search snippets."))

    if m.meta_description and 50 <= len(m.meta_description) <= 160:
        seo_passed += 1
    elif not m.meta_description:
        fixes.append(Fix(severity="medium", area="seo",
            message="Meta description is missing — add one of 50–160 characters."))
    else:
        fixes.append(Fix(severity="low", area="seo",
            message=f"Meta description is {len(m.meta_description)} chars — aim for 50–160."))

    if m.h1_count == 1:
        seo_passed += 1
    elif m.h1_count == 0:
        fixes.append(Fix(severity="medium", area="seo",
            message="No <h1> found — add exactly one primary heading."))
    else:
        fixes.append(Fix(severity="low", area="seo",
            message=f"{m.h1_count} <h1> tags found — use exactly one primary heading."))

    if m.word_count > 300:
        seo_passed += 1
    else:
        fixes.append(Fix(severity="medium", area="seo",
            message=f"Only ~{m.word_count} words — thin content ranks poorly; aim for 300+."))

    seo = round(100 * seo_passed / 4)

    # Accessibility: alt-text coverage
    if m.images_total == 0:
        a11y = 100
    else:
        covered = m.images_total - m.images_missing_alt
        a11y = round(100 * covered / m.images_total)
        if m.images_missing_alt > 0:
            fixes.append(Fix(severity="high", area="accessibility",
                message=(f"{m.images_missing_alt} of {m.images_total} images are missing "
                         "alt text — add descriptive alt attributes.")))

    # Performance: response-time bands
    rt = m.response_time_ms
    if rt < 500:
        perf = 100
    elif rt < 1500:
        perf = 70
    elif rt < 3000:
        perf = 40
    else:
        perf = 10
    if perf < 70:
        fixes.append(Fix(severity="medium", area="performance",
            message=f"Response took {rt} ms — investigate server/CDN latency (aim <500 ms)."))

    overall = round(WEIGHT_SEO * seo + WEIGHT_A11Y * a11y + WEIGHT_PERF * perf)
    fixes.sort(key=lambda f: _SEVERITY_ORDER[f.severity])

    card = ScoreCard(
        overall=overall,
        grade=_grade(overall),
        breakdown=ScoreBreakdown(seo=seo, accessibility=a11y, performance=perf),
    )
    return card, fixes
