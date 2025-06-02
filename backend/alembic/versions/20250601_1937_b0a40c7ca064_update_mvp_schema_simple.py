"""update_mvp_schema_simple

Revision ID: b0a40c7ca064
Revises: 7dd45a2bd520
Create Date: 2025-06-01 19:37:52.635939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel.sql.sqltypes
import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision: str = 'b0a40c7ca064'
down_revision: Union[str, None] = '7dd45a2bd520'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Manejo de datos existentes en context_chunks."""
    
    # PASO 1: Primero modificar ia_responses para eliminar dependencia con interaction_steps
    print("🔄 Modificando ia_responses para eliminar dependencias...")
    
    # Agregar nueva columna (temporal como nullable)
    op.add_column('ia_responses', sa.Column('interaction_event_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    
    # Como no hay datos, no necesito migrar. Solo hago la columna NOT NULL
    op.alter_column('ia_responses', 'interaction_event_id', nullable=False)
    
    # Eliminar la foreign key vieja y crear la nueva
    op.drop_constraint('ia_responses_interaction_step_id_fkey', 'ia_responses', type_='foreignkey')
    op.drop_index(op.f('ix_ia_responses_interaction_step_id'), table_name='ia_responses')
    op.create_index(op.f('ix_ia_responses_interaction_event_id'), 'ia_responses', ['interaction_event_id'], unique=False)
    op.create_foreign_key(None, 'ia_responses', 'interaction_events', ['interaction_event_id'], ['id'])
    op.drop_column('ia_responses', 'interaction_step_id')
    
    # PASO 2: Ahora eliminar las tablas obsoletas (sin dependencias)
    print("🗑️ Eliminando tablas obsoletas...")
    
    op.drop_index(op.f('ix_interaction_steps_deleted_at'), table_name='interaction_steps')
    op.drop_index(op.f('ix_interaction_steps_session_id'), table_name='interaction_steps')
    op.drop_index(op.f('ix_interaction_steps_step_order'), table_name='interaction_steps')
    op.drop_table('interaction_steps')
    
    op.drop_index(op.f('ix_research_sessions_deleted_at'), table_name='research_sessions')
    op.drop_index(op.f('ix_research_sessions_project_id'), table_name='research_sessions')
    op.drop_index(op.f('ix_research_sessions_user_id'), table_name='research_sessions')
    op.drop_table('research_sessions')
    
    # PASO 3: Actualizar context_chunks - LIMPIAR DATOS ANTES DEL CAMBIO
    print("🔧 Actualizando context_chunks (limpiando datos de prueba)...")
    
    # Verificar cuántos registros hay
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT COUNT(*) FROM context_chunks"))
    count = result.scalar()
    print(f"   Encontrados {count} registros en context_chunks")
    
    if count > 0:
        print("   ⚠️  Eliminando datos de prueba para cambiar estructura del vector...")
        op.execute("TRUNCATE TABLE context_chunks RESTART IDENTITY CASCADE")
    
    # Cambiar content_text de VARCHAR a TEXT
    op.alter_column('context_chunks', 'content_text',
               existing_type=sa.VARCHAR(),
               type_=sa.Text(),
               existing_nullable=False)
    
    # Para el vector embedding: eliminar y recrear (no se puede alterar dimensiones directamente)
    print("   Recreando columna content_embedding con nuevas dimensiones...")
    op.drop_column('context_chunks', 'content_embedding')
    op.add_column('context_chunks', sa.Column('content_embedding', pgvector.sqlalchemy.Vector(dim=384), nullable=False))
    
    # Cambiar created_at de TIMESTAMP a TIMESTAMPTZ
    op.alter_column('context_chunks', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False)
    op.create_index(op.f('ix_context_chunks_created_at'), 'context_chunks', ['created_at'], unique=False)
    
    # PASO 4: Actualizar interaction_events
    print("📝 Actualizando interaction_events...")
    
    # Agregar columna user_prompt_text solo si no tiene datos (tabla vacía)
    op.add_column('interaction_events', sa.Column('user_prompt_text', sa.Text(), nullable=True))
    # Como la tabla está vacía, puedo hacer NOT NULL después
    op.alter_column('interaction_events', 'user_prompt_text', nullable=False)
    
    op.add_column('interaction_events', sa.Column('context_used_summary', sa.Text(), nullable=True))
    op.add_column('interaction_events', sa.Column('moderated_synthesis_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.add_column('interaction_events', sa.Column('user_feedback_score', sa.Integer(), nullable=True))
    op.add_column('interaction_events', sa.Column('user_feedback_comment', sa.Text(), nullable=True))
    
    # Actualizar tipos de columnas existentes
    op.alter_column('interaction_events', 'ai_responses_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               nullable=True)
    op.alter_column('interaction_events', 'processing_time_ms',
               existing_type=sa.INTEGER(),
               nullable=True)
    
    # Crear foreign keys solo para interaction_events (las de context_chunks ya existen)
    print("🔗 Creando foreign keys para interaction_events...")
    
    # Verificar si las foreign keys ya existen antes de crearlas
    try:
        op.create_foreign_key('interaction_events_project_id_fkey', 'interaction_events', 'projects', ['project_id'], ['id'])
    except:
        print("   Foreign key project_id ya existe, saltando...")
        
    try:
        op.create_foreign_key('interaction_events_moderated_synthesis_id_fkey', 'interaction_events', 'moderated_syntheses', ['moderated_synthesis_id'], ['id'])
    except:
        print("   Foreign key moderated_synthesis_id ya existe, saltando...")
        
    try:
        op.create_foreign_key('interaction_events_user_id_fkey', 'interaction_events', 'users', ['user_id'], ['id'])
    except:
        print("   Foreign key user_id ya existe, saltando...")
    
    # Eliminar columna obsoleta
    op.drop_column('interaction_events', 'user_prompt')
    
    # PASO 5: Actualizar moderated_syntheses
    print("📄 Actualizando moderated_syntheses...")
    op.alter_column('moderated_syntheses', 'synthesis_text',
               existing_type=sa.VARCHAR(),
               type_=sa.Text(),
               existing_nullable=False)
    op.alter_column('moderated_syntheses', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False)
               
    # PASO 6: Actualizar users
    print("👤 Actualizando users...")
    
    # Primero, actualizar los avatar_url NULL con un valor por defecto
    connection = op.get_bind()
    null_avatars = connection.execute(sa.text("SELECT COUNT(*) FROM users WHERE avatar_url IS NULL")).scalar()
    print(f"   Encontrados {null_avatars} usuarios con avatar_url NULL")
    
    if null_avatars > 0:
        print("   Asignando avatar por defecto a usuarios sin avatar...")
        op.execute("UPDATE users SET avatar_url = 'https://via.placeholder.com/150' WHERE avatar_url IS NULL")
    
    # Ahora sí podemos hacer la columna NOT NULL
    op.alter_column('users', 'avatar_url',
               existing_type=sa.VARCHAR(),
               nullable=False)
    
    print("✅ Migración MVP completada exitosamente!")
    print("ℹ️  Nota: Los datos de prueba en context_chunks fueron eliminados debido al cambio de estructura vectorial.")


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'avatar_url',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('moderated_syntheses', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=False)
    op.alter_column('moderated_syntheses', 'synthesis_text',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    op.add_column('interaction_events', sa.Column('user_prompt', sa.TEXT(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'interaction_events', type_='foreignkey')
    op.drop_constraint(None, 'interaction_events', type_='foreignkey')
    op.drop_constraint(None, 'interaction_events', type_='foreignkey')
    op.alter_column('interaction_events', 'processing_time_ms',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('interaction_events', 'ai_responses_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               nullable=False)
    op.drop_column('interaction_events', 'user_feedback_comment')
    op.drop_column('interaction_events', 'user_feedback_score')
    op.drop_column('interaction_events', 'moderated_synthesis_id')
    op.drop_column('interaction_events', 'context_used_summary')
    op.drop_column('interaction_events', 'user_prompt_text')
    op.add_column('ia_responses', sa.Column('interaction_step_id', sa.UUID(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'ia_responses', type_='foreignkey')
    op.create_foreign_key(op.f('ia_responses_interaction_step_id_fkey'), 'ia_responses', 'interaction_steps', ['interaction_step_id'], ['id'])
    op.drop_index(op.f('ix_ia_responses_interaction_event_id'), table_name='ia_responses')
    op.create_index(op.f('ix_ia_responses_interaction_step_id'), 'ia_responses', ['interaction_step_id'], unique=False)
    op.drop_column('ia_responses', 'interaction_event_id')
    op.drop_index(op.f('ix_context_chunks_created_at'), table_name='context_chunks')
    op.alter_column('context_chunks', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=False)
    op.alter_column('context_chunks', 'content_embedding',
               existing_type=pgvector.sqlalchemy.Vector(dim=384),
               type_=pgvector.sqlalchemy.Vector(dim=1536),
               existing_nullable=False)
    op.alter_column('context_chunks', 'content_text',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    op.create_table('interaction_steps',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('deleted_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('session_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('step_order', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('user_prompt_text', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('context_used_summary', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('moderator_synthesis_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('user_feedback_score', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('user_feedback_comment', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['moderator_synthesis_id'], ['moderated_syntheses.id'], name=op.f('interaction_steps_moderator_synthesis_id_fkey')),
    sa.ForeignKeyConstraint(['session_id'], ['research_sessions.id'], name=op.f('interaction_steps_session_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('interaction_steps_pkey'))
    )
    op.create_index(op.f('ix_interaction_steps_step_order'), 'interaction_steps', ['step_order'], unique=False)
    op.create_index(op.f('ix_interaction_steps_session_id'), 'interaction_steps', ['session_id'], unique=False)
    op.create_index(op.f('ix_interaction_steps_deleted_at'), 'interaction_steps', ['deleted_at'], unique=False)
    op.create_table('research_sessions',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('deleted_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('project_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('session_start_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('initial_user_prompt', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('moderated_synthesis_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['moderated_synthesis_id'], ['moderated_syntheses.id'], name=op.f('research_sessions_moderated_synthesis_id_fkey')),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('research_sessions_project_id_fkey')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('research_sessions_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('research_sessions_pkey'))
    )
    op.create_index(op.f('ix_research_sessions_user_id'), 'research_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_research_sessions_project_id'), 'research_sessions', ['project_id'], unique=False)
    op.create_index(op.f('ix_research_sessions_deleted_at'), 'research_sessions', ['deleted_at'], unique=False)
    # ### end Alembic commands ###
