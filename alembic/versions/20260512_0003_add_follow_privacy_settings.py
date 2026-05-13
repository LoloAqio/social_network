"""add follow privacy settings

Revision ID: 20260512_0003
Revises: 20260512_0002
Create Date: 2026-05-12
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260512_0003"
down_revision: str | None = "20260512_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_followers_public", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("is_following_public", sa.Boolean(), server_default=sa.true(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "is_following_public")
    op.drop_column("users", "is_followers_public")
