from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.institution import InstitutionCreate, InstitutionRead
from app.services.institution_service import InstitutionService

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.post("", response_model=InstitutionRead, status_code=status.HTTP_201_CREATED)
def create_institution(
    payload: InstitutionCreate, db: Session = Depends(get_db)
) -> InstitutionRead:
    return InstitutionService(db).create(payload)


@router.get("", response_model=list[InstitutionRead])
def list_institutions(db: Session = Depends(get_db)) -> list[InstitutionRead]:
    return InstitutionService(db).list_all()
