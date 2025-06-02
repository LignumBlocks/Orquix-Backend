"""add_pgvector_indexes_and_optimizations

Revision ID: 9076a76c6735
Revises: b0a40c7ca064
Create Date: 2025-06-01 19:53:03.188151

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9076a76c6735'
down_revision: Union[str, None] = 'b0a40c7ca064'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pgvector indexes and other optimizations."""
    
    print("🚀 Agregando optimizaciones e índices pgvector...")
    
    # Asegurar que la extensión pgvector esté habilitada
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # ÍNDICES VECTORIALES para context_chunks
    print("📊 Creando índices vectoriales para context_chunks...")
    
    # Índice principal para similitud coseno (más usado en RAG)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_context_chunks_embedding_cosine 
        ON context_chunks USING ivfflat (content_embedding vector_cosine_ops) 
        WITH (lists = 100)
    """)
    
    # Índice adicional para similitud L2 (euclidiana) si se necesita en el futuro
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_context_chunks_embedding_l2 
        ON context_chunks USING ivfflat (content_embedding vector_l2_ops) 
        WITH (lists = 100)
    """)
    
    # ÍNDICES COMPUESTOS para consultas frecuentes
    print("🔗 Creando índices compuestos para optimización...")
    
    # context_chunks - consultas por proyecto/usuario/tipo
    op.create_index(
        'ix_context_chunks_project_user_type', 
        'context_chunks', 
        ['project_id', 'user_id', 'source_type'], 
        unique=False
    )
    
    op.create_index(
        'ix_context_chunks_project_created', 
        'context_chunks', 
        ['project_id', 'created_at'], 
        unique=False
    )
    
    # interaction_events - consultas frecuentes por proyecto y usuario
    op.create_index(
        'ix_interaction_events_project_created', 
        'interaction_events', 
        ['project_id', 'created_at'], 
        unique=False
    )
    
    op.create_index(
        'ix_interaction_events_user_created', 
        'interaction_events', 
        ['user_id', 'created_at'], 
        unique=False
    )
    
    op.create_index(
        'ix_interaction_events_feedback_score', 
        'interaction_events', 
        ['user_feedback_score'], 
        unique=False
    )
    
    # ia_responses - filtrado por proveedor y latencia
    op.create_index(
        'ix_ia_responses_provider_received', 
        'ia_responses', 
        ['ia_provider_name', 'received_at'], 
        unique=False
    )
    
    op.create_index(
        'ix_ia_responses_latency', 
        'ia_responses', 
        ['latency_ms'], 
        unique=False
    )
    
    # Índice condicional para errores en ia_responses
    op.create_index(
        'ix_ia_responses_errors', 
        'ia_responses', 
        ['error_message'], 
        unique=False,
        postgresql_where=sa.text("error_message IS NOT NULL")
    )
    
    # projects - consultas de usuario y archivados
    op.create_index(
        'ix_projects_user_archived', 
        'projects', 
        ['user_id', 'archived_at'], 
        unique=False
    )
    
    # Configuraciones de optimización para pgvector
    print("⚙️ Aplicando configuraciones de optimización...")
    op.execute("SET maintenance_work_mem = '2GB'")  # Temporal para construcción de índices
    
    # Estadísticas para el optimizador de consultas
    op.execute("ANALYZE context_chunks")
    op.execute("ANALYZE interaction_events")
    op.execute("ANALYZE ia_responses")
    op.execute("ANALYZE projects")
    op.execute("ANALYZE users")
    
    print("✅ Índices pgvector y optimizaciones aplicadas exitosamente!")


def downgrade() -> None:
    """Remove pgvector indexes and optimizations."""
    
    print("⬇️ Eliminando índices y optimizaciones...")
    
    # Eliminar índices de projects
    op.drop_index('ix_projects_user_archived', table_name='projects')
    
    # Eliminar índices de ia_responses
    op.drop_index('ix_ia_responses_errors', table_name='ia_responses')
    op.drop_index('ix_ia_responses_latency', table_name='ia_responses')
    op.drop_index('ix_ia_responses_provider_received', table_name='ia_responses')
    
    # Eliminar índices de interaction_events
    op.drop_index('ix_interaction_events_feedback_score', table_name='interaction_events')
    op.drop_index('ix_interaction_events_user_created', table_name='interaction_events')
    op.drop_index('ix_interaction_events_project_created', table_name='interaction_events')
    
    # Eliminar índices compuestos de context_chunks
    op.drop_index('ix_context_chunks_project_created', table_name='context_chunks')
    op.drop_index('ix_context_chunks_project_user_type', table_name='context_chunks')
    
    # Eliminar índices vectoriales (sin CONCURRENTLY en transacciones)
    op.execute("DROP INDEX IF EXISTS ix_context_chunks_embedding_l2")
    op.execute("DROP INDEX IF EXISTS ix_context_chunks_embedding_cosine")
    
    print("✅ Rollback completado!")
