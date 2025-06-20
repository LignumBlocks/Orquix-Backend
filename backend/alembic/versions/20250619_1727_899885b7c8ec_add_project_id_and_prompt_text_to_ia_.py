"""add project_id and prompt_text to ia_responses

Revision ID: 899885b7c8ec
Revises: add_deleted_at_field
Create Date: 2025-06-19 17:27:19.367633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '899885b7c8ec'
down_revision: Union[str, None] = 'add_deleted_at_field'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add project_id and prompt_text columns to ia_responses
    op.add_column('ia_responses', sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('ia_responses', sa.Column('prompt_text', sa.Text(), nullable=True))
    op.create_index(op.f('ix_ia_responses_project_id'), 'ia_responses', ['project_id'], unique=False)
    op.create_foreign_key('fk_ia_responses_project_id', 'ia_responses', 'projects', ['project_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove project_id and prompt_text columns from ia_responses
    op.drop_constraint('fk_ia_responses_project_id', 'ia_responses', type_='foreignkey')
    op.drop_index(op.f('ix_ia_responses_project_id'), table_name='ia_responses')
    op.drop_column('ia_responses', 'prompt_text')
    op.drop_column('ia_responses', 'project_id')
