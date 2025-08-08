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
class CWLGroup(app_commands.Group):
    """CWL (Clan War League) commands"""
    def __init__(self):
        super().__init__(name="cwl", description="Clan War League commands")

    @app_commands.command(name="fetch_stars", description="Fetch and update CWL stars from Clash of Clans API")
    async def fetch_stars(self, interaction: discord.Interaction):
        """Fetch CWL stars from the API and update database"""
        await interaction.response.send_message("⏳ This command is being migrated to the new CWL group system. Please use the individual `/fetch_cwl_stars` command for now.", ephemeral=True)

    @app_commands.command(name="leaderboard", description="Show current CWL stars leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        """Show CWL stars leaderboard"""
        await interaction.response.send_message("⏳ This command is being migrated to the new CWL group system. Please use the individual `/cwl_leaderboard` command for now.", ephemeral=True)

    @app_commands.command(name="schedule", description="Show current CWL round schedule")
    async def schedule(self, interaction: discord.Interaction):
        """Show CWL round schedule"""
        await interaction.response.send_message("⏳ This command is being migrated to the new CWL group system. Please use the individual `/cwl_schedule` command for now.", ephemeral=True)

    @app_commands.command(name="history", description="View CWL season history")
    async def history(self, interaction: discord.Interaction, player_name: Optional[str] = None, season_year: Optional[int] = None, season_month: Optional[int] = None):
        """View CWL history"""
        await interaction.response.send_message("⏳ This command is being migrated to the new CWL group system. Please use the individual `/cwl_history` command for now.", ephemeral=True)

    @app_commands.command(name="debug_api", description="Debug CWL API response (Admin only)")
    async def debug_api(self, interaction: discord.Interaction):
        """Debug the CWL API response"""
        if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ This command requires admin permissions.", ephemeral=True)
            return
        await interaction.response.send_message("⏳ This command is being migrated to the new CWL group system. Please use the individual `/debug_cwl_api` command for now.", ephemeral=True)

    @app_commands.command(name="clear_data", description="Clear current CWL stars and missed attacks (Admin only)")
    async def clear_data(self, interaction: discord.Interaction):
        """Clear current CWL season data"""
        if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ This command requires admin permissions.", ephemeral=True)
            return
        await interaction.response.send_message("⏳ This command is being migrated to the new CWL group system. Please use the individual `/clear_cwl_data` command for now.", ephemeral=True)

    @app_commands.command(name="reset_wars", description="Reset processed wars tracking (Admin only)")
    async def reset_wars(self, interaction: discord.Interaction):
        """Reset the processed wars table"""
        if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ This command requires admin permissions.", ephemeral=True)
            return
        await interaction.response.send_message("⏳ This command is being migrated to the new CWL group system. Please use the individual `/reset_processed_wars` command for now.", ephemeral=True)

    @app_commands.command(name="reset_cache", description="Reset CWL notification cache (Admin only)")
    async def reset_cache(self, interaction: discord.Interaction):
        """Reset the CWL notification cache"""
        if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ This command requires admin permissions.", ephemeral=True)
            return
        await interaction.response.send_message("⏳ This command is being migrated to the new CWL group system. Please use the individual `/reset_cwl_cache` command for now.", ephemeral=True)

    @app_commands.command(name="sync_commands", description="Manually sync CWL commands (Owner only)")
    async def sync_commands(self, interaction: discord.Interaction):
        """Sync CWL commands"""
        if interaction.user.id != int(config.ADMIN_DISCORD_ID):
            await interaction.response.send_message("❌ Only the bot owner can use this command.", ephemeral=True)
            return
        await interaction.response.send_message("⏳ This command is being migrated to the new CWL group system. Please use the individual `/sync_cwl_commands` command for now.", ephemeral=True)

    @app_commands.command(name="test", description="Test CWL system functionality")
    async def test(self, interaction: discord.Interaction):
        """Test CWL system"""
        await interaction.response.send_message("⏳ This command is being migrated to the new CWL group system. Please use the individual `/cwl_test` command for now.", ephemeral=True)

    @app_commands.command(name="test_notification", description="Send a test CWL notification")
    async def test_notification(self, interaction: discord.Interaction):
        """Send a test notification"""
        await interaction.response.send_message("⏳ This command is being migrated to the new CWL group system. Please use the individual `/test_cwl_notification` command for now.", ephemeral=True)

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
        self.bot.tree.add_command(CWLGroup())
        # ...existing code...
        # Move all command/event logic here

async def setup(bot):
    await bot.add_cog(CommandGroupsCog(bot))
