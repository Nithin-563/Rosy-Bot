"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01

This mirrors the SQLAlchemy models in `rosy.models`.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guilds",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(120), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "guild_settings",
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("guilds.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("ai_provider", sa.String(40), nullable=False, server_default="openrouter"),
        sa.Column("ai_model", sa.String(120), nullable=False, server_default=""),
        sa.Column("autonomous_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("autonomous_probability", sa.Float(), nullable=False, server_default="0.15"),
        sa.Column("personality_mode", sa.String(30), nullable=False, server_default="friendly"),
        sa.Column("memory_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("prefix", sa.String(16), nullable=False, server_default=""),
        sa.Column("log_channel_id", sa.BigInteger(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
    )
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, server_default=""),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("llm_preferred_model", sa.String(120), nullable=False, server_default=""),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "provider_credentials",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("provider", sa.String(40), nullable=False, index=True),
        sa.Column("api_key_cipher", sa.Text(), nullable=False),
        sa.Column("base_url", sa.String(300), nullable=True),
        sa.Column("default_model", sa.String(120), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("guild_id", "provider", name="uq_cred_guild_provider"),
    )
    op.create_table(
        "memories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("scope", sa.Enum("dm", "guild", "user_in_guild", name="memory_scope"), nullable=False, index=True),
        sa.Column("type", sa.Enum("user_preference", "useful_fact", "conversation_summary", "guild_fact", "guild_preference", "temporary_context", "relationship", "knowledge", name="memory_type"), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("importance", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("source", sa.String(120), nullable=False, server_default=""),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("scope", "guild_id", "user_id", "content", name="uq_memory_dedup"),
    )
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("channel_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("is_dm", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )
    op.create_table(
        "usage",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("provider", sa.String(40), nullable=False, server_default=""),
        sa.Column("model", sa.String(120), nullable=False, server_default=""),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("kind", sa.String(40), nullable=False, server_default="chat"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )
    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("channel_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("fire_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("recurring", sa.String(20), nullable=False, server_default=""),
        sa.Column("fired", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "moderation_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("target_user_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )
    op.create_table(
        "custom_commands",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("response", sa.Text(), nullable=False, server_default=""),
        sa.Column("ai_powered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("aliases", sa.JSON(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("guild_id", "name", name="uq_custom_command_guild_name"),
    )
    op.create_table(
        "knowledge",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("scope", sa.Enum("dm", "guild", "user_in_guild", name="knowledge_scope"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("importance", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("source", sa.String(120), nullable=False, server_default=""),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "plugin_config",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("plugin", sa.String(80), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.UniqueConstraint("guild_id", "plugin", name="uq_plugin_guild_plugin"),
    )
    op.create_table(
        "personality_state",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("mode", sa.String(30), nullable=False, server_default="friendly"),
        sa.Column("history", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for t in [
        "personality_state", "plugin_config", "knowledge", "custom_commands",
        "moderation_records", "reminders", "usage", "messages", "conversations",
        "memories", "provider_credentials", "user_preferences", "guild_settings",
        "users", "guilds",
    ]:
        op.drop_table(t)