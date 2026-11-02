from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.database.session import engine, get_db
from app.main import app
from app.models.analysis import AutomaticAnalysis
from app.models.document import CertificateDocument
from app.models.enums import AnalysisResult, ReviewDecision, SubmissionStatus, UserRole
from app.models.history import StatusHistory
from app.models.institution import Institution
from app.models.review import ManualReview
from app.models.rule import ValidationRule
from app.models.submission import Submission
from app.models.user import User


@pytest.fixture
def scenario(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection, join_transaction_mode="create_savepoint")
    inst = Institution(name=f"A3 test {uuid4().hex}", active=True)
    db.add(inst)
    db.flush()
    users = []
    for role in [UserRole.STUDENT, UserRole.STUDENT, UserRole.EVALUATOR]:
        user = User(
            institution_id=inst.id,
            name="Teste A3",
            email=f"{uuid4().hex}@test.local",
            password_hash=security.get_password_hash("test-pass"),
            role=role,
            active=True,
        )
        db.add(user)
        db.flush()
        users.append(user)
    db.commit()
    app.dependency_overrides[get_db] = lambda: db
    headers = [
        {"Authorization": "Bearer " + security.create_access_token(str(u.id), u.email, u.role)}
        for u in users
    ]
    try:
        with TestClient(app) as client:
            yield client, db, headers, users
    finally:
        app.dependency_overrides.clear()
        db.close()
        transaction.rollback()
        connection.close()


def payload(**kwargs):
    return dict(
        title="Curso demonstração",
        category="Curso",
        provider_name="Instituição Demo",
        start_date="2026-09-01",
        end_date="2026-09-02",
        declared_hours="1.50",
        **kwargs,
    )


def test_submission_requires_document_and_records_history(scenario):
    client, db, headers, _ = scenario
    response = client.post("/api/v1/activities/", json=payload(), headers=headers[0])
    assert response.status_code == 201
    assert Decimal(response.json()["declared_hours"]) == Decimal("1.50")
    activity_id = response.json()["id"]
    url = f"/api/v1/activities/{activity_id}"
    assert client.post(url + "/submit", headers=headers[0]).status_code == 400
    assert (
        client.post(
            url + "/documents",
            headers=headers[1],
            files={"file": ("demo.pdf", b"%PDF-demo", "application/pdf")},
        ).status_code
        == 404
    )
    assert (
        client.post(
            url + "/documents",
            headers=headers[0],
            files={"file": ("demo.txt", b"demo", "text/plain")},
        ).status_code
        == 400
    )
    assert (
        client.post(
            url + "/documents",
            headers=headers[0],
            files={"file": ("demo.pdf", b"%PDF-demo", "application/pdf")},
        ).status_code
        == 201
    )
    submitted = client.post(url + "/submit", headers=headers[0])
    assert submitted.status_code == 201
    assert submitted.json()["protocol"].startswith("VAL-")
    assert client.post(url + "/submit", headers=headers[0]).status_code == 400
    assert client.post(url + "/submit", headers=headers[1]).status_code == 404
    rows = client.get("/api/v1/activities/", headers=headers[0]).json()
    row = next(r for r in rows if r["id"] == activity_id)
    assert row["status"] == "Em análise"
    assert row["protocol"] == submitted.json()["protocol"]
    assert client.get("/api/v1/activities/", headers=headers[1]).json() == []
    history = db.scalars(select(StatusHistory).where(StatusHistory.changed_by_id == _[0].id)).all()
    assert len(history) == 1


def test_student_sees_only_own_request_detail(scenario):
    client, db, headers, users = scenario
    created = client.post("/api/v1/activities/", json=payload(), headers=headers[0])
    activity_id = created.json()["id"]
    url = f"/api/v1/activities/{activity_id}"
    assert client.get(url, headers=headers[1]).status_code == 404
    assert client.get(url, headers=headers[2]).status_code == 403
    assert (
        client.post(
            url + "/documents",
            headers=headers[0],
            files={"file": ("demo.pdf", b"%PDF-demo", "application/pdf")},
        ).status_code
        == 201
    )
    submitted = client.post(url + "/submit", headers=headers[0])
    detail = client.get(url, headers=headers[0])
    assert detail.status_code == 200
    body = detail.json()
    assert body["protocol"] == submitted.json()["protocol"]
    assert body["status"] == "Em análise"
    assert body["result"] == "Aguardando resultado"
    assert body["justification"] is None
    assert len(body["history"]) == 1
    submission = db.scalar(select(Submission).where(Submission.activity_id == activity_id))
    submission.status = SubmissionStatus.APPROVED
    db.add(
        StatusHistory(
            submission_id=submission.id,
            status=SubmissionStatus.APPROVED,
            changed_by_id=users[2].id,
            note="Avaliação concluída.",
        )
    )
    db.add(
        ManualReview(
            submission_id=submission.id,
            evaluator_id=users[2].id,
            decision=ReviewDecision.APPROVED,
            justification="O certificado confere.",
        )
    )
    db.commit()
    updated = client.get(url, headers=headers[0]).json()
    assert updated["status"] == "Aprovada"
    assert updated["result"] == "Aprovada"
    assert updated["justification"] == "O certificado confere."
    assert [item["status"] for item in updated["history"]] == ["Em análise", "Aprovada"]
    listed = client.get("/api/v1/activities/", headers=headers[0]).json()
    assert next(row for row in listed if row["id"] == activity_id)["status"] == "Aprovada"
    assert client.get(url, headers=headers[1]).status_code == 404


def test_admin_creates_and_updates_rules(scenario):
    client, db, headers, users = scenario
    admin = User(
        institution_id=users[0].institution_id,
        name="Admin A3",
        email=f"{uuid4().hex}@test.local",
        password_hash=security.get_password_hash("test-pass"),
        role=UserRole.ADMIN,
        active=True,
    )
    db.add(admin)
    db.commit()
    token = security.create_access_token(str(admin.id), admin.email, admin.role)
    admin_headers = {"Authorization": f"Bearer {token}"}
    body = {
        "category": "Curso de extensão",
        "valid_from": "2026-01-01",
        "valid_until": "2026-12-31",
        "max_hours": "40.50",
        "accepted_document_types": ["pdf", "jpeg"],
        "confidence_threshold": 0.9,
        "allows_auto_approval": True,
    }
    assert client.get("/api/v1/rules", headers=headers[0]).status_code == 403
    created = client.post("/api/v1/rules", json=body, headers=admin_headers)
    assert created.status_code == 201
    created_body = created.json()
    assert created_body["accepted_document_types"] == ["PDF", "JPG"]
    assert created_body["allows_auto_approval"] is True
    assert client.post("/api/v1/rules", json=body, headers=admin_headers).status_code == 409
    listed = client.get("/api/v1/rules", headers=admin_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["category"] == "Curso de extensão"
    updated = client.put(
        f"/api/v1/rules/{created_body['id']}",
        json={**body, "allows_auto_approval": False, "max_hours": None, "valid_until": None},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["allows_auto_approval"] is False
    assert updated.json()["max_hours"] is None
    assert updated.json()["valid_until"] is None
    invalid = {**body, "category": "Outra categoria", "valid_until": "2025-01-01"}
    assert client.post("/api/v1/rules", json=invalid, headers=admin_headers).status_code == 422


def test_auth_roles_and_invalid_input(scenario):
    client, _, headers, users = scenario
    assert (
        client.post(
            "/api/v1/auth/login", data={"username": users[0].email, "password": "test-pass"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/auth/login", data={"username": users[0].email, "password": "wrong"}
        ).status_code
        == 401
    )
    assert client.get("/api/v1/activities/").status_code == 401
    assert client.post("/api/v1/activities/", json=payload(), headers=headers[2]).status_code == 403
    for patch in [{"declared_hours": 0}, {"title": "  "}, {"end_date": "2026-08-01"}]:
        body = payload()
        body.update(patch)
        assert client.post("/api/v1/activities/", json=body, headers=headers[0]).status_code == 422


def test_evaluator_queue_shows_only_pending_reviews(scenario):
    client, db, headers, users = scenario
    created = client.post("/api/v1/activities/", json=payload(), headers=headers[0])
    activity_id = created.json()["id"]
    url = f"/api/v1/activities/{activity_id}"
    assert (
        client.post(
            url + "/documents",
            headers=headers[0],
            files={"file": ("demo.pdf", b"%PDF-demo", "application/pdf")},
        ).status_code
        == 201
    )
    client.post(url + "/submit", headers=headers[0])
    assert client.get("/api/v1/reviews", headers=headers[2]).json() == []
    assert client.get("/api/v1/reviews", headers=headers[0]).status_code == 403
    submission = db.scalar(select(Submission).where(Submission.activity_id == activity_id))
    document = db.scalar(
        select(CertificateDocument).where(CertificateDocument.activity_id == activity_id)
    )
    rule = ValidationRule(
        institution_id=users[0].institution_id,
        category="Curso de extensão",
        version=1,
        valid_from=date(2026, 1, 1),
        max_hours=Decimal("40.00"),
        accepted_document_types=["PDF"],
        confidence_threshold=0.85,
        allows_auto_approval=False,
        active=True,
    )
    db.add(rule)
    db.flush()
    document.ocr_text = "Certificado de curso de extensão"
    document.extracted_data = {"titulo": "Curso de extensão", "carga_horaria": "40"}
    submission.status = SubmissionStatus.PENDING_REVIEW
    submission.validation_rule_id = rule.id
    db.add(
        AutomaticAnalysis(
            submission_id=submission.id,
            result=AnalysisResult.MANUAL_REVIEW,
            confidence=0.62,
            explanation="A carga horária não ficou clara.",
        )
    )
    other = Institution(name=f"Outra {uuid4().hex}", active=True)
    db.add(other)
    db.flush()
    outsider = User(
        institution_id=other.id,
        name="Avaliador externo",
        email=f"{uuid4().hex}@test.local",
        password_hash=security.get_password_hash("test-pass"),
        role=UserRole.EVALUATOR,
        active=True,
    )
    db.add(outsider)
    db.commit()
    outsider_headers = {
        "Authorization": "Bearer "
        + security.create_access_token(str(outsider.id), outsider.email, outsider.role)
    }
    queued = client.get("/api/v1/reviews", headers=headers[2])
    assert queued.status_code == 200
    assert len(queued.json()) == 1
    assert queued.json()[0]["protocol"] == submission.protocol
    assert client.get("/api/v1/reviews", headers=outsider_headers).json() == []
    detail = client.get(f"/api/v1/reviews/{submission.id}", headers=headers[2])
    assert detail.status_code == 200
    body = detail.json()
    assert body["activity"]["title"] == "Curso demonstração"
    assert body["certificates"][0]["extracted_data"]["titulo"] == "Curso de extensão"
    assert body["analysis"]["result"] == "Encaminhada para análise manual"
    assert body["rule"]["category"] == "Curso de extensão"
    certificate = client.get(
        f"/api/v1/reviews/{submission.id}/certificates/{document.id}", headers=headers[2]
    )
    assert certificate.status_code == 200
    assert certificate.content == b"%PDF-demo"
    hidden = client.get(f"/api/v1/reviews/{submission.id}", headers=outsider_headers)
    assert hidden.status_code == 404
    denied = client.get(f"/api/v1/reviews/{submission.id}", headers=headers[0])
    assert denied.status_code == 403
    submission.status = SubmissionStatus.APPROVED
    db.commit()
    assert client.get("/api/v1/reviews", headers=headers[2]).json() == []
    assert client.get(f"/api/v1/reviews/{submission.id}", headers=headers[2]).status_code == 404
