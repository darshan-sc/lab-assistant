"""add project members and invites

Revision ID: b4c9d5e7f801
Revises: a3b8c4d5e6f7
Create Date: 2026-02-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4c9d5e7f801'
down_revision: Union[str, Sequence[str], None] = 'a3b8c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create project_members and project_invites tables, seed owner memberships."""
    # Create project_members table
    op.create_table(
        'project_members',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='member'),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('project_id', 'user_id', name='uq_project_member'),
    )

    # Create project_invites table
    op.create_table(
        'project_invites',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('code', sa.String(20), nullable=False, unique=True, index=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )

    # Seed: for every existing project, insert a ProjectMember row with role='owner'
    op.execute(
        """
        INSERT INTO project_members (project_id, user_id, role)
        SELECT id, user_id, 'owner'
        FROM projects
        """
    )


def downgrade() -> None:
    """Drop project_invites and project_members tables."""
    op.drop_table('project_invites')
    op.drop_table('project_members')
