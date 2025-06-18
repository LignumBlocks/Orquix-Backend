"""Add deleted_at field to interaction_events

Revision ID: add_deleted_at_field
Revises: add_updated_at_field
Create Date: 2025-06-17 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_deleted_at_field'
down_revision: Union[str, None] = 'add_updated_at_field'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add deleted_at column to interaction_events."""
    # Add deleted_at column (nullable with index)
    op.add_column('interaction_events', 
                  sa.Column('deleted_at', 
                           sa.DateTime(timezone=True), 
                           nullable=True))
    
    # Add index for deleted_at
    op.create_index(op.f('ix_interaction_events_deleted_at'), 'interaction_events', ['deleted_at'], unique=False)


def downgrade() -> None:
    """Remove deleted_at column."""
    op.drop_index(op.f('ix_interaction_events_deleted_at'), table_name='interaction_events')
    op.drop_column('interaction_events', 'deleted_at') 