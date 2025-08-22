"""Add escalation models

Revision ID: 20240819_add_escalation_models
Revises: 
Create Date: 2024-08-19 09:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240819_add_escalation_models'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create escalation_policies table
    op.create_table('escalation_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False, index=True, unique=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('steps', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create escalation_events table
    op.create_table('escalation_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('policy_id', sa.Integer(), nullable=False),
        sa.Column('step', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_id'], ['escalation_policies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on escalation_events for faster lookups
    op.create_index('idx_escalation_events_incident', 'escalation_events', ['incident_id'], unique=False)
    op.create_index('idx_escalation_events_policy', 'escalation_events', ['policy_id'], unique=False)
    op.create_index('idx_escalation_events_status', 'escalation_events', ['status'], unique=False)


def downgrade():
    # Drop indexes first
    op.drop_index('idx_escalation_events_status', table_name='escalation_events')
    op.drop_index('idx_escalation_events_policy', table_name='escalation_events')
    op.drop_index('idx_escalation_events_incident', table_name='escalation_events')
    
    # Drop tables
    op.drop_table('escalation_events')
    op.drop_table('escalation_policies')
