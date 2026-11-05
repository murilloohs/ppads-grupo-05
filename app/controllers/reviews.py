from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_evaluator
from app.database.session import get_db
from app.models.user import User
from app.schemas.review_queue import (
    ReviewDecisionRead,
    ReviewDecisionWrite,
    ReviewDetail,
    ReviewQueueItem,
)
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Revisão manual"])


@router.get("", response_model=list[ReviewQueueItem])
def list_review_queue(
    db: Session = Depends(get_db),
    current_evaluator: User = Depends(get_current_evaluator),
) -> list[ReviewQueueItem]:
    return ReviewService(db).list_queue(current_evaluator)


@router.get("/{submission_id}", response_model=ReviewDetail)
def get_review_detail(
    submission_id: int,
    db: Session = Depends(get_db),
    current_evaluator: User = Depends(get_current_evaluator),
) -> ReviewDetail:
    return ReviewService(db).get_detail(submission_id, current_evaluator)


@router.post(
    "/{submission_id}/decision",
    response_model=ReviewDecisionRead,
    status_code=status.HTTP_201_CREATED,
)
def decide_review(
    submission_id: int,
    payload: ReviewDecisionWrite,
    db: Session = Depends(get_db),
    current_evaluator: User = Depends(get_current_evaluator),
) -> ReviewDecisionRead:
    return ReviewService(db).decide(submission_id, payload, current_evaluator)


@router.get("/{submission_id}/certificates/{document_id}")
def download_certificate(
    submission_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_evaluator: User = Depends(get_current_evaluator),
) -> FileResponse:
    path, media_type, filename = ReviewService(db).certificate_file(
        submission_id, document_id, current_evaluator
    )
    return FileResponse(path, media_type=media_type, filename=filename)
