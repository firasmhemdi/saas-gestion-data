"""password reset otp purpose

Revision ID: f12a0c9b8d31
Revises: b4e7c2d9a101
Create Date: 2026-08-19 13:20:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "f12a0c9b8d31"
down_revision: Union[str, None] = "b4e7c2d9a101"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE otp_purpose ADD VALUE IF NOT EXISTS 'password_reset'")


def downgrade() -> None:
    pass
