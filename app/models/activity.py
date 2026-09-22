from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin


class ComplementaryActivity(TimestampMixin, Base):
    __tablename__ = "complementary_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100), index=True)
    provider_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    declared_hours: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    student = relationship("User", back_populates="activities")
    documents = relationship("CertificateDocument", back_populates="activity", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="activity")
