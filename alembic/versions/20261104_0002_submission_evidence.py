"""Preserve the document and activity data used in each submission."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261104_0002"
down_revision = "20260922_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("submissions", sa.Column("document_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_submission_document", "submissions", "certificate_documents", ["document_id"], ["id"]
    )
    op.add_column("submissions", sa.Column("activity_snapshot", postgresql.JSONB(), nullable=True))
    op.execute("""
        UPDATE submissions s SET document_id = (
            SELECT d.id FROM certificate_documents d WHERE d.activity_id = s.activity_id
            ORDER BY (d.created_at <= s.submitted_at) DESC, d.id DESC LIMIT 1
        ), activity_snapshot = (
            SELECT jsonb_build_object('title', a.title, 'category', a.category,
                'provider_name', a.provider_name, 'start_date', a.start_date,
                'end_date', a.end_date, 'declared_hours', a.declared_hours::text,
                'description', a.description)
            FROM complementary_activities a WHERE a.id = s.activity_id
        )
    """)


def downgrade():
    op.drop_column("submissions", "activity_snapshot")
    op.drop_constraint("fk_submission_document", "submissions", type_="foreignkey")
    op.drop_column("submissions", "document_id")
