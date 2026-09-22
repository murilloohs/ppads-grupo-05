from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.institution import Institution
from app.repositories.institution_repository import InstitutionRepository
from app.schemas.institution import InstitutionCreate


class InstitutionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = InstitutionRepository(db)

    def create(self, payload: InstitutionCreate) -> Institution:
        try:
            return self.repository.create(name=payload.name, code=payload.code)
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Instituição já cadastrada.",
            ) from exc

    def list_all(self) -> list[Institution]:
        return self.repository.list_all()
