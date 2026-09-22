from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin


class ValidationRule(TimestampMixin, Base):
    __tablename__ = "validation_rules"
    __table_args__ = (UniqueConstraint("institution_id", "course_id", "category", "version", name="uq_rule_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), index=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    valid_from: Mapped[date] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    max_hours: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    accepted_document_types: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    mandatory_criteria: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.85)
    allows_auto_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    institution = relationship("Institution", back_populates="rules")
    course = relationship("Course", back_populates="rules")
    submissions = relationship("Submission", back_populates="validation_rule")
