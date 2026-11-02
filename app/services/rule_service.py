from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.rule import ValidationRule
from app.models.user import User
from app.repositories.rule_repository import RuleRepository
from app.schemas.rule import RuleWrite


class RuleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = RuleRepository(db)

    def list_for(self, admin: User) -> list[ValidationRule]:
        return self.repository.list_for_institution(admin.institution_id)

    def create(self, payload: RuleWrite, admin: User) -> ValidationRule:
        self._ensure_unique(admin.institution_id, payload.category)
        rule = ValidationRule(
            institution_id=admin.institution_id,
            course_id=None,
            version=1,
            active=True,
            created_by_id=admin.id,
            category=payload.category,
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
            max_hours=self._hours(payload.max_hours),
            accepted_document_types=payload.accepted_document_types,
            confidence_threshold=payload.confidence_threshold,
            allows_auto_approval=payload.allows_auto_approval,
        )
        try:
            return self.repository.add(rule)
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma regra para esta categoria.",
            ) from exc

    def update(self, rule_id: int, payload: RuleWrite, admin: User) -> ValidationRule:
        rule = self.repository.get_for_institution(rule_id, admin.institution_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Regra não encontrada."
            )
        self._ensure_unique(admin.institution_id, payload.category, ignore_id=rule.id)
        self.repository.apply(
            rule,
            category=payload.category,
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
            max_hours=self._hours(payload.max_hours),
            accepted_document_types=payload.accepted_document_types,
            confidence_threshold=payload.confidence_threshold,
            allows_auto_approval=payload.allows_auto_approval,
        )
        try:
            return self.repository.save(rule)
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma regra para esta categoria.",
            ) from exc

    def _ensure_unique(
        self, institution_id: int, category: str, ignore_id: int | None = None
    ) -> None:
        if self.repository.find_by_category(institution_id, category, ignore_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma regra para esta categoria.",
            )

    @staticmethod
    def _hours(value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(Decimal("0.01"))
