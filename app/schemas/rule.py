from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ALLOWED_DOCUMENT_TYPES = ("PDF", "JPG", "PNG")


class RuleWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    category: str = Field(min_length=1, max_length=100)
    valid_from: date
    valid_until: date | None = None
    max_hours: Decimal | None = Field(default=None, gt=0, le=Decimal("99999.99"))
    accepted_document_types: list[str] = Field(min_length=1)
    confidence_threshold: float = Field(ge=0, le=1)
    allows_auto_approval: bool = False

    @field_validator("accepted_document_types")
    @classmethod
    def validate_documents(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            token = item.strip().upper()
            if token == "JPEG":
                token = "JPG"
            if token not in ALLOWED_DOCUMENT_TYPES:
                raise ValueError("Documentos aceitos: PDF, JPG ou PNG.")
            if token not in cleaned:
                cleaned.append(token)
        if not cleaned:
            raise ValueError("Informe ao menos um documento aceito.")
        return cleaned

    @model_validator(mode="after")
    def validate_period(self):
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("O fim da vigência deve ser igual ou posterior ao início.")
        return self


class RuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    valid_from: date
    valid_until: date | None
    max_hours: Decimal | None
    accepted_document_types: list[str] | None
    confidence_threshold: float
    allows_auto_approval: bool
