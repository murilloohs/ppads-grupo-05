from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.enums import SubmissionStatus
from app.models.mixins import TimestampMixin


class Submission(TimestampMixin, Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    protocol: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("complementary_activities.id"), index=True)
    validation_rule_id: Mapped[int | None] = mapped_column(
        ForeignKey("validation_rules.id"), nullable=True
    )
    document_id: Mapped[int | None] = mapped_column(ForeignKey("certificate_documents.id"))
    activity_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    document = relationship("CertificateDocument")
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status"),
        default=SubmissionStatus.SUBMITTED,
        index=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    student = relationship("User", back_populates="submissions")
    activity = relationship("ComplementaryActivity", back_populates="submissions")
    validation_rule = relationship("ValidationRule", back_populates="submissions")
    automatic_analysis = relationship(
        "AutomaticAnalysis", back_populates="submission", uselist=False
    )
    manual_reviews = relationship("ManualReview", back_populates="submission")
    history = relationship(
        "StatusHistory", back_populates="submission", cascade="all, delete-orphan"
    )
