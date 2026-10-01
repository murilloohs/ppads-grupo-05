from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException

from app.models.enums import SubmissionStatus
from app.models.submission import Submission
from app.repositories.submission_repository import SubmissionRepository


class SubmissionService:
    def __init__(self, repository: SubmissionRepository):
        self.repository = repository

    def submit(self, activity_id, student_id):
        if not self.repository.owned_activity(activity_id, student_id):
            raise HTTPException(404, "Atividade não encontrada.")
        if self.repository.existing(activity_id):
            raise HTTPException(400, "Esta atividade já foi submetida.")
        if not self.repository.has_document(activity_id):
            raise HTTPException(400, "É obrigatório anexar um documento antes de enviar.")
        submission = self.repository.save(
            Submission(
                protocol=f"VAL-{datetime.now(UTC).year}-{uuid4().hex[:12].upper()}",
                student_id=student_id,
                activity_id=activity_id,
                status=SubmissionStatus.SUBMITTED,
            ),
            student_id,
        )
        return {
            "message": "Solicitação enviada com sucesso!",
            "protocol": submission.protocol,
            "status": submission.status.value,
        }
