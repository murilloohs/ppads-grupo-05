from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "student"
    EVALUATOR = "evaluator"
    COORDINATOR = "coordinator"
    ADMIN = "admin"


class SubmissionStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CORRECTION_REQUESTED = "correction_requested"


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CORRECTION_REQUESTED = "correction_requested"


class AnalysisResult(StrEnum):
    APPROVED = "approved"
    MANUAL_REVIEW = "manual_review"
    FAILED = "failed"
