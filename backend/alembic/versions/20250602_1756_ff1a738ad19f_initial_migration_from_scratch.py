"""initial_migration_from_scratch

Revision ID: ff1a738ad19f
Revises: 
Create Date: 2025-06-02 17:56:36.813156

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'ff1a738ad19f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create all tables."""
    
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('google_id', sa.String(), nullable=False),
        sa.Column('avatar_url', sa.String(), nullable=False),
    )
    op.create_index(op.f('ix_users_deleted_at'), 'users', ['deleted_at'])
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)
    
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('moderator_personality', sa.String(), nullable=False, server_default='Analytical'),
        sa.Column('moderator_temperature', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('moderator_length_penalty', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index(op.f('ix_projects_deleted_at'), 'projects', ['deleted_at'])
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'])
    
    # Create moderated_syntheses table
    op.create_table(
        'moderated_syntheses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('synthesis_text', sa.Text(), nullable=False),
    )
    op.create_index(op.f('ix_moderated_syntheses_deleted_at'), 'moderated_syntheses', ['deleted_at'])
    
    # Create interaction_events table
    op.create_table(
        'interaction_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_prompt_text', sa.Text(), nullable=False),
        sa.Column('context_used_summary', sa.Text(), nullable=True),
        sa.Column('moderated_synthesis_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_feedback_score', sa.Integer(), nullable=True),
        sa.Column('user_feedback_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ai_responses_json', postgresql.JSONB(), nullable=True),
        sa.Column('moderator_synthesis_json', postgresql.JSONB(), nullable=True),
        sa.Column('context_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('context_preview', sa.String(500), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['moderated_synthesis_id'], ['moderated_syntheses.id']),
    )
    op.create_index(op.f('ix_interaction_events_created_at'), 'interaction_events', ['created_at'])
    op.create_index(op.f('ix_interaction_events_project_id'), 'interaction_events', ['project_id'])
    op.create_index(op.f('ix_interaction_events_user_id'), 'interaction_events', ['user_id'])
    
    # Create ia_responses table
    op.create_table(
        'ia_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('interaction_event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ia_provider_name', sa.String(), nullable=False),
        sa.Column('raw_response_text', sa.String(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['interaction_event_id'], ['interaction_events.id']),
    )
    op.create_index(op.f('ix_ia_responses_deleted_at'), 'ia_responses', ['deleted_at'])
    op.create_index(op.f('ix_ia_responses_ia_provider_name'), 'ia_responses', ['ia_provider_name'])
    op.create_index(op.f('ix_ia_responses_interaction_event_id'), 'ia_responses', ['interaction_event_id'])
    
    # Create context_chunks table
    op.create_table(
        'context_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('content_embedding', Vector(1536), nullable=False),  # Default embedding dimension
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_identifier', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index(op.f('ix_context_chunks_deleted_at'), 'context_chunks', ['deleted_at'])
    op.create_index(op.f('ix_context_chunks_project_id'), 'context_chunks', ['project_id'])
    op.create_index(op.f('ix_context_chunks_user_id'), 'context_chunks', ['user_id'])
    op.create_index(op.f('ix_context_chunks_source_type'), 'context_chunks', ['source_type'])
    op.create_index(op.f('ix_context_chunks_source_identifier'), 'context_chunks', ['source_identifier'])


def downgrade() -> None:
    """Downgrade schema - Drop all tables."""
    op.drop_table('context_chunks')
    op.drop_table('ia_responses')
    op.drop_table('interaction_events')
    op.drop_table('moderated_syntheses')
    op.drop_table('projects')
    op.drop_table('users')
