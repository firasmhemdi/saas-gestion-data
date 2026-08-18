"""sprints 3 4 5 ingestion mapping documents

Revision ID: 92d0f8b7c4a1
Revises: 3aa6f4182463
Create Date: 2026-08-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "92d0f8b7c4a1"
down_revision: Union[str, None] = "3aa6f4182463"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("site_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.Enum("preview", "pending", "running", "success", "failed", name="import_status"), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("imported_count", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("mapping", sa.JSON(), nullable=True),
        sa.Column("preview_rows", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_jobs_company_id"), "import_jobs", ["company_id"], unique=False)
    op.create_index(op.f("ix_import_jobs_created_at"), "import_jobs", ["created_at"], unique=False)
    op.create_index(op.f("ix_import_jobs_created_by"), "import_jobs", ["created_by"], unique=False)
    op.create_index(op.f("ix_import_jobs_site_id"), "import_jobs", ["site_id"], unique=False)
    op.create_index(op.f("ix_import_jobs_source_id"), "import_jobs", ["source_id"], unique=False)
    op.create_index(op.f("ix_import_jobs_status"), "import_jobs", ["status"], unique=False)

    op.create_table(
        "data_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("target_model", sa.String(length=64), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_data_mappings_company_id"), "data_mappings", ["company_id"], unique=False)
    op.create_index(op.f("ix_data_mappings_source_id"), "data_mappings", ["source_id"], unique=False)

    op.create_table(
        "sync_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("frequency", sa.String(length=32), nullable=False),
        sa.Column("window_start", sa.String(length=8), nullable=True),
        sa.Column("window_end", sa.String(length=8), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_status", sa.Enum("idle", "success", "failed", name="sync_status"), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sync_schedules_company_id"), "sync_schedules", ["company_id"], unique=False)
    op.create_index(op.f("ix_sync_schedules_source_id"), "sync_schedules", ["source_id"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.Enum("facture_energie", "bordereau_dechets", "contrat", "attestation", "autre", name="document_type"), nullable=False),
        sa.Column("status", sa.Enum("uploaded", "extracted", "validated", "rejected", name="document_status"), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_company_id"), "documents", ["company_id"], unique=False)
    op.create_index(op.f("ix_documents_created_at"), "documents", ["created_at"], unique=False)
    op.create_index(op.f("ix_documents_created_by"), "documents", ["created_by"], unique=False)
    op.create_index(op.f("ix_documents_document_type"), "documents", ["document_type"], unique=False)
    op.create_index(op.f("ix_documents_site_id"), "documents", ["site_id"], unique=False)
    op.create_index(op.f("ix_documents_status"), "documents", ["status"], unique=False)

    op.create_table(
        "extracted_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("fields", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validated_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["validated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_extracted_data_company_id"), "extracted_data", ["company_id"], unique=False)
    op.create_index(op.f("ix_extracted_data_document_id"), "extracted_data", ["document_id"], unique=False)
    op.create_index(op.f("ix_extracted_data_validated_by"), "extracted_data", ["validated_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_extracted_data_validated_by"), table_name="extracted_data")
    op.drop_index(op.f("ix_extracted_data_document_id"), table_name="extracted_data")
    op.drop_index(op.f("ix_extracted_data_company_id"), table_name="extracted_data")
    op.drop_table("extracted_data")
    op.drop_index(op.f("ix_documents_status"), table_name="documents")
    op.drop_index(op.f("ix_documents_site_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_document_type"), table_name="documents")
    op.drop_index(op.f("ix_documents_created_by"), table_name="documents")
    op.drop_index(op.f("ix_documents_created_at"), table_name="documents")
    op.drop_index(op.f("ix_documents_company_id"), table_name="documents")
    op.drop_table("documents")
    op.drop_index(op.f("ix_sync_schedules_source_id"), table_name="sync_schedules")
    op.drop_index(op.f("ix_sync_schedules_company_id"), table_name="sync_schedules")
    op.drop_table("sync_schedules")
    op.drop_index(op.f("ix_data_mappings_source_id"), table_name="data_mappings")
    op.drop_index(op.f("ix_data_mappings_company_id"), table_name="data_mappings")
    op.drop_table("data_mappings")
    op.drop_index(op.f("ix_import_jobs_status"), table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_source_id"), table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_site_id"), table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_created_by"), table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_created_at"), table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_company_id"), table_name="import_jobs")
    op.drop_table("import_jobs")
