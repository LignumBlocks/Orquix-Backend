"""update_embedding_dimension

Revision ID: 7dd45a2bd520
Revises: a9f33085b59a
Create Date: 2025-05-30 08:24:08.281473

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '7dd45a2bd520'
down_revision: Union[str, None] = 'a9f33085b59a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Primero eliminamos los datos existentes ya que no podemos convertirlos automáticamente
    op.execute('TRUNCATE TABLE context_chunks')
    
    # Modificamos la columna content_embedding
    op.alter_column(
        'context_chunks',
        'content_embedding',
        existing_type=Vector(1536),
        type_=Vector(1536),  # Dimensión para OpenAI text-embedding-3-small
        postgresql_using='content_embedding::vector(1536)'
    )

def downgrade() -> None:
    # En caso de downgrade, también necesitamos limpiar los datos
    op.execute('TRUNCATE TABLE context_chunks')
    
    # Revertimos la columna a su dimensión original
    op.alter_column(
        'context_chunks',
        'content_embedding',
        existing_type=Vector(1536),
        type_=Vector(1536),
        postgresql_using='content_embedding::vector(1536)'
    )
