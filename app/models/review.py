from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.enums import ReviewDecision
from app.models.mixins import TimestampMixin


class ManualReview(TimestampMixin, Base):
    __tablename__ = "manual_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), index=True
    )
    evaluator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    decision: Mapped[ReviewDecision] = mapped_column(Enum(ReviewDecision, name="review_decision"))
    justification: Mapped[str] = mapped_column(Text)

    submission = relationship("Submission", back_populates="manual_reviews")
    evaluator = relationship("User")
