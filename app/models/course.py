from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin


class Course(TimestampMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (UniqueConstraint("institution_id", "name", name="uq_course_institution_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    required_complementary_hours: Mapped[int] = mapped_column(default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    institution = relationship("Institution", back_populates="courses")
    users = relationship("User", back_populates="course")
    rules = relationship("ValidationRule", back_populates="course")
