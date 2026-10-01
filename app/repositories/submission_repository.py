from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import ComplementaryActivity
from app.models.document import CertificateDocument
from app.models.history import StatusHistory
from app.models.submission import Submission


class SubmissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def owned_activity(self, activity_id, student_id):
        return self.db.scalar(
            select(ComplementaryActivity)
            .where(
                ComplementaryActivity.id == activity_id,
                ComplementaryActivity.student_id == student_id,
            )
            .with_for_update()
        )

    def has_document(self, activity_id):
        return (
            self.db.scalar(
                select(CertificateDocument.id)
                .where(CertificateDocument.activity_id == activity_id)
                .limit(1)
            )
            is not None
        )

    def existing(self, activity_id):
        return self.db.scalar(select(Submission).where(Submission.activity_id == activity_id))

    def save(self, submission, student_id):
        self.db.add(submission)
        self.db.flush()
        self.db.add(
            StatusHistory(
                submission_id=submission.id,
                status=submission.status,
                changed_by_id=student_id,
                note="Solicitação recebida com documento comprobatório.",
            )
        )
        self.db.commit()
        self.db.refresh(submission)
        return submission
