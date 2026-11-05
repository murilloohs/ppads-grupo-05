from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.institution import Institution
from app.models.rule import ValidationRule
from app.models.user import User
from app.repositories.rule_repository import RuleRepository
from app.schemas.rule import RuleWrite


class RuleService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = RuleRepository(db)

    def list_for(self, admin: User):
        rules = self.repository.list_for_institution(admin.institution_id)
        latest = {}
        for rule in rules:
            key = rule.category.casefold()
            if key not in latest or rule.version > latest[key].version:
                latest[key] = rule
        return list(latest.values())

    def _lock(self, institution_id):
        self.db.execute(
            select(Institution).where(Institution.id == institution_id).with_for_update()
        ).scalar_one()

    def create(self, payload: RuleWrite, admin: User):
        self._lock(admin.institution_id)
        if self.repository.find_by_category(admin.institution_id, payload.category):
            raise HTTPException(409, "Já existe uma regra para esta categoria.")
        return self._new(payload, admin, 1)

    def update(self, rule_id: int, payload: RuleWrite, admin: User):
        self._lock(admin.institution_id)
        rule = self.repository.get_for_institution(rule_id, admin.institution_id)
        if rule is None:
            raise HTTPException(404, "Regra não encontrada.")
        if payload.category.casefold() != rule.category.casefold():
            raise HTTPException(422, "Para outra categoria, cadastre uma nova regra.")
        versions = self.versions(rule_id, admin)
        if rule.version != max(item.version for item in versions):
            raise HTTPException(409, "A regra foi atualizada. Recarregue antes de editar.")
        return self._new(payload, admin, rule.version + 1)

    def versions(self, rule_id: int, admin: User):
        rule = self.repository.get_for_institution(rule_id, admin.institution_id)
        if rule is None:
            raise HTTPException(404, "Regra não encontrada.")
        return [
            item
            for item in self.repository.list_for_institution(admin.institution_id)
            if item.category.casefold() == rule.category.casefold()
        ]

    def _new(self, payload, admin, version):
        values = payload.model_dump()
        if values["max_hours"] is not None:
            values["max_hours"] = Decimal(values["max_hours"]).quantize(Decimal("0.01"))
        rule = ValidationRule(
            **values,
            institution_id=admin.institution_id,
            course_id=None,
            version=version,
            active=True,
            created_by_id=admin.id,
        )
        return self.repository.add(rule)
