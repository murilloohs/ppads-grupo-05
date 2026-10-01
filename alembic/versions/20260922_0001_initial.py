"""initial schema

Revision ID: 20260922_0001
Revises:
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260922_0001"
down_revision = None
branch_labels = None
depends_on = None

user_role = postgresql.ENUM(
    "STUDENT", "EVALUATOR", "COORDINATOR", "ADMIN", name="user_role", create_type=False
)
submission_status = postgresql.ENUM(
    "DRAFT",
    "SUBMITTED",
    "PROCESSING",
    "PENDING_REVIEW",
    "APPROVED",
    "REJECTED",
    "CORRECTION_REQUESTED",
    name="submission_status",
    create_type=False,
)
analysis_result = postgresql.ENUM(
    "APPROVED", "MANUAL_REVIEW", "FAILED", name="analysis_result", create_type=False
)
review_decision = postgresql.ENUM(
    "APPROVED", "REJECTED", "CORRECTION_REQUESTED", name="review_decision", create_type=False
)
history_status = postgresql.ENUM(
    "DRAFT",
    "SUBMITTED",
    "PROCESSING",
    "PENDING_REVIEW",
    "APPROVED",
    "REJECTED",
    "CORRECTION_REQUESTED",
    name="history_submission_status",
    create_type=False,
)


def timestamps():
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_institutions_name", "institutions", ["name"])

    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "institution_id",
            sa.Integer(),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("required_complementary_hours", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
        sa.UniqueConstraint("institution_id", "name", name="uq_course_institution_name"),
    )
    op.create_index("ix_courses_institution_id", "courses", ["institution_id"])
    op.create_index("ix_courses_name", "courses", ["name"])

    user_role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("institution_id", sa.Integer(), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("registration_number", sa.String(60), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "complementary_activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("provider_name", sa.String(180), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("declared_hours", sa.Numeric(7, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *timestamps(),
    )
    op.create_index(
        "ix_complementary_activities_student_id", "complementary_activities", ["student_id"]
    )
    op.create_index(
        "ix_complementary_activities_category", "complementary_activities", ["category"]
    )

    op.create_table(
        "certificate_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "activity_id",
            sa.Integer(),
            sa.ForeignKey("complementary_activities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("stored_name", sa.String(255), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("extracted_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *timestamps(),
    )
    op.create_index(
        "ix_certificate_documents_activity_id", "certificate_documents", ["activity_id"]
    )

    op.create_table(
        "validation_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("institution_id", sa.Integer(), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("max_hours", sa.Numeric(7, 2), nullable=True),
        sa.Column(
            "accepted_document_types", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("mandatory_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence_threshold", sa.Float(), nullable=False, server_default="0.85"),
        sa.Column("allows_auto_approval", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        *timestamps(),
        sa.UniqueConstraint(
            "institution_id", "course_id", "category", "version", name="uq_rule_version"
        ),
    )

    submission_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("protocol", sa.String(40), nullable=False, unique=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "activity_id",
            sa.Integer(),
            sa.ForeignKey("complementary_activities.id"),
            nullable=False,
        ),
        sa.Column(
            "validation_rule_id", sa.Integer(), sa.ForeignKey("validation_rules.id"), nullable=True
        ),
        sa.Column("status", submission_status, nullable=False),
        sa.Column(
            "submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        *timestamps(),
    )
    op.create_index("ix_submissions_protocol", "submissions", ["protocol"])
    op.create_index("ix_submissions_status", "submissions", ["status"])

    analysis_result.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "automatic_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "submission_id",
            sa.Integer(),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("result", analysis_result, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        *timestamps(),
    )

    review_decision.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "manual_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "submission_id",
            sa.Integer(),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("evaluator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", review_decision, nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        *timestamps(),
    )

    history_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "submission_id",
            sa.Integer(),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", history_status, nullable=False),
        sa.Column("changed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *timestamps(),
    )


def downgrade() -> None:
    op.drop_table("status_history")
    op.drop_table("manual_reviews")
    op.drop_table("automatic_analyses")
    op.drop_table("submissions")
    op.drop_table("validation_rules")
    op.drop_table("certificate_documents")
    op.drop_table("complementary_activities")
    op.drop_table("users")
    op.drop_table("courses")
    op.drop_table("institutions")
    history_status.drop(op.get_bind(), checkfirst=True)
    review_decision.drop(op.get_bind(), checkfirst=True)
    analysis_result.drop(op.get_bind(), checkfirst=True)
    submission_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
