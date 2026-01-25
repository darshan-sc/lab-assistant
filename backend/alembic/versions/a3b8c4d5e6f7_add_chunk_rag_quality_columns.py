"""add chunk rag quality columns

Revision ID: a3b8c4d5e6f7
Revises: db9c11e5334a
Create Date: 2026-01-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b8c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = 'db9c11e5334a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add page tracking, section info, and document metadata columns to chunks."""
    # Page tracking
    op.add_column('chunks', sa.Column('page_start', sa.Integer(), nullable=True))
    op.add_column('chunks', sa.Column('page_end', sa.Integer(), nullable=True))

    # Section/structure tracking
    op.add_column('chunks', sa.Column('section_title', sa.String(length=200), nullable=True))

    # Document metadata (denormalized for fast retrieval)
    op.add_column('chunks', sa.Column('doc_title', sa.String(length=500), nullable=True))
    op.add_column('chunks', sa.Column('doc_authors', sa.Text(), nullable=True))
    op.add_column('chunks', sa.Column('doc_year', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove RAG quality columns from chunks."""
    op.drop_column('chunks', 'doc_year')
    op.drop_column('chunks', 'doc_authors')
    op.drop_column('chunks', 'doc_title')
    op.drop_column('chunks', 'section_title')
    op.drop_column('chunks', 'page_end')
    op.drop_column('chunks', 'page_start')
