from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from app.models.analysis import AutomaticAnalysis
from app.models.enums import AnalysisResult, SubmissionStatus
from app.models.submission import Submission
from app.repositories.rule_repository import RuleRepository
from app.repositories.submission_repository import SubmissionRepository
from app.services.analysis_service import AnalysisService, SimpleAnalysis, select_rule
from app.services.document_service import verified_path
from app.services.ocr_service import CertificateOcrService, OcrReading

_DOCUMENT_TYPES = {
    "application/pdf": "PDF",
    "image/jpeg": "JPG",
    "image/jpg": "JPG",
    "image/png": "PNG",
    ".pdf": "PDF",
    ".jpg": "JPG",
    ".jpeg": "JPG",
    ".png": "PNG",
}


class SubmissionService:
    def __init__(self, repository: SubmissionRepository):
        self.repository = repository
        self.ocr = CertificateOcrService()
        self.analysis = AnalysisService()

    def submit(self, activity_id, student_id):
        activity = self.repository.owned_activity(activity_id, student_id)
        if not activity:
            raise HTTPException(404, "Atividade não encontrada.")
        previous = self.repository.existing(activity_id)
        if previous and previous.status != SubmissionStatus.CORRECTION_REQUESTED:
            raise HTTPException(400, "Esta atividade já foi submetida.")
        document = self.repository.latest_document(activity_id)
        if document is None:
            raise HTTPException(400, "É obrigatório anexar um documento antes de enviar.")
        reading = self._read(str(verified_path(document)), document.mime_type)
        document.ocr_text = reading.text
        document.extracted_data = reading.fields
        outcome = self._analyze(activity, reading, document)
        submission = self.repository.save(
            Submission(
                protocol=f"VAL-{datetime.now(UTC).year}-{uuid4().hex[:12].upper()}",
                student_id=student_id,
                activity_id=activity_id,
                validation_rule_id=outcome.rule_id,
                document_id=document.id,
                activity_snapshot={
                    "title": activity.title,
                    "category": activity.category,
                    "provider_name": activity.provider_name,
                    "start_date": activity.start_date.isoformat() if activity.start_date else None,
                    "end_date": activity.end_date.isoformat() if activity.end_date else None,
                    "declared_hours": str(activity.declared_hours),
                    "description": activity.description,
                },
                status=outcome.status,
            ),
            student_id,
            outcome.explanation,
            AutomaticAnalysis(
                result=outcome.result,
                confidence=outcome.confidence,
                details=outcome.details,
                explanation=outcome.explanation,
            ),
        )
        return {
            "message": "Solicitação enviada com sucesso!",
            "protocol": submission.protocol,
            "status": submission.status.value,
            "leitura": {"ok": reading.ok, "dados": reading.fields},
            "analise": {
                "resultado": outcome.result.value,
                "confianca": outcome.confidence,
                "explicacao": outcome.explanation,
            },
        }

    def _analyze(self, activity, reading: OcrReading, document) -> SimpleAnalysis:
        try:
            on_date = activity.start_date or date.today()
            rules = RuleRepository(self.repository.db).applicable(
                activity.student.institution_id, on_date
            )
            rule = select_rule(rules, activity.category)
            return self.analysis.evaluate(
                activity,
                reading.fields,
                rule,
                student_name=activity.student.name,
                document_type=_document_type(document.mime_type, document.original_name),
                ocr_ok=reading.ok,
            )
        except Exception:
            return SimpleAnalysis(
                result=AnalysisResult.MANUAL_REVIEW,
                status=SubmissionStatus.PENDING_REVIEW,
                confidence=0.0,
                explanation=(
                    "Não foi possível concluir a análise. A solicitação segue para revisão manual."
                ),
                details={"comparacoes": [], "divergencias": [], "motivo": "falha_na_analise"},
                rule_id=None,
            )

    def _read(self, path: str, mime_type: str | None) -> OcrReading:
        try:
            return self.ocr.read(path, mime_type)
        except Exception:
            return OcrReading(False, None, None)


def _document_type(mime_type: str | None, original_name: str | None) -> str | None:
    mime = (mime_type or "").split(";", 1)[0].strip().lower()
    if mime in _DOCUMENT_TYPES:
        return _DOCUMENT_TYPES[mime]
    return _DOCUMENT_TYPES.get(Path(original_name or "").suffix.lower())
