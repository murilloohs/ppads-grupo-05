from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rule import ValidationRule


class RuleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_institution(self, institution_id: int) -> list[ValidationRule]:
        statement = (
            select(ValidationRule)
            .where(
                ValidationRule.institution_id == institution_id,
                ValidationRule.course_id.is_(None),
            )
            .order_by(ValidationRule.category, ValidationRule.id)
        )
        return list(self.db.scalars(statement).all())

    def get_for_institution(self, rule_id: int, institution_id: int) -> ValidationRule | None:
        statement = select(ValidationRule).where(
            ValidationRule.id == rule_id,
            ValidationRule.institution_id == institution_id,
            ValidationRule.course_id.is_(None),
        )
        return self.db.scalars(statement).first()

    def find_by_category(
        self, institution_id: int, category: str, ignore_id: int | None = None
    ) -> ValidationRule | None:
        statement = select(ValidationRule).where(
            ValidationRule.institution_id == institution_id,
            ValidationRule.course_id.is_(None),
            ValidationRule.category == category,
        )
        if ignore_id is not None:
            statement = statement.where(ValidationRule.id != ignore_id)
        return self.db.scalars(statement).first()

    def add(self, rule: ValidationRule) -> ValidationRule:
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def save(self, rule: ValidationRule) -> ValidationRule:
        self.db.commit()
        self.db.refresh(rule)
        return rule

    @staticmethod
    def apply(
        rule: ValidationRule,
        *,
        category: str,
        valid_from: date,
        valid_until: date | None,
        max_hours: Decimal | None,
        accepted_document_types: list[str],
        confidence_threshold: float,
        allows_auto_approval: bool,
    ) -> None:
        rule.category = category
        rule.valid_from = valid_from
        rule.valid_until = valid_until
        rule.max_hours = max_hours
        rule.accepted_document_types = accepted_document_types
        rule.confidence_threshold = confidence_threshold
        rule.allows_auto_approval = allows_auto_approval
