from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.activity import ComplementaryActivity
from app.models.enums import ReviewDecision, SubmissionStatus
from app.models.history import StatusHistory
from app.models.review import ManualReview
from app.models.submission import Submission
from app.models.user import User


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_pending(self, institution_id: int) -> list[Submission]:
        statement = (
            self._pending(institution_id)
            .options(
                joinedload(Submission.activity),
                joinedload(Submission.student),
                joinedload(Submission.automatic_analysis),
                joinedload(Submission.validation_rule),
            )
            .order_by(Submission.submitted_at, Submission.id)
        )
        return list(self.db.scalars(statement).unique().all())

    def get_pending(self, submission_id: int, institution_id: int) -> Submission | None:
        statement = (
            self._pending(institution_id)
            .where(Submission.id == submission_id)
            .options(
                joinedload(Submission.activity).joinedload(ComplementaryActivity.documents),
                joinedload(Submission.student),
                joinedload(Submission.automatic_analysis),
                joinedload(Submission.validation_rule),
            )
        )
        return self.db.scalars(statement).unique().first()

    def record_decision(
        self,
        submission: Submission,
        evaluator_id: int,
        decision: ReviewDecision,
        justification: str,
        status: SubmissionStatus,
        note: str,
    ) -> Submission:
        submission.status = status
        self.db.add(
            ManualReview(
                submission_id=submission.id,
                evaluator_id=evaluator_id,
                decision=decision,
                justification=justification,
            )
        )
        self.db.add(
            StatusHistory(
                submission_id=submission.id,
                status=status,
                changed_by_id=evaluator_id,
                note=note,
            )
        )
        self.db.commit()
        self.db.refresh(submission)
        return submission

    @staticmethod
    def _pending(institution_id: int):
        return (
            select(Submission)
            .join(User, Submission.student_id == User.id)
            .where(
                Submission.status == SubmissionStatus.PENDING_REVIEW,
                User.institution_id == institution_id,
            )
        )
