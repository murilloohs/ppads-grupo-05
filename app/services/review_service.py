from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import CertificateDocument
from app.models.enums import AnalysisResult
from app.models.submission import Submission
from app.models.user import User
from app.repositories.review_repository import ReviewRepository
from app.schemas.review_queue import (
    ActivityReviewRead,
    AnalysisRead,
    CertificateRead,
    ReviewDetail,
    ReviewQueueItem,
    RuleReviewRead,
)

_ANALYSIS_RESULTS = {
    AnalysisResult.APPROVED: "Aprovada na análise automática",
    AnalysisResult.MANUAL_REVIEW: "Encaminhada para análise manual",
    AnalysisResult.FAILED: "Análise automática sem conclusão",
}


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.repository = ReviewRepository(db)

    def list_queue(self, evaluator: User) -> list[ReviewQueueItem]:
        pending = self.repository.list_pending(evaluator.institution_id)
        return [self._item(submission) for submission in pending]

    def get_detail(self, submission_id: int, evaluator: User) -> ReviewDetail:
        submission = self._pending(submission_id, evaluator)
        activity = submission.activity
        analysis = submission.automatic_analysis
        return ReviewDetail(
            id=submission.id,
            protocol=submission.protocol,
            submitted_at=submission.submitted_at,
            status="Aguardando revisão",
            activity=ActivityReviewRead(
                title=activity.title,
                category=activity.category,
                provider_name=activity.provider_name,
                start_date=activity.start_date,
                end_date=activity.end_date,
                declared_hours=activity.declared_hours,
                description=activity.description,
                student_name=submission.student.name,
            ),
            certificates=[self._certificate(document) for document in activity.documents],
            analysis=self._analysis(analysis) if analysis else None,
            rule=RuleReviewRead.model_validate(submission.validation_rule)
            if submission.validation_rule
            else None,
        )

    def certificate_file(
        self, submission_id: int, document_id: int, evaluator: User
    ) -> tuple[Path, str, str]:
        submission = self._pending(submission_id, evaluator)
        document = next(
            (item for item in submission.activity.documents if item.id == document_id), None
        )
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Certificado não encontrado."
            )
        path = self._safe_path(document.storage_path)
        if path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Certificado não encontrado."
            )
        return path, document.mime_type, document.original_name

    def _pending(self, submission_id: int, evaluator: User) -> Submission:
        submission = self.repository.get_pending(submission_id, evaluator.institution_id)
        if submission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação não encontrada."
            )
        return submission

    @staticmethod
    def _item(submission: Submission) -> ReviewQueueItem:
        return ReviewQueueItem(
            id=submission.id,
            protocol=submission.protocol,
            submitted_at=submission.submitted_at,
            student_name=submission.student.name,
            title=submission.activity.title,
            category=submission.activity.category,
            declared_hours=submission.activity.declared_hours,
            has_analysis=submission.automatic_analysis is not None,
            has_rule=submission.validation_rule_id is not None,
        )

    @staticmethod
    def _certificate(document: CertificateDocument) -> CertificateRead:
        return CertificateRead(
            id=document.id,
            original_name=document.original_name,
            mime_type=document.mime_type,
            size_bytes=document.size_bytes,
            ocr_text=document.ocr_text,
            extracted_data=document.extracted_data,
        )

    @staticmethod
    def _analysis(analysis) -> AnalysisRead:
        return AnalysisRead(
            result=_ANALYSIS_RESULTS.get(analysis.result, "Aguardando resultado"),
            confidence=analysis.confidence,
            explanation=analysis.explanation,
        )

    @staticmethod
    def _safe_path(storage_path: str) -> Path | None:
        root = Path(settings.upload_dir).resolve()
        path = Path(storage_path).resolve()
        if not path.is_file() or not path.is_relative_to(root):
            return None
        return path
