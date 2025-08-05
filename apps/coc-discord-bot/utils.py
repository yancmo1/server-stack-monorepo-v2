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
        if not join_date_str or join_date_str in ("None", "null", ""):
            return False
        
        join_date_str = str(join_date_str)
        
        # Handle different date formats
        if 'T' in join_date_str:  # ISO format with time
            join_date = datetime.strptime(join_date_str.split('T')[0], "%Y-%m-%d")
        elif ' ' in join_date_str:  # PostgreSQL timestamp format
            join_date = datetime.strptime(join_date_str.split(' ')[0], "%Y-%m-%d")
        else:
            join_date = datetime.strptime(join_date_str, "%Y-%m-%d")
        
        return (datetime.utcnow() - join_date).days < 60
    except Exception:
        return False

def format_last_bonus(date_str):
    if not date_str or date_str in ("None", "null", ""):
        return "Never"
    try:
        date_str = str(date_str)
        
        # Handle different date formats
        if 'T' in date_str:  # ISO format with time
            date_obj = datetime.strptime(date_str.split('T')[0], "%Y-%m-%d")
        elif ' ' in date_str:  # PostgreSQL timestamp format
            date_obj = datetime.strptime(date_str.split(' ')[0], "%Y-%m-%d")
        else:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        return date_obj.strftime("%b %d, %Y")
    except Exception:
        return "Never"

def days_ago(join_date_str):
    try:
        if not join_date_str or join_date_str in ("None", "null", ""):
            return "?"
        
        join_date_str = str(join_date_str)
        
        # Handle different date formats
        if 'T' in join_date_str:  # ISO format with time
            join_date = datetime.strptime(join_date_str.split('T')[0], "%Y-%m-%d")
        elif ' ' in join_date_str:  # PostgreSQL timestamp format
            join_date = datetime.strptime(join_date_str.split(' ')[0], "%Y-%m-%d")
        else:
            join_date = datetime.strptime(join_date_str, "%Y-%m-%d")
        
        return (datetime.utcnow() - join_date).days
    except Exception:
        return "?"

