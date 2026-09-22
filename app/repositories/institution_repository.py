from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.institution import Institution


class InstitutionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, name: str, code: str | None) -> Institution:
        entity = Institution(name=name, code=code)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def list_all(self) -> list[Institution]:
        return list(self.db.scalars(select(Institution).order_by(Institution.name)).all())
