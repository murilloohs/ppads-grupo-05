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
    assert body["result"] == "Encaminhada para análise manual"
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
    submitted = client.post(url + "/submit", headers=headers[0])
    assert submitted.status_code == 201
    assert submitted.json()["leitura"]["ok"] is False
    assert len(client.get("/api/v1/reviews", headers=headers[2]).json()) == 1
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
    analysis = db.scalar(
        select(AutomaticAnalysis).where(AutomaticAnalysis.submission_id == submission.id)
    )
    analysis.result = AnalysisResult.MANUAL_REVIEW
    analysis.confidence = 0.62
    analysis.explanation = "A carga horária não ficou clara."
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


def test_ocr_extracts_certificate_fields():
    from app.services.ocr_service import extract_certificate_fields

    fields = extract_certificate_fields(
        "Nome: Maria Silva\n"
        "Atividade: Curso de extensao\n"
        "Instituicao: Mackenzie\n"
        "Periodo: 01/09/2026 a 02/09/2026\n"
        "Carga horaria: 40 horas\n"
    )
    assert fields["Nome"] == "Maria Silva"
    assert fields["Atividade"] == "Curso de extensao"
    assert fields["Instituição"] == "Mackenzie"
    assert fields["Data/período"] == "01/09/2026 a 02/09/2026"
    assert fields["Carga horária"] == "40"
    single_line = extract_certificate_fields(
        "Nome: Ana Souza Atividade: Curso de extensao Instituicao: Mackenzie "
        "Periodo: 01/03/2026 a 30/03/2026 Carga horaria: 20 horas"
    )
    assert single_line == {
        "Nome": "Ana Souza",
        "Atividade": "Curso de extensao",
        "Instituição": "Mackenzie",
        "Data/período": "01/03/2026 a 30/03/2026",
        "Carga horária": "20",
    }
    prose = extract_certificate_fields(
        "Certificamos que Ana Souza participou da atividade Curso de Inteligencia Artificial, "
        "promovida pela instituicao Universidade Mackenzie, no periodo de 01/03/2026 a 30/03/2026, "
        "com carga horaria de 20 horas. Duracao complementar de 2 horas."
    )
    assert prose["Nome"] == "Ana Souza"
    assert prose["Atividade"] == "Curso de Inteligencia Artificial"
    assert prose["Instituição"] == "Universidade Mackenzie"
    assert prose["Data/período"] == "01/03/2026 a 30/03/2026"
    assert prose["Carga horária"] == "20"
    conclusion = extract_certificate_fields(
        "Certificado de Conclusão\n"
        "Curso Fundamentos da Linguagem PHP\n"
        "Murillo Henrique Santos\n"
        "Concluiu com êxito o curso de Fundamentos da Linguagem PHP da Trybe, "
        "com carga horária de 20 horas.\n"
        "Data de conclusão:\n"
        "27/09/2026\n"
        "27/09/2026\n"
    )
    assert conclusion["Nome"] == "Murillo Henrique Santos"
    assert conclusion["Atividade"] == "Fundamentos da Linguagem PHP"
    assert conclusion["Instituição"] == "Trybe"
    assert conclusion["Data/período"] == "27/09/2026"
    assert conclusion["Carga horária"] == "20"


def test_single_conclusion_date_matches_declared_end():
    from app.services.analysis_service import _period_check

    matched = _period_check(date(2026, 9, 1), date(2026, 9, 27), "27/09/2026")
    assert matched["situacao"] == "confere"
    shifted = _period_check(date(2026, 9, 1), date(2026, 9, 30), "27/09/2026")
    assert shifted["situacao"] == "diverge"


def test_image_certificate_reads_text_behind_the_template(tmp_path, monkeypatch):
    import fitz
    import pytesseract
    from PIL import Image

    from app.services.ocr_service import CertificateOcrService

    image = Image.new("RGB", (800, 600), "white")
    picture = tmp_path / "pagina.png"
    image.save(picture)
    document = fitz.open()
    page = document.new_page(width=800, height=600)
    page.insert_image(page.rect, filename=str(picture))
    page.insert_text((72, 80), "Murillo Henrique Santos")
    page.insert_text((72, 520), "27/09/2026")
    certificate = tmp_path / "certificado.pdf"
    document.save(certificate)
    document.close()

    def fake_ocr(_image, lang="por"):
        assert lang
        return (
            "Curso Fundamentos da Linguagem PHP\n"
            "Murillo Henrique Santos\n"
            "Concluiu com êxito o curso de Fundamentos da Linguagem PHP da Trybe, "
            "com carga horária de 20 horas.\n"
            "27/09/2026\n"
        )

    monkeypatch.setattr(pytesseract, "image_to_string", fake_ocr)
    reading = CertificateOcrService().read(str(certificate), "application/pdf")
    assert reading.ok is True
    assert reading.fields["Nome"] == "Murillo Henrique Santos"
    assert reading.fields["Atividade"] == "Fundamentos da Linguagem PHP"
    assert reading.fields["Instituição"] == "Trybe"
    assert reading.fields["Carga horária"] == "20"
    assert reading.fields["Data/período"] == "27/09/2026"


def test_submit_keeps_ocr_data_and_routes_unreadable_files(scenario, tmp_path):
    import fitz

    from app.services.ocr_service import CertificateOcrService

    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"%PDF-demo")
    assert CertificateOcrService().read(str(broken), "application/pdf").ok is False

    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(
        fitz.Rect(72, 72, 520, 420),
        "Nome: Maria Silva\n"
        "Atividade: Curso de extensao\n"
        "Instituicao: Mackenzie\n"
        "Periodo: 01/09/2026 a 02/09/2026\n"
        "Carga horaria: 40 horas",
    )
    certificate = tmp_path / "certificado.pdf"
    document.save(certificate)
    document.close()

    client, _, headers, _ = scenario
    created = client.post("/api/v1/activities/", json=payload(), headers=headers[0])
    activity_id = created.json()["id"]
    url = f"/api/v1/activities/{activity_id}"
    with certificate.open("rb") as handle:
        uploaded = client.post(
            url + "/documents",
            headers=headers[0],
            files={"file": ("certificado.pdf", handle, "application/pdf")},
        )
    assert uploaded.status_code == 201
    submitted = client.post(url + "/submit", headers=headers[0])
    assert submitted.status_code == 201
    body = submitted.json()
    assert body["status"] == "pending_review"
    assert body["leitura"]["ok"] is True
    assert body["leitura"]["dados"]["Nome"] == "Maria Silva"
    assert body["leitura"]["dados"]["Atividade"] == "Curso de extensao"
    assert body["leitura"]["dados"]["Instituição"] == "Mackenzie"
    assert body["leitura"]["dados"]["Carga horária"] == "40"
    assert body["analise"]["resultado"] == "manual_review"
    assert len(client.get("/api/v1/reviews", headers=headers[2]).json()) == 1


def test_analysis_approves_match_and_flags_divergence(scenario, tmp_path):
    import fitz

    from app.models.analysis import AutomaticAnalysis

    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(
        fitz.Rect(72, 72, 520, 420),
        "Nome: Maria Silva\n"
        "Atividade: Curso de extensao\n"
        "Instituicao: Mackenzie\n"
        "Periodo: 01/09/2026 a 02/09/2026\n"
        "Carga horaria: 40 horas",
    )
    certificate = tmp_path / "certificado.pdf"
    document.save(certificate)
    document.close()
    content = certificate.read_bytes()

    client, db, headers, users = scenario
    users[0].name = "Maria Silva"
    rule = ValidationRule(
        institution_id=users[0].institution_id,
        category="Curso de extensão",
        version=1,
        valid_from=date(2026, 1, 1),
        valid_until=date(2026, 12, 31),
        max_hours=Decimal("40.00"),
        accepted_document_types=["PDF"],
        confidence_threshold=0.85,
        allows_auto_approval=True,
        active=True,
    )
    db.add(rule)
    db.commit()

    def send(hours):
        body = payload()
        body.update(
            title="Curso de extensao",
            category="Curso de extensao",
            provider_name="Mackenzie",
            start_date="2026-09-01",
            end_date="2026-09-02",
            declared_hours=hours,
        )
        created = client.post("/api/v1/activities/", json=body, headers=headers[0])
        activity_id = created.json()["id"]
        url = f"/api/v1/activities/{activity_id}"
        uploaded = client.post(
            url + "/documents",
            headers=headers[0],
            files={"file": ("certificado.pdf", content, "application/pdf")},
        )
        assert uploaded.status_code == 201
        return client.post(url + "/submit", headers=headers[0])

    approved = send("40")
    assert approved.status_code == 201
    assert approved.json()["status"] == "approved"
    assert approved.json()["analise"]["resultado"] == "approved"
    saved = db.scalar(
        select(AutomaticAnalysis).where(
            AutomaticAnalysis.explanation == approved.json()["analise"]["explicacao"]
        )
    )
    assert saved is not None
    assert saved.result == AnalysisResult.APPROVED
    assert client.get("/api/v1/reviews", headers=headers[2]).json() == []

    divergent = send("20")
    assert divergent.status_code == 201
    assert divergent.json()["status"] == "pending_review"
    assert divergent.json()["analise"]["resultado"] == "manual_review"
    assert "carga horária" in divergent.json()["analise"]["explicacao"].lower()
    queued = client.get("/api/v1/reviews", headers=headers[2]).json()
    assert len(queued) == 1
    assert queued[0]["protocol"] == divergent.json()["protocol"]
    review = client.get(f"/api/v1/reviews/{queued[0]['id']}", headers=headers[2]).json()
    extracted = review["certificates"][0]["extracted_data"]
    assert extracted["Nome"] == "Maria Silva"
    assert extracted["Atividade"] == "Curso de extensao"
    assert extracted["Instituição"] == "Mackenzie"
    assert extracted["Carga horária"] == "40"
    compared = {item["campo"]: item for item in review["analysis"]["comparisons"]}
    assert compared["Atividade"]["referencia"] == "Curso de extensao"
    assert compared["Atividade"]["situacao"] == "confere"
    assert compared["Carga horária"]["referencia"] == "40"
    assert compared["Carga horária"]["situacao"] == "diverge"


def test_evaluator_approves_or_rejects_pending_request(scenario):
    client, _, headers, _ = scenario
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
    submitted = client.post(url + "/submit", headers=headers[0])
    submission_id = client.get("/api/v1/reviews", headers=headers[2]).json()[0]["id"]
    assert client.post(
        f"/api/v1/reviews/{submission_id}/decision",
        json={"decision": "approved", "justification": "  "},
        headers=headers[2],
    ).status_code == 422
    assert (
        client.post(
            f"/api/v1/reviews/{submission_id}/decision",
            json={"decision": "approved", "justification": "Documento confere."},
            headers=headers[0],
        ).status_code
        == 403
    )
    decision = client.post(
        f"/api/v1/reviews/{submission_id}/decision",
        json={"decision": "approved", "justification": "Documento confere."},
        headers=headers[2],
    )
    assert decision.status_code == 201
    assert decision.json()["status"] == "approved"
    assert client.get("/api/v1/reviews", headers=headers[2]).json() == []
    assert (
        client.post(
            f"/api/v1/reviews/{submission_id}/decision",
            json={"decision": "rejected", "justification": "Tarde demais."},
            headers=headers[2],
        ).status_code
        == 404
    )
    detail = client.get(url, headers=headers[0]).json()
    assert detail["status"] == "Aprovada"
    assert detail["justification"] == "Documento confere."
    assert detail["protocol"] == submitted.json()["protocol"]

    body = payload()
    body["title"] = "Outra atividade"
    second = client.post("/api/v1/activities/", json=body, headers=headers[0])
    second_url = f"/api/v1/activities/{second.json()['id']}"
    client.post(
        second_url + "/documents",
        headers=headers[0],
        files={"file": ("demo.pdf", b"%PDF-demo", "application/pdf")},
    )
    client.post(second_url + "/submit", headers=headers[0])
    rejected_id = client.get("/api/v1/reviews", headers=headers[2]).json()[0]["id"]
    rejected = client.post(
        f"/api/v1/reviews/{rejected_id}/decision",
        json={"decision": "rejected", "justification": "O certificado não confere."},
        headers=headers[2],
    )
    assert rejected.status_code == 201
    assert rejected.json()["status"] == "rejected"
    assert client.get(second_url, headers=headers[0]).json()["status"] == "Reprovada"
