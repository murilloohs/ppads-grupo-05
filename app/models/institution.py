from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin


class Institution(TimestampMixin, Base):
    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    code: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    courses = relationship("Course", back_populates="institution")
    users = relationship("User", back_populates="institution")
    rules = relationship("ValidationRule", back_populates="institution")
