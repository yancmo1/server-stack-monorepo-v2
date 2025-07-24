"""
Shared utility functions for role checks, date formatting, and other helpers.
"""
import config
from datetime import datetime

def has_any_role_id(interaction, allowed_role_ids):
    if not interaction.guild:
        return False
    member = interaction.guild.get_member(interaction.user.id)
    if not member:
        return False
    return any(role.id in allowed_role_ids for role in member.roles)

def is_admin(interaction):
    return has_any_role_id(interaction, [config.ADMIN_ROLE_ID])

def is_admin_leader_co_leader(interaction):
    return has_any_role_id(interaction, [config.ADMIN_ROLE_ID, config.LEADER_ROLE_ID, config.CO_LEADER_ROLE_ID])

def is_admin_leader_co_elder_member(interaction):
    return has_any_role_id(interaction, [config.ADMIN_ROLE_ID, config.LEADER_ROLE_ID, config.CO_LEADER_ROLE_ID, config.ELDER_ROLE_ID, config.MEMBER_ROLE_ID])

def is_newbie(join_date_str):
    try:
        join_date = datetime.strptime(join_date_str, "%Y-%m-%d")
        return (datetime.utcnow() - join_date).days < 60
    except Exception:
        return False

def format_last_bonus(date_str):
    if not date_str or date_str in ("None", "null"):
        return "Never"
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %d, %Y")
    except Exception:
        return "Never"

def days_ago(join_date_str):
    try:
        join_date = datetime.strptime(join_date_str, "%Y-%m-%d")
        return (datetime.utcnow() - join_date).days
    except Exception:
        return "?"

