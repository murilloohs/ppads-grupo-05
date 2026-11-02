import hashlib
import os
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
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
    activity = (
        db.query(ComplementaryActivity)
        .filter(
            ComplementaryActivity.id == activity_id,
            ComplementaryActivity.student_id == current_student.id,
        )
        .first()
    )

    if not activity:
        raise HTTPException(status_code=404, detail="Atividade não encontrada ou acesso negado.")

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400, detail="Formato inválido. Apenas PDF, JPG e PNG são permitidos."
        )

    file_extension = os.path.splitext((file.filename or "documento"))[1]
    stored_name = f"{uuid4().hex}{file_extension}"
    file_path = os.path.join(settings.upload_dir, stored_name)

    sha256_hash = hashlib.sha256()
    file_size = 0

    with open(file_path, "wb") as buffer:
        while chunk := file.file.read(8192):
            sha256_hash.update(chunk)
            buffer.write(chunk)
            file_size += len(chunk)

            if file_size > (settings.max_upload_size_mb * 1024 * 1024):
                os.remove(file_path)
                raise HTTPException(
                    status_code=413, detail="Ficheiro excede o tamanho máximo permitido."
                )

    db_document = CertificateDocument(
        activity_id=activity.id,
        original_name=file.filename,
        stored_name=stored_name,
        mime_type=file.content_type,
        size_bytes=file_size,
        storage_path=file_path,
        sha256=sha256_hash.hexdigest(),
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
        history=history_items(submission),
    )
