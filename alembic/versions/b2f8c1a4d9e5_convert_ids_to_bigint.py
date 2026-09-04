"""convert snowflake ids to BIGINT

Revision ID: b2f8c1a4d9e5
Revises: a4794f3706e6
Create Date: 2026-09-04

Discord snowflake ids are 64-bit. The initial migration generated 32-bit
INTEGER columns (autogen from SQLite). This migration converts every
snowflake column to BIGINT so large ids no longer overflow. Tables are empty
on upgrade, so a plain type change is safe.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2f8c1a4d9e5"
down_revision: Union[str, None] = "a4794f3706e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite can't ALTER COLUMN TYPE and fresh SQLite already creates BIGINT via
    # the initial migration, so only run the conversion on PostgreSQL.
    if op.get_context().dialect.name != "postgresql":
        return

    # --- primary keys (referenced) ---
    op.alter_column("guilds", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("users", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("ai_providers", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("channels", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("conversations", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("messages", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("memories", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("usage_stats", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("reminders", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("scheduled_tasks", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("moderation_records", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("custom_commands", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("knowledge", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("guild_config", "id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)

    # --- foreign keys / reference columns (referencing) ---
    op.alter_column("ai_providers", "guild_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=True)
    op.alter_column("channels", "guild_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=True)
    op.alter_column("channels", "channel_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("conversations", "guild_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=True)
    op.alter_column("conversations", "user_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=True)
    op.alter_column("conversations", "channel_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=True)
    op.alter_column("messages", "conversation_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("memories", "guild_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=True)
    op.alter_column("memories", "user_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=True)
    op.alter_column("usage_stats", "guild_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=True)
    op.alter_column("reminders", "guild_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=True)
    op.alter_column("reminders", "user_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("reminders", "channel_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("scheduled_tasks", "guild_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=True)
    op.alter_column("moderation_records", "guild_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("moderation_records", "user_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("moderation_records", "moderator_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("custom_commands", "guild_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("knowledge", "guild_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=True)
    op.alter_column("knowledge", "user_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=True)
    op.alter_column("guild_config", "guild_id", existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)


def downgrade() -> None:
    pass
