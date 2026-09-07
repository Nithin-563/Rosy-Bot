"""Discord permission helpers — Rosy never bypasses Discord's own permissions."""
from __future__ import annotations

from discord import Member, PermissionOverwrite  # type: ignore


def is_moderator(member: Member | None) -> bool:
    """True if the member can manage the guild (kick/ban/manage_messages)."""
    if member is None:
        return False
    if member.guild_permissions.administrator:
        return True
    if member.guild_permissions.manage_guild:
        return True
    if member.guild_permissions.manage_messages:
        return True
    if member.guild_permissions.kick_members or member.guild_permissions.ban_members:
        return True
    return False


def is_admin(member: Member | None) -> bool:
    if member is None:
        return False
    return member.guild_permissions.administrator or member.guild_permissions.manage_guild


def can_moderate(member: Member | None, target: Member | None) -> bool:
    """Moderator cannot act on higher or equal hierarchy role members."""
    if not is_moderator(member):
        return False
    if target is None or member is None:
        return True
    return member.top_role > target.top_role
