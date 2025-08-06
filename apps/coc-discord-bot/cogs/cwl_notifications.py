import discord
from discord.ext import tasks, commands
import asyncio
import logging
from datetime import datetime
import json
import os
from utils_supercell import get_current_cwl_war
import config

logger = logging.getLogger("cwl_notifications")
CACHE_PATH = os.path.join(os.path.dirname(__file__), "../data/cwl_notification_cache.json")

def load_cache():
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"last_war_state": None, "last_player_stars": {}}

def save_cache(cache):
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f)
    except Exception as e:
        logger.error(f"Failed to save CWL notification cache: {e}")

class CWLNotifications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        cache = load_cache()
        self.last_war_state = cache.get("last_war_state")
        self.last_player_stars = cache.get("last_player_stars", {})
        self.cwl_polling_task.start()

    async def cog_unload(self):
        self.cwl_polling_task.cancel()

    @tasks.loop(seconds=45)
    async def cwl_polling_task(self):
        await self.bot.wait_until_ready()
        try:
            clan_tag = config.CLAN_TAG or ""
            if not clan_tag:
                logger.warning("No CLAN_TAG configured for CWL notifications.")
                return
            war_data = get_current_cwl_war(clan_tag)
            if not war_data:
                logger.info("No current CWL war data found.")
                return
            war_state = war_data.get('state')
            war_tag = war_data.get('warTag')
            # Detect war state change
            if war_state != self.last_war_state:
                self.last_war_state = war_state
                await self.send_war_state_notification(war_state, war_tag)
            # Detect new stars for each player
            for member in war_data.get('clan', {}).get('members', []):
                tag = member.get('tag')
                name = member.get('name')
                stars = sum(a.get('stars', 0) for a in member.get('attacks', []))
                prev_stars = self.last_player_stars.get(tag, 0)
                if stars > prev_stars:
                    await self.send_star_notification(name, tag, stars, prev_stars)
                self.last_player_stars[tag] = stars
            # Save cache after each poll
            save_cache({
                "last_war_state": self.last_war_state,
                "last_player_stars": self.last_player_stars
            })
        except Exception as e:
            logger.error(f"CWL polling error: {e}")

    async def send_war_state_notification(self, state, war_tag):
        channel = self.bot.get_channel(config.CWL_REWARDS_CHANNEL_ID)
        if not channel:
            logger.warning("CWL rewards channel not found!")
            return
        if state == 'inWar':
            await channel.send(f"⚔️ A new CWL war has started! War tag: `{war_tag}`")
        elif state == 'warEnded':
            await channel.send(f"✅ The current CWL war has ended! War tag: `{war_tag}`. Leaderboard will auto-update.")
        elif state == 'preparation':
            await channel.send(f"⏳ CWL war preparation day has begun. Get ready!")

    async def send_star_notification(self, name, tag, stars, prev_stars):
        channel = self.bot.get_channel(config.CWL_REWARDS_CHANNEL_ID)
        if not channel:
            logger.warning("CWL rewards channel not found!")
            return
        if stars >= 8 and prev_stars < 8:
            await channel.send(f"🌟 **{name}** has reached **8+ stars** in CWL! Consider subbing if needed.")
        else:
            await channel.send(f"⭐ **{name}** earned a new star in CWL! Total: {stars}")

    @discord.app_commands.command(name="sync_cwl_commands", description="Sync CWL notification slash commands for this server (admin only).")
    @commands.is_owner()
    async def sync_cwl_commands(self, interaction: discord.Interaction):
        """
        Sync only the CWL notification commands for this guild. Owner/admin only.
        """
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            synced = await self.bot.tree.sync(guild=interaction.guild)
            # Filter for CWL commands only (optional, for feedback)
            cwl_cmds = [cmd for cmd in synced if cmd.name.startswith("test_cwl_notification") or cmd.name.startswith("sync_cwl_commands")]
            await interaction.followup.send(f"✅ Synced {len(cwl_cmds)} CWL notification command(s) for this server.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to sync CWL commands: {e}", ephemeral=True)

    @discord.app_commands.command(name="test_cwl_notification", description="Send a test CWL notification to the configured channel.")
    async def test_cwl_notification(self, interaction: discord.Interaction):
        channel = self.bot.get_channel(config.CWL_REWARDS_CHANNEL_ID)
        if channel:
            await channel.send("✅ Test notification: CWL notifications are working!")
            await interaction.response.send_message("Test notification sent to CWL rewards channel.", ephemeral=True)
        else:
            await interaction.response.send_message("CWL rewards channel not found. Check the channel ID in config.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CWLNotifications(bot))
