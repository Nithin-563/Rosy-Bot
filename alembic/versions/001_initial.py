"""Initial migration - Create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create guilds table
    op.create_table(
        'guilds',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('guild_id')
    )
    op.create_index('ix_guilds_guild_id', 'guilds', ['guild_id'], unique=True)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('global_name', sa.String(length=255), nullable=True),
        sa.Column('is_bot_owner', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_users_user_id', 'users', ['user_id'], unique=True)

    # Create guild_settings table
    op.create_table(
        'guild_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_guild_settings_guild_key', 'guild_settings', ['guild_id', 'key'], unique=True)

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=True),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('channel_id', sa.BigInteger(), nullable=True),
        sa.Column('conversation_type', sa.String(length=50), nullable=False),
        sa.Column('is_dm', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversations_guild_user', 'conversations', ['guild_id', 'user_id'], unique=False)
    op.create_index('ix_conversations_dm', 'conversations', ['is_dm', 'user_id'], unique=False)

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('conversation_id', sa.BigInteger(), nullable=False),
        sa.Column('discord_message_id', sa.BigInteger(), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_conversation_created', 'messages', ['conversation_id', 'created_at'], unique=False)

    # Create memories table
    op.create_table(
        'memories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=True),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('memory_type', sa.String(length=50), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('importance', sa.Integer(), nullable=False),
        sa.Column('access_count', sa.Integer(), nullable=False),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_memories_guild_user', 'memories', ['guild_id', 'user_id'], unique=False)
    op.create_index('ix_memories_type_key', 'memories', ['memory_type', 'key'], unique=False)

    # Create ai_providers table
    op.create_table(
        'ai_providers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=True),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('api_endpoint', sa.String(length=500), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('max_tokens', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('guild_id')
    )

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=True),
        sa.Column('provider_id', sa.BigInteger(), nullable=True),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('key_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['provider_id'], ['ai_providers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_keys_guild_provider', 'api_keys', ['guild_id', 'provider_name'], unique=False)

    # Create personality_preferences table
    op.create_table(
        'personality_preferences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=True),
        sa.Column('personality_type', sa.String(length=50), nullable=False),
        sa.Column('traits', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('response_length', sa.String(length=20), nullable=False),
        sa.Column('humor_level', sa.Integer(), nullable=False),
        sa.Column('formality_level', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('guild_id')
    )

    # Create logs table
    op.create_table(
        'logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('log_level', sa.String(length=20), nullable=False),
        sa.Column('logger_name', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=True),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_logs_guild_time', 'logs', ['guild_id', 'created_at'], unique=False)
    op.create_index('ix_logs_level_time', 'logs', ['log_level', 'created_at'], unique=False)

    # Create reminders table
    op.create_table(
        'reminders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('channel_id', sa.BigInteger(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False),
        sa.Column('is_dm', sa.Boolean(), nullable=False),
        sa.Column('repeat_interval', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reminders_user_scheduled', 'reminders', ['user_id', 'scheduled_at'], unique=False)
    op.create_index('ix_reminders_completed', 'reminders', ['is_completed', 'scheduled_at'], unique=False)


def downgrade() -> None:
    op.drop_table('reminders')
    op.drop_table('logs')
    op.drop_table('personality_preferences')
    op.drop_table('api_keys')
    op.drop_table('ai_providers')
    op.drop_table('memories')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('guild_settings')
    op.drop_table('users')
    op.drop_table('guilds')
