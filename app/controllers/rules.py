from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.rule import RuleRead, RuleWrite
from app.services.rule_service import RuleService

router = APIRouter(prefix="/rules", tags=["Regras de validação"])


@router.get("", response_model=list[RuleRead])
def list_rules(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> list[RuleRead]:
    return RuleService(db).list_for(current_admin)


@router.post("", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: RuleWrite,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> RuleRead:
    return RuleService(db).create(payload, current_admin)


@router.put("/{rule_id}", response_model=RuleRead)
def update_rule(
    rule_id: int,
    payload: RuleWrite,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> RuleRead:
    return RuleService(db).update(rule_id, payload, current_admin)
