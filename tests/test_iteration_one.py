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
from app.models.enums import UserRole
from app.models.history import StatusHistory
from app.models.institution import Institution
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
