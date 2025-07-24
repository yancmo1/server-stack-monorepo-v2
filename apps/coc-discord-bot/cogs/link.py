import discord
from discord import app_commands, ui
from discord.ext import commands
import logging

import config
import database_optimized as database

logger = logging.getLogger("link")

GUILD_ID = discord.Object(id=config.GUILD_ID)

class LinkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ...existing code...
        # Move all command/event logic here

async def setup(bot):
    await bot.add_cog(LinkCog(bot))
