import discord
from discord.ext import commands
from discord import app_commands
import logging

from config import DISCORD_ROLE_NAMES
import database_optimized as database
from database_optimized import (
    get_all_discord_coc_links_with_roles,
    get_clan_role_by_coc_name_or_tag,
)

logger = logging.getLogger("rolesync")

ROLE_PRIORITY = ["Leader", "Co-Leader", "Elder", "Member"]


class RoleSyncCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ...existing command/event logic...


async def setup(bot):
    await bot.add_cog(RoleSyncCog(bot))
