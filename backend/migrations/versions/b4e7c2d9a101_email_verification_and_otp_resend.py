"""email verification and otp resend

Revision ID: b4e7c2d9a101
Revises: 92d0f8b7c4a1
Create Date: 2026-08-18 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4e7c2d9a101"
down_revision: Union[str, None] = "92d0f8b7c4a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE otp_purpose ADD VALUE IF NOT EXISTS 'email_verification'")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("email_verified", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE users SET email_verified = true WHERE email_verified IS NULL")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("email_verified", existing_type=sa.Boolean(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("email_verified_at")
        batch_op.drop_column("email_verified")
