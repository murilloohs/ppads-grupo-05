from decimal import Decimal

from sqlalchemy import select

from app.core import security
from app.models.document import CertificateDocument
from app.models.enums import UserRole
from app.models.rule import ValidationRule
from app.models.submission import Submission
from app.models.user import User
from tests.test_iteration_one import payload, valid_pdf


def send(client, headers, title="Curso demonstração"):
    body = payload()
    body["title"] = title
    activity_id = client.post("/api/v1/activities/", json=body, headers=headers).json()["id"]
    url = f"/api/v1/activities/{activity_id}"
    response = client.post(
        url + "/documents",
        headers=headers,
        files={"file": ("teste.pdf", valid_pdf(title), "application/pdf")},
    )
    assert response.status_code == 201
    result = client.post(url + "/submit", headers=headers)
    assert result.status_code == 201
    return activity_id, url, response.json()["document_id"]


def test_correction_resubmission_preserves_evidence(scenario):
    client, db, headers, _ = scenario
    activity_id, url, document_id = send(client, headers[0])
    first = db.scalar(select(Submission).where(Submission.activity_id == activity_id))
    assert client.put(url, json=payload(), headers=headers[0]).status_code == 409
    assert (
        client.post(
            url + "/documents",
            headers=headers[0],
            files={"file": ("test.pdf", valid_pdf(), "application/pdf")},
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/v1/reviews/{first.id}/decision",
            headers=headers[2],
            json={"decision": "correction_requested", "justification": "Ajuste a carga."},
        ).status_code
        == 201
    )
    corrected = payload()
    corrected["declared_hours"] = "2.50"
    assert client.put(url, json=corrected, headers=headers[0]).status_code == 200
    assert (
        client.post(
            url + "/documents",
            headers=headers[0],
            files={"file": ("corrigido.pdf", valid_pdf("Novo certificado"), "application/pdf")},
        ).status_code
        == 201
    )
    assert client.post(url + "/submit", headers=headers[0]).status_code == 201
    db.refresh(first)
    assert first.document_id == document_id
    assert Decimal(first.activity_snapshot["declared_hours"]) == Decimal("1.50")
    detail = client.get(url, headers=headers[0]).json()
    assert len(detail["history"]) == 3
    assert detail["protocol"] != first.protocol
    assert client.get(url, headers=headers[1]).status_code == 404
    assert client.get(url + f"/documents/{document_id}", headers=headers[1]).status_code == 404
    assert client.get(url + f"/documents/{document_id}", headers=headers[0]).status_code == 200


def test_rule_versions_and_stale_edit(scenario):
    client, db, _, users = scenario
    admin = User(
        institution_id=users[0].institution_id,
        name="Administrador",
        email="admin-version@test.local",
        role=UserRole.ADMIN,
        password_hash=security.get_password_hash("test-pass"),
        active=True,
    )
    db.add(admin)
    db.commit()
    headers = {
        "Authorization": "Bearer "
        + security.create_access_token(str(admin.id), admin.email, admin.role)
    }
    body = {
        "category": "Curso",
        "valid_from": "2026-01-01",
        "max_hours": "40",
        "accepted_document_types": ["PDF"],
        "confidence_threshold": 0.85,
        "allows_auto_approval": False,
    }
    original = client.post("/api/v1/rules", json=body, headers=headers).json()
    changed = client.put(
        f"/api/v1/rules/{original['id']}", json={**body, "max_hours": "20"}, headers=headers
    )
    assert changed.status_code == 200
    assert changed.json()["version"] == 2
    db.expire_all()
    assert db.get(ValidationRule, original["id"]).max_hours == Decimal("40")
    assert (
        client.put(f"/api/v1/rules/{original['id']}", json=body, headers=headers).status_code == 409
    )
    assert len(client.get("/api/v1/rules", headers=headers).json()) == 1
    assert len(client.get(f"/api/v1/rules/{original['id']}/versions", headers=headers).json()) == 2
    assert (
        client.post(
            "/api/v1/rules", json={**body, "category": "curso"}, headers=headers
        ).status_code
        == 409
    )


def test_upload_integrity_duplicate_and_closed_decision(scenario):
    client, db, headers, _ = scenario
    for content in [b"", b"%PDF-invalid", b"not an image"]:
        activity = client.post("/api/v1/activities/", json=payload(), headers=headers[0]).json()[
            "id"
        ]
        assert (
            client.post(
                f"/api/v1/activities/{activity}/documents",
                headers=headers[0],
                files={"file": ("fake.pdf", content, "application/pdf")},
            ).status_code
            == 400
        )
    activity, url, document_id = send(client, headers[0], title="Arquivo unico")
    other = client.post("/api/v1/activities/", json=payload(), headers=headers[0]).json()["id"]
    doc = db.get(CertificateDocument, document_id)
    from pathlib import Path

    assert (
        client.post(
            f"/api/v1/activities/{other}/documents",
            headers=headers[0],
            files={"file": ("dup.pdf", Path(doc.storage_path).read_bytes(), "application/pdf")},
        ).status_code
        == 409
    )
    submission = db.scalar(select(Submission).where(Submission.activity_id == activity))
    decision = f"/api/v1/reviews/{submission.id}/decision"
    assert (
        client.post(
            decision, headers=headers[2], json={"decision": "approved", "justification": "OK"}
        ).status_code
        == 201
    )
    assert (
        client.post(
            decision, headers=headers[2], json={"decision": "rejected", "justification": "Outra"}
        ).status_code
        == 409
    )
    Path(doc.storage_path).write_bytes(b"tampered")
    assert client.get(url + f"/documents/{document_id}", headers=headers[0]).status_code == 409
