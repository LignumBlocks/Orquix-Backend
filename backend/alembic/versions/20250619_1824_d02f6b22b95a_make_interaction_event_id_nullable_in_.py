"""remove_interaction_event_id_from_ia_responses

Revision ID: d02f6b22b95a
Revises: 899885b7c8ec
Create Date: 2025-06-19 18:24:33.514039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd02f6b22b95a'
down_revision: Union[str, None] = '899885b7c8ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove interaction_event_id column and its foreign key constraint
    op.drop_constraint('ia_responses_interaction_event_id_fkey', 'ia_responses', type_='foreignkey')
    op.drop_index('ix_ia_responses_interaction_event_id', table_name='ia_responses')
    op.drop_column('ia_responses', 'interaction_event_id')


def downgrade() -> None:
    """Downgrade schema."""
    # Add back interaction_event_id column and its constraints
    op.add_column('ia_responses', sa.Column('interaction_event_id', sa.UUID(), nullable=False))
    op.create_index('ix_ia_responses_interaction_event_id', 'ia_responses', ['interaction_event_id'])
    op.create_foreign_key('ia_responses_interaction_event_id_fkey', 'ia_responses', 'interaction_events', ['interaction_event_id'], ['id'])
