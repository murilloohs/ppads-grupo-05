import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_student
from app.core.config import settings
from app.database.session import get_db
from app.models.activity import ComplementaryActivity
from app.models.document import CertificateDocument
from app.models.enums import AnalysisResult, ReviewDecision, SubmissionStatus
from app.models.submission import Submission
from app.models.user import User
from app.repositories.submission_repository import SubmissionRepository
from app.schemas.activity import ActivityCreate, ActivityDetail, ActivityRead, StatusChangeRead
from app.services.document_service import validate_content, verified_path
from app.services.submission_service import SubmissionService

router = APIRouter(prefix="/activities", tags=["Atividades Complementares"])

_ANALYSIS_RESULTS = {
    AnalysisResult.APPROVED: "Aprovada na análise automática",
    AnalysisResult.MANUAL_REVIEW: "Encaminhada para análise manual",
    AnalysisResult.FAILED: "Análise automática sem conclusão",
}
_REVIEW_RESULTS = {
    ReviewDecision.APPROVED: "Aprovada",
    ReviewDecision.REJECTED: "Reprovada",
    ReviewDecision.CORRECTION_REQUESTED: "Correções solicitadas",
}


def status_label(status: SubmissionStatus | None) -> str:
    if status in {
        SubmissionStatus.SUBMITTED,
        SubmissionStatus.PROCESSING,
        SubmissionStatus.PENDING_REVIEW,
    }:
        return "Em análise"
    if status == SubmissionStatus.APPROVED:
        return "Aprovada"
    if status == SubmissionStatus.REJECTED:
        return "Reprovada"
    if status == SubmissionStatus.CORRECTION_REQUESTED:
        return "Correções"
    return "Rascunho"


def latest_submission(activity: ComplementaryActivity) -> Submission | None:
    if not activity.submissions:
        return None
    return max(activity.submissions, key=lambda item: item.id)


def result_label(submission: Submission | None) -> str:
    if submission is None:
        return "Sem resultado"
    if submission.manual_reviews:
        review = max(submission.manual_reviews, key=lambda item: item.id)
        return _REVIEW_RESULTS.get(review.decision, "Aguardando resultado")
    if submission.automatic_analysis:
        return _ANALYSIS_RESULTS.get(submission.automatic_analysis.result, "Aguardando resultado")
    return "Aguardando resultado"


def latest_justification(submission: Submission | None) -> str | None:
    if submission is None or not submission.manual_reviews:
        return None
    review = max(submission.manual_reviews, key=lambda item: item.id)
    text = (review.justification or "").strip()
    return text or None


def history_items(submission: Submission | None) -> list[StatusChangeRead]:
    if submission is None:
        return []
    ordered = sorted(submission.history, key=lambda item: (item.created_at, item.id))
    return [
        StatusChangeRead(
            status=status_label(item.status), note=item.note, changed_at=item.created_at
        )
        for item in ordered
    ]


@router.post("/", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity_in: ActivityCreate,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
):
    new_activity = ComplementaryActivity(
        student_id=current_student.id,
        title=activity_in.title,
        category=activity_in.category,
        provider_name=activity_in.provider_name,
        start_date=activity_in.start_date,
        end_date=activity_in.end_date,
        declared_hours=activity_in.declared_hours,
        description=activity_in.description,
    )

    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)

    return new_activity


ALLOWED_MIME_TYPES = ["application/pdf", "image/jpeg", "image/png"]


@router.post("/{activity_id}/documents", status_code=status.HTTP_201_CREATED)
def upload_certificate(
    activity_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
):
    activity = SubmissionRepository(db).owned_activity(activity_id, current_student.id)
    if not activity:
        raise HTTPException(404, "Atividade não encontrada.")
    previous = latest_submission(activity)
    if previous and previous.status != SubmissionStatus.CORRECTION_REQUESTED:
        raise HTTPException(409, "O envio está fechado. Aguarde uma solicitação de correção.")
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, "Formato inválido. Apenas PDF, JPG e PNG são permitidos.")
    limit = settings.max_upload_size_mb * 1024 * 1024
    content = file.file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(413, "Arquivo excede o tamanho máximo permitido.")
    validate_content(content, file.content_type)
    digest = hashlib.sha256(content).hexdigest()
    duplicate = (
        db.query(CertificateDocument)
        .join(ComplementaryActivity)
        .filter(
            ComplementaryActivity.student_id == current_student.id,
            ComplementaryActivity.id != activity_id,
            CertificateDocument.sha256 == digest,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(409, "Este certificado já foi enviado em outra atividade sua.")
    extension = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}
    stored_name = uuid4().hex + extension[file.content_type]
    folder = Path(settings.upload_dir)
    folder.mkdir(parents=True, exist_ok=True)
    file_path = str(folder / stored_name)
    Path(file_path).write_bytes(content)
    file_size = len(content)

    db_document = CertificateDocument(
        activity_id=activity.id,
        original_name=file.filename,
        stored_name=stored_name,
        mime_type=file.content_type,
        size_bytes=file_size,
        storage_path=file_path,
        sha256=digest,
    )

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    return {
        "message": "Ficheiro enviado com sucesso.",
        "document_id": db_document.id,
        "original_name": db_document.original_name,
    }


@router.post("/{activity_id}/submit", status_code=status.HTTP_201_CREATED)
def submit_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
):
    service = SubmissionService(SubmissionRepository(db))
    return service.submit(activity_id, current_student.id)


@router.get("/")
def get_user_activities(
    current_user: User = Depends(get_current_student), db: Session = Depends(get_db)
):
    activities = (
        db.query(ComplementaryActivity)
        .options(joinedload(ComplementaryActivity.submissions))
        .filter(ComplementaryActivity.student_id == current_user.id)
        .all()
    )

    result = []
    for act in activities:
        submission = latest_submission(act)
        result.append(
            {
                "id": act.id,
                "title": act.title,
                "declared_hours": act.declared_hours,
                "protocol": submission.protocol if submission else f"ID-{act.id}",
                "status": status_label(submission.status if submission else None),
            }
        )

    return result


@router.get("/{activity_id}", response_model=ActivityDetail)
def get_activity_detail(
    activity_id: int,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ActivityDetail:
    activity = (
        db.query(ComplementaryActivity)
        .options(
            joinedload(ComplementaryActivity.submissions).joinedload(Submission.history),
            joinedload(ComplementaryActivity.submissions).joinedload(Submission.manual_reviews),
            joinedload(ComplementaryActivity.submissions).joinedload(Submission.automatic_analysis),
        )
        .filter(
            ComplementaryActivity.id == activity_id,
            ComplementaryActivity.student_id == current_user.id,
        )
        .first()
    )
    if not activity:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")

    submission = latest_submission(activity)
    return ActivityDetail(
        id=activity.id,
        protocol=submission.protocol if submission else f"ID-{activity.id}",
        title=activity.title,
        category=activity.category,
        provider_name=activity.provider_name,
        start_date=activity.start_date,
        end_date=activity.end_date,
        declared_hours=activity.declared_hours,
        description=activity.description,
        status=status_label(submission.status if submission else None),
        result=result_label(submission),
        justification=latest_justification(submission),
        certificates=[
            {"id": item.id, "original_name": item.original_name}
            for item in (
                [submission.document] if submission and submission.document else activity.documents
            )
        ],
        history=sorted(
            [event for item in activity.submissions for event in history_items(item)],
            key=lambda item: item.changed_at,
        ),
    )


@router.put("/{activity_id}", response_model=ActivityRead)
def correct_activity(
    activity_id: int,
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_student),
):
    activity = SubmissionRepository(db).owned_activity(activity_id, student.id)
    if activity is None:
        raise HTTPException(404, "Atividade não encontrada.")
    previous = latest_submission(activity)
    if previous and previous.status != SubmissionStatus.CORRECTION_REQUESTED:
        raise HTTPException(409, "Somente rascunhos ou correções podem ser editados.")
    for key, value in payload.model_dump().items():
        setattr(activity, key, value)
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/{activity_id}/documents/{document_id}")
def student_certificate(
    activity_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_student),
):
    activity = SubmissionRepository(db).owned_activity(activity_id, student.id)
    if activity is None:
        raise HTTPException(404, "Atividade não encontrada.")
    document = next((item for item in activity.documents if item.id == document_id), None)
    if document is None:
        raise HTTPException(404, "Certificado não encontrado.")
    return FileResponse(
        verified_path(document), media_type=document.mime_type, filename=document.original_name
    )
