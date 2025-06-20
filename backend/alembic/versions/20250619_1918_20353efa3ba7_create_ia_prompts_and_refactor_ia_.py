"""create_ia_prompts_and_refactor_ia_responses_manual

Revision ID: 20353efa3ba7
Revises: d8b67e63dfb7
Create Date: 2025-06-19 19:18:59.018276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20353efa3ba7'
down_revision: Union[str, None] = 'd8b67e63dfb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Crear tabla ia_prompts
    op.create_table('ia_prompts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('context_session_id', sa.UUID(), nullable=True),
        sa.Column('original_query', sa.Text(), nullable=False),
        sa.Column('generated_prompt', sa.Text(), nullable=False),
        sa.Column('is_edited', sa.Boolean(), nullable=False, default=False),
        sa.Column('edited_prompt', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='generated'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    )
    
    # Crear índices para ia_prompts
    op.create_index('ix_ia_prompts_deleted_at', 'ia_prompts', ['deleted_at'])
    op.create_index('ix_ia_prompts_project_id', 'ia_prompts', ['project_id'])
    op.create_index('ix_ia_prompts_context_session_id', 'ia_prompts', ['context_session_id'])
    op.create_index('ix_ia_prompts_status', 'ia_prompts', ['status'])
    
    # Agregar columna ia_prompt_id a ia_responses (nullable por ahora)
    op.add_column('ia_responses', sa.Column('ia_prompt_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_ia_responses_ia_prompt_id', 'ia_responses', 'ia_prompts', ['ia_prompt_id'], ['id'])
    op.create_index('ix_ia_responses_ia_prompt_id', 'ia_responses', ['ia_prompt_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Eliminar referencias a ia_prompts
    op.drop_constraint('fk_ia_responses_ia_prompt_id', 'ia_responses', type_='foreignkey')
    op.drop_index('ix_ia_responses_ia_prompt_id', 'ia_responses')
    op.drop_column('ia_responses', 'ia_prompt_id')
    
    # Eliminar tabla ia_prompts
    op.drop_table('ia_prompts')
