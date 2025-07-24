"""
Command Groups for better organization
This approach uses Discord's command groups to organize related commands
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import logging

import config
import database_optimized as database
from config import is_leader_or_admin

# Set up logging
logger = logging.getLogger("command_groups")

GUILD_ID = config.GUILD_ID

@app_commands.guilds(discord.Object(id=GUILD_ID))
class AdminGroup(app_commands.Group):
    """Admin-only commands"""
    def __init__(self):
        super().__init__(name="admin", description="Administrator commands")

    @app_commands.command(name="ping", description="Test bot connectivity")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("🏓 Pong! The bot is alive.", ephemeral=True)

    @app_commands.command(name="api_test", description="Test CoC API connectivity")
    async def api_test(self, interaction: discord.Interaction):
        import requests
        import urllib.parse
        from config import SUPERCELL_API_TOKEN, CLAN_TAG
        headers = {
            "Authorization": f"Bearer {SUPERCELL_API_TOKEN}",
            "Accept": "application/json"
        }
        tag = str(CLAN_TAG or "").strip()
        if not tag:
            await interaction.response.send_message("❌ CLAN_TAG is not set in config.", ephemeral=True)
            return
        encoded_tag = urllib.parse.quote(tag, safe='')
        url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}"
        try:
            response = requests.get(url, headers=headers, timeout=10, verify=not config.DEV_MODE)
            if response.status_code == 200:
                data = response.json()
                clan_name = data.get("name", "Unknown Clan")
                await interaction.response.send_message(f"✅ CoC API is reachable! Clan: **{clan_name}**", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ CoC API returned status {response.status_code}: {response.text}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error connecting to CoC API: {e}", ephemeral=True)

class CommandGroupsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.tree.add_command(AdminGroup())
        # ...existing code...
        # Move all command/event logic here

async def setup(bot):
    await bot.add_cog(CommandGroupsCog(bot))
