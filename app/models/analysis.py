from sqlalchemy import Enum, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.enums import AnalysisResult
from app.models.mixins import TimestampMixin


class AutomaticAnalysis(TimestampMixin, Base):
    __tablename__ = "automatic_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), unique=True, index=True
    )
    result: Mapped[AnalysisResult] = mapped_column(Enum(AnalysisResult, name="analysis_result"))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    submission = relationship("Submission", back_populates="automatic_analysis")
