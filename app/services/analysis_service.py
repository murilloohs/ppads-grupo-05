import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models.enums import AnalysisResult, SubmissionStatus

_SITUATIONS = ("confere", "diverge", "inconclusivo")


@dataclass(frozen=True)
class SimpleAnalysis:
    result: AnalysisResult
    status: SubmissionStatus
    confidence: float
    explanation: str
    details: dict
    rule_id: int | None


def select_rule(rules, category: str):
    target = _normalize(category)
    for rule in rules:
        if _normalize(rule.category) == target:
            return rule
    return None


class AnalysisService:
    def evaluate(
        self,
        activity,
        extracted: dict | None,
        rule,
        *,
        student_name: str | None,
        document_type: str | None,
        ocr_ok: bool,
    ) -> SimpleAnalysis:
        if not ocr_ok:
            return _manual(
                "Não foi possível ler o certificado. A solicitação segue para revisão manual.",
                [],
                rule.id if rule else None,
                motivo="leitura_indisponivel",
            )
        fields = extracted or {}
        checks = [
            _rule_check(activity, rule),
            _validity_check(activity, rule),
            _document_check(document_type, rule),
            _max_hours_check(activity, rule),
            _text_check("Atividade", activity.title, fields.get("Atividade")),
            _text_check("Instituição", activity.provider_name, fields.get("Instituição")),
            _text_check("Nome", student_name, fields.get("Nome")),
            _hours_check(activity.declared_hours, fields.get("Carga horária")),
            _period_check(activity.start_date, activity.end_date, fields.get("Data/período")),
        ]
        matches = sum(item["situacao"] == "confere" for item in checks)
        confidence = round(matches / len(checks), 4)
        divergences = [item for item in checks if item["situacao"] == "diverge"]
        inconclusive = [item for item in checks if item["situacao"] == "inconclusivo"]
        rule_id = rule.id if rule else None
        can_approve = (
            rule is not None
            and rule.allows_auto_approval
            and confidence >= float(rule.confidence_threshold)
            and not divergences
            and not inconclusive
        )
        if can_approve:
            return SimpleAnalysis(
                result=AnalysisResult.APPROVED,
                status=SubmissionStatus.APPROVED,
                confidence=confidence,
                explanation=(
                    "Os dados informados conferem com o certificado e com a regra. "
                    "A solicitação foi aprovada automaticamente."
                ),
                details=_details(checks, rule_id),
                rule_id=rule_id,
            )
        return _manual(_explanation(divergences, inconclusive, rule), checks, rule_id)


def _manual(
    explanation: str, checks: list[dict], rule_id: int | None, motivo: str | None = None
) -> SimpleAnalysis:
    details = _details(checks, rule_id)
    if motivo:
        details["motivo"] = motivo
    confidence = 0.0
    if checks:
        confidence = round(sum(item["situacao"] == "confere" for item in checks) / len(checks), 4)
    return SimpleAnalysis(
        result=AnalysisResult.MANUAL_REVIEW,
        status=SubmissionStatus.PENDING_REVIEW,
        confidence=confidence,
        explanation=explanation,
        details=details,
        rule_id=rule_id,
    )


def _details(checks: list[dict], rule_id: int | None) -> dict:
    return {
        "comparacoes": checks,
        "divergencias": [
            f"{item['campo']}: informado {item['informado']} e referência {item['referencia']}."
            for item in checks
            if item["situacao"] == "diverge"
        ],
        "regra_id": rule_id,
    }


def _explanation(divergences: list[dict], inconclusive: list[dict], rule) -> str:
    parts = []
    if divergences:
        fields = ", ".join(item["campo"].lower() for item in divergences)
        parts.append(f"Foram encontradas divergências em {fields}.")
    if inconclusive:
        fields = ", ".join(item["campo"].lower() for item in inconclusive)
        parts.append(f"A comparação ficou inconclusiva em {fields}.")
    if rule is not None and not rule.allows_auto_approval and not divergences and not inconclusive:
        parts.append("Os dados conferem, mas a regra não permite aprovação automática.")
    if not parts:
        parts.append("A solicitação segue para revisão manual.")
    else:
        parts.append("A solicitação segue para revisão manual.")
    return " ".join(parts)


def _check(campo: str, informed, reference, situation: str) -> dict:
    if situation not in _SITUATIONS:
        situation = "inconclusivo"
    return {
        "campo": campo,
        "informado": _text(informed),
        "referencia": _text(reference),
        "situacao": situation,
    }


def _rule_check(activity, rule) -> dict:
    if rule is None:
        return _check("Regra", activity.category, None, "inconclusivo")
    same = _normalize(activity.category) == _normalize(rule.category)
    return _check("Regra", activity.category, rule.category, "confere" if same else "diverge")


def _validity_check(activity, rule) -> dict:
    informed = _period_label(activity.start_date, activity.end_date)
    if rule is None or activity.start_date is None or activity.end_date is None:
        limit = None if rule is None else _period_label(rule.valid_from, rule.valid_until)
        return _check("Vigência", informed, limit, "inconclusivo")
    if activity.start_date < rule.valid_from or (
        rule.valid_until is not None and activity.end_date > rule.valid_until
    ):
        reference = _period_label(rule.valid_from, rule.valid_until)
        return _check("Vigência", informed, reference, "diverge")
    return _check("Vigência", informed, _period_label(rule.valid_from, rule.valid_until), "confere")


def _document_check(document_type: str | None, rule) -> dict:
    if rule is None:
        return _check("Documento", document_type, None, "inconclusivo")
    accepted = rule.accepted_document_types or []
    if not accepted:
        return _check("Documento", document_type, "sem restrição", "confere")
    if not document_type:
        return _check("Documento", None, ", ".join(accepted), "inconclusivo")
    situation = "confere" if document_type in {item.upper() for item in accepted} else "diverge"
    return _check("Documento", document_type, ", ".join(accepted), situation)


def _max_hours_check(activity, rule) -> dict:
    informed = _text(activity.declared_hours)
    if rule is None:
        return _check("Carga horária máxima", informed, None, "inconclusivo")
    if rule.max_hours is None:
        return _check("Carga horária máxima", informed, "sem limite", "confere")
    if activity.declared_hours > rule.max_hours:
        return _check("Carga horária máxima", informed, rule.max_hours, "diverge")
    return _check("Carga horária máxima", informed, rule.max_hours, "confere")


def _text_check(campo: str, informed, extracted) -> dict:
    agreed = _texts_agree(informed, extracted)
    if agreed is None:
        return _check(campo, informed, extracted, "inconclusivo")
    return _check(campo, informed, extracted, "confere" if agreed else "diverge")


def _hours_check(declared, extracted) -> dict:
    found = _parse_hours(extracted)
    if found is None:
        return _check("Carga horária", declared, extracted, "inconclusivo")
    same = declared.quantize(Decimal("0.01")) == found.quantize(Decimal("0.01"))
    return _check("Carga horária", declared, found, "confere" if same else "diverge")


def _period_check(start: date | None, end: date | None, extracted) -> dict:
    informed = _period_label(start, end)
    unique = sorted(set(_parse_dates(extracted)))
    if start is None or end is None or not unique:
        return _check("Data/período", informed, extracted, "inconclusivo")
    if len(unique) == 1:
        conclusion = unique[0]
        matches = end == conclusion and start <= conclusion
        return _check("Data/período", informed, extracted, "confere" if matches else "diverge")
    opening, closing = unique[0], unique[-1]
    if opening <= start <= closing and opening <= end <= closing:
        return _check("Data/período", informed, extracted, "confere")
    return _check("Data/período", informed, extracted, "diverge")


def _texts_agree(left, right) -> bool | None:
    normalized_left, normalized_right = _normalize(left), _normalize(right)
    if not normalized_left or not normalized_right:
        return None
    if (
        normalized_left == normalized_right
        or normalized_left in normalized_right
        or normalized_right in normalized_left
    ):
        return True
    left_tokens = set(normalized_left.split())
    right_tokens = set(normalized_right.split())
    if not left_tokens or not right_tokens:
        return None
    return len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens)) >= 0.6


def _normalize(value) -> str:
    if value is None:
        return ""
    decomposed = unicodedata.normalize("NFKD", str(value))
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", without_accents.lower()).strip()


def _parse_hours(value) -> Decimal | None:
    if isinstance(value, Decimal):
        return value
    match = re.search(r"\d+(?:[.,]\d+)?", "" if value is None else str(value))
    if not match:
        return None
    return Decimal(match.group(0).replace(",", "."))


def _parse_dates(value) -> list[date]:
    found = []
    raw = "" if value is None else str(value)
    for token in re.findall(r"\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}", raw):
        try:
            if "-" in token:
                found.append(date.fromisoformat(token))
            else:
                day, month, year = token.split("/")
                found.append(date(int(year), int(month), int(day)))
        except ValueError:
            continue
    return found


def _period_label(start: date | None, end: date | None) -> str | None:
    if start is None and end is None:
        return None
    if end is None:
        return start.isoformat()
    if start is None:
        return end.isoformat()
    return f"{start.isoformat()} a {end.isoformat()}"


def _text(value) -> str | None:
    if value is None or value == "":
        return None
    return str(value)
