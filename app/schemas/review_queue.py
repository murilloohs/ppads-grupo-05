from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ReviewQueueItem(BaseModel):
    id: int
    protocol: str
    submitted_at: datetime
    student_name: str
    title: str
    category: str
    declared_hours: Decimal
    has_analysis: bool
    has_rule: bool


class CertificateRead(BaseModel):
    id: int
    original_name: str
    mime_type: str
    size_bytes: int
    ocr_text: str | None
    extracted_data: dict | None


class ActivityReviewRead(BaseModel):
    title: str
    category: str
    provider_name: str | None
    start_date: date | None
    end_date: date | None
    declared_hours: Decimal
    description: str | None
    student_name: str


class AnalysisRead(BaseModel):
    result: str
    confidence: float | None
    explanation: str | None


class RuleReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    valid_from: date
    valid_until: date | None
    max_hours: Decimal | None
    accepted_document_types: list[str] | None
    confidence_threshold: float
    allows_auto_approval: bool


class ReviewDetail(BaseModel):
    id: int
    protocol: str
    submitted_at: datetime
    status: str
    activity: ActivityReviewRead
    certificates: list[CertificateRead]
    analysis: AnalysisRead | None
    rule: RuleReviewRead | None
