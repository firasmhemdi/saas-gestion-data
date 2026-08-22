"""add csv source type

Revision ID: a94e2b601f4c
Revises: f12a0c9b8d31
Create Date: 2026-08-22 10:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "a94e2b601f4c"
down_revision: Union[str, None] = "f12a0c9b8d31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'csv'")
        op.execute("ALTER TYPE data_entry_source ADD VALUE IF NOT EXISTS 'csv'")


def downgrade() -> None:
    pass
