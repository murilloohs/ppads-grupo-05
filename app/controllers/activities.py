from datetime import datetime
from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload
import os
import shutil
import hashlib
from uuid import uuid4

from app.core.config import settings
from app.database.session import get_db
from app.api.deps import get_current_student, get_current_user
from app.models.user import User
from app.models.activity import ComplementaryActivity
from app.models.document import CertificateDocument
from app.models.enums import SubmissionStatus
from app.models.submission import Submission
from app.schemas.activity import ActivityCreate, ActivityRead


router = APIRouter(prefix="/activities", tags=["Atividades Complementares"])

@router.post("/", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(activity_in: ActivityCreate, db: Session = Depends(get_db), current_student: User = Depends(get_current_student)):
    new_activity = ComplementaryActivity(
        student_id=current_student.id,
        title=activity_in.title,
        category=activity_in.category,
        provider_name=activity_in.provider_name,
        start_date=activity_in.start_date,
        end_date=activity_in.end_date,
        declared_hours=activity_in.declared_hours,
        description=activity_in.description
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
    current_student: User = Depends(get_current_student)
):
    activity = db.query(ComplementaryActivity).filter(
        ComplementaryActivity.id == activity_id,
        ComplementaryActivity.student_id == current_student.id
    ).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Atividade não encontrada ou acesso negado.")

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400, 
            detail="Formato inválido. Apenas PDF, JPG e PNG são permitidos."
        )
    
    file_extension = os.path.splitext(file.filename)[1]
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
                raise HTTPException(status_code=413, detail="Ficheiro excede o tamanho máximo permitido.")
    
    db_document = CertificateDocument(
        activity_id=activity.id,
        original_name=file.filename,
        stored_name=stored_name,
        mime_type=file.content_type,
        size_bytes=file_size,
        storage_path=file_path,
        sha256=sha256_hash.hexdigest()
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return {
        "message": "Ficheiro enviado com sucesso.",
        "document_id": db_document.id,
        "original_name": db_document.original_name
    }


@router.post("/{activity_id}/submit", status_code=status.HTTP_201_CREATED)
def submit_activity(activity_id: int, db: Session = Depends(get_db), current_student: User = Depends(get_current_student)):
    activity = db.query(ComplementaryActivity).filter(
        ComplementaryActivity.id == activity_id,
        ComplementaryActivity.student_id == current_student.id
    ).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")

    document = db.query(CertificateDocument).filter(CertificateDocument.activity_id == activity.id).first()
    if not document:
        raise HTTPException(status_code=400, detail="É obrigatório anexar um documento antes de enviar a solicitação.")

    existing_submission = db.query(Submission).filter(Submission.activity_id == activity.id).first()
    if existing_submission:
        raise HTTPException(status_code=400, detail="Esta atividade já foi submetida.")

    protocol_str = f"VAL-{datetime.now().year}-{uuid4().hex[:6].upper()}"

    new_submission = Submission(
        protocol=protocol_str,
        student_id=current_student.id,
        activity_id=activity.id,
        status=SubmissionStatus.SUBMITTED
    )

    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    return {
        "message": "Solicitação enviada com sucesso!",
        "protocol": new_submission.protocol,
        "status": new_submission.status.value if hasattr(new_submission.status, 'value') else new_submission.status
    }


@router.get("/")
def get_user_activities(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    activities = db.query(ComplementaryActivity).options(
        joinedload(ComplementaryActivity.submissions)
    ).filter(
        ComplementaryActivity.student_id == current_user.id
    ).all()
    
    result = []
    for act in activities:
        submission = act.submissions[0] if act.submissions else None
        
        status_text = "Rascunho"
        
        if submission:
            status_value = str(submission.status)
            
            if status_value in [SubmissionStatus.SUBMITTED, SubmissionStatus.PROCESSING, SubmissionStatus.PENDING_REVIEW]:
                status_text = "Em análise"
            elif status_value == SubmissionStatus.APPROVED:
                status_text = "Aprovada"
            elif status_value in [SubmissionStatus.REJECTED, SubmissionStatus.CORRECTION_REQUESTED]:
                status_text = "Correções"
        
        result.append({
            "id": act.id,
            "title": act.title,
            "declared_hours": act.declared_hours,
            "protocol": submission.protocol if submission else f"ID-{act.id}",
            "status": status_text
        })
        
    return result