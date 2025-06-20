"""remove_obsolete_columns_from_ia_responses

Revision ID: 5662ce7d838a
Revises: 20353efa3ba7
Create Date: 2025-06-19 19:34:32.165506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5662ce7d838a'
down_revision: Union[str, None] = '20353efa3ba7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Eliminar columnas obsoletas de ia_responses
    op.drop_constraint('fk_ia_responses_project_id', 'ia_responses', type_='foreignkey')
    op.drop_index('ix_ia_responses_project_id', 'ia_responses')
    op.drop_column('ia_responses', 'project_id')
    op.drop_column('ia_responses', 'prompt_text')


def downgrade() -> None:
    """Downgrade schema."""
    # Restaurar columnas eliminadas
    op.add_column('ia_responses', sa.Column('prompt_text', sa.Text(), nullable=True))
    op.add_column('ia_responses', sa.Column('project_id', sa.UUID(), nullable=False))
    op.create_index('ix_ia_responses_project_id', 'ia_responses', ['project_id'])
    op.create_foreign_key('fk_ia_responses_project_id', 'ia_responses', 'projects', ['project_id'], ['id'])
