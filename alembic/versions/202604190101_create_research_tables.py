"""create research tables

Revision ID: 202604190101
Revises:
Create Date: 2026-04-19 10:01:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "202604190101"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_job_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary Key ID"),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("repository_url", sa.String(length=512), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("repo", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column("instant_data", sa.JSON(), nullable=True),
        sa.Column(
            "progress_msg",
            sa.String(length=255),
            nullable=False,
            server_default="Repository research queued",
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("ai_cache_key", sa.String(length=512), nullable=True),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_time", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
        comment="Research job lifecycle records",
    )
    op.create_index(op.f("ix_research_job_records_id"), "research_job_records", ["id"], unique=False)
    op.create_index(op.f("ix_research_job_records_job_id"), "research_job_records", ["job_id"], unique=True)
    op.create_index(op.f("ix_research_job_records_owner"), "research_job_records", ["owner"], unique=False)
    op.create_index(op.f("ix_research_job_records_repo"), "research_job_records", ["repo"], unique=False)
    op.create_index(op.f("ix_research_job_records_repository_url"), "research_job_records", ["repository_url"], unique=False)
    op.create_index(op.f("ix_research_job_records_status"), "research_job_records", ["status"], unique=False)

    op.create_table(
        "final_research_report_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary Key ID"),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("repository_url", sa.String(length=512), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column("deterministic_data", sa.JSON(), nullable=False),
        sa.Column("ai_insights", sa.JSON(), nullable=True),
        sa.Column("ai_fallback", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ai_fallback_reason", sa.Text(), nullable=True),
        sa.Column("markdown_report", sa.Text(), nullable=False),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_time", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
        comment="Persisted final research reports",
    )
    op.create_index(op.f("ix_final_research_report_records_id"), "final_research_report_records", ["id"], unique=False)
    op.create_index(op.f("ix_final_research_report_records_job_id"), "final_research_report_records", ["job_id"], unique=True)
    op.create_index(op.f("ix_final_research_report_records_repository_url"), "final_research_report_records", ["repository_url"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_final_research_report_records_repository_url"), table_name="final_research_report_records")
    op.drop_index(op.f("ix_final_research_report_records_job_id"), table_name="final_research_report_records")
    op.drop_index(op.f("ix_final_research_report_records_id"), table_name="final_research_report_records")
    op.drop_table("final_research_report_records")

    op.drop_index(op.f("ix_research_job_records_status"), table_name="research_job_records")
    op.drop_index(op.f("ix_research_job_records_repository_url"), table_name="research_job_records")
    op.drop_index(op.f("ix_research_job_records_repo"), table_name="research_job_records")
    op.drop_index(op.f("ix_research_job_records_owner"), table_name="research_job_records")
    op.drop_index(op.f("ix_research_job_records_job_id"), table_name="research_job_records")
    op.drop_index(op.f("ix_research_job_records_id"), table_name="research_job_records")
    op.drop_table("research_job_records")