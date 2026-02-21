"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('username', sa.String(64), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('role', sa.Enum('L1', 'L2', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('full_name', sa.String(128), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_users_username', 'users', ['username'])

    op.create_table(
        'datasets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(256), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.Enum('UPLOADING','PARSING','CORRELATING','SUMMARIZING','READY','ERROR', name='datasetstatus'), nullable=False),
        sa.Column('uploaded_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True)),
        sa.Column('event_count', sa.Integer, default=0),
        sa.Column('incident_count', sa.Integer, default=0),
        sa.Column('parse_errors', JSONB, nullable=True),
    )

    op.create_table(
        'raw_files',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_id', UUID(as_uuid=True), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(512), nullable=False),
        sa.Column('file_type', sa.Enum('SIEM_JSON','WEB_LOG','SURICATA','SNORT', name='filetype'), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('stored_path', sa.String(1024), nullable=False),
        sa.Column('size_bytes', sa.BigInteger, default=0),
        sa.Column('uploaded_at', sa.DateTime(timezone=True)),
    )

    op.create_table(
        'events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_id', UUID(as_uuid=True), sa.ForeignKey('datasets.id'), nullable=False),
        sa.Column('raw_file_id', UUID(as_uuid=True), sa.ForeignKey('raw_files.id'), nullable=True),
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_type', sa.String(32), nullable=True),
        sa.Column('host', sa.String(256), nullable=True),
        sa.Column('username', sa.String(256), nullable=True),
        sa.Column('src_ip', sa.String(64), nullable=True),
        sa.Column('dst_ip', sa.String(64), nullable=True),
        sa.Column('src_port', sa.Integer, nullable=True),
        sa.Column('dst_port', sa.Integer, nullable=True),
        sa.Column('event_type', sa.String(64), nullable=True),
        sa.Column('severity_hint', sa.String(32), nullable=True),
        sa.Column('http_method', sa.String(16), nullable=True),
        sa.Column('url_path', sa.Text, nullable=True),
        sa.Column('http_status', sa.Integer, nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('response_size', sa.Integer, nullable=True),
        sa.Column('signature_id', sa.String(64), nullable=True),
        sa.Column('signature', sa.Text, nullable=True),
        sa.Column('category', sa.String(128), nullable=True),
        sa.Column('ids_priority', sa.Integer, nullable=True),
        sa.Column('protocol', sa.String(32), nullable=True),
        sa.Column('message', sa.Text, nullable=True),
        sa.Column('raw_json', JSONB, nullable=True),
        sa.Column('extras', JSONB, nullable=True),
    )
    op.create_index('ix_events_event_time', 'events', ['event_time'])
    op.create_index('ix_events_username', 'events', ['username'])
    op.create_index('ix_events_src_ip', 'events', ['src_ip'])
    op.create_index('ix_events_dataset_time', 'events', ['dataset_id', 'event_time'])
    op.create_index('ix_events_src_ip_time', 'events', ['src_ip', 'event_time'])

    op.create_table(
        'incidents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_id', UUID(as_uuid=True), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('status', sa.String(20), default='NEW', nullable=False),
        sa.Column('severity', sa.String(20), default='MEDIUM', nullable=False),
        sa.Column('incident_type', sa.String(64), nullable=True),
        sa.Column('confidence', sa.Integer, default=50),
        sa.Column('rule_id', sa.String(64), nullable=True),
        sa.Column('rule_explanation', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('acknowledged_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_to', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('closed_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_incidents_dataset_status', 'incidents', ['dataset_id', 'status'])

    op.create_table(
        'incident_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_id', UUID(as_uuid=True), sa.ForeignKey('events.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relevance', sa.String(32), default='corroborating'),
        sa.UniqueConstraint('incident_id', 'event_id', name='uq_incident_event'),
    )

    op.create_table(
        'incident_notes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('note_type', sa.Enum('TRIAGE','INVESTIGATION', name='notetype'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('author_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )

    op.create_table(
        'incident_ai_summaries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('summary_json', JSONB, nullable=True),
        sa.Column('narrative', sa.Text, nullable=True),
        sa.Column('model_name', sa.String(256), nullable=True),
        sa.Column('prompt_version', sa.String(64), nullable=True),
        sa.Column('generation_time_sec', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )

    op.create_table(
        'chat_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('dataset_id', UUID(as_uuid=True), sa.ForeignKey('datasets.id'), nullable=True),
        sa.Column('incident_id', UUID(as_uuid=True), sa.ForeignKey('incidents.id'), nullable=True),
        sa.Column('title', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )

    op.create_table(
        'chat_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.Enum('USER','ASSISTANT', name='messagerole'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('evidence_refs', JSONB, nullable=True),
        sa.Column('model_name', sa.String(256), nullable=True),
        sa.Column('prompt_version', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )

    op.create_table(
        'audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action_type', sa.String(64), nullable=False),
        sa.Column('target_type', sa.String(64), nullable=True),
        sa.Column('target_id', sa.String(128), nullable=True),
        sa.Column('before_json', JSONB, nullable=True),
        sa.Column('after_json', JSONB, nullable=True),
        sa.Column('details', sa.Text, nullable=True),
        sa.Column('ip_addr', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('incident_ai_summaries')
    op.drop_table('incident_notes')
    op.drop_table('incident_events')
    op.drop_table('incidents')
    op.drop_table('events')
    op.drop_table('raw_files')
    op.drop_table('datasets')
    op.drop_table('users')
