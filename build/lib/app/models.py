from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

Severity = Literal["high", "medium", "low"]
Area = Literal["seo", "accessibility", "performance"]


class ParseResult(BaseModel):
    title: Optional[str]
    meta_description: Optional[str]
    h1_count: int
    images_total: int
    images_missing_alt: int
    word_count: int


class Metrics(BaseModel):
    http_status: int
    response_time_ms: int
    title: Optional[str]
    meta_description: Optional[str]
    h1_count: int
    images_total: int
    images_missing_alt: int
    word_count: int


class Fix(BaseModel):
    severity: Severity
    area: Area
    message: str


class ScoreBreakdown(BaseModel):
    seo: int
    accessibility: int
    performance: int


class ScoreCard(BaseModel):
    overall: int
    grade: str
    breakdown: ScoreBreakdown


class AuditRequest(BaseModel):
    url: str


class AuditReport(BaseModel):
    final_url: str
    fetched_at: str
    metrics: Metrics
    score: ScoreCard
    fixes: list[Fix]
