"""Add updated_at field to interaction_events

Revision ID: add_updated_at_field
Revises: simple_context_fields
Create Date: 2025-06-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_updated_at_field'
down_revision: Union[str, None] = 'simple_context_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add updated_at column to interaction_events."""
    # Add updated_at column with default value
    op.add_column('interaction_events', 
                  sa.Column('updated_at', 
                           sa.DateTime(timezone=True), 
                           nullable=False, 
                           server_default=sa.func.now()))


def downgrade() -> None:
    """Remove updated_at column."""
    op.drop_column('interaction_events', 'updated_at') 