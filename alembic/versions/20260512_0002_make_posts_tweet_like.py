"""make posts tweet like

Revision ID: 20260512_0002
Revises: 3917be0dd0f9
Create Date: 2026-05-12
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260512_0002"
down_revision: str | None = "3917be0dd0f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("posts", "title")
    op.alter_column(
        "posts",
        "content",
        existing_type=sa.Text(),
        type_=sa.String(length=280),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "posts",
        "content",
        existing_type=sa.String(length=280),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.add_column("posts", sa.Column("title", sa.String(length=150), nullable=False))
