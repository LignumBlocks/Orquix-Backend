"""Add interaction_type and session_status fields to interaction_events

Revision ID: simple_context_fields
Revises: ff1a738ad19f
Create Date: 2025-06-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'simple_context_fields'
down_revision: Union[str, None] = 'ff1a738ad19f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add interaction_type and session_status columns to interaction_events."""
    # Add interaction_type column with default value
    op.add_column('interaction_events', 
                  sa.Column('interaction_type', 
                           sa.String(length=50), 
                           nullable=False, 
                           server_default='final_query'))
    
    # Add session_status column (nullable)
    op.add_column('interaction_events', 
                  sa.Column('session_status', 
                           sa.String(length=20), 
                           nullable=True))


def downgrade() -> None:
    """Remove interaction_type and session_status columns."""
    op.drop_column('interaction_events', 'session_status')
    op.drop_column('interaction_events', 'interaction_type') 