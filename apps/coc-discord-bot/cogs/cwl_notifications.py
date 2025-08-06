import discord
from discord.ext import tasks, commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime
import json
import os
from utils_supercell import get_current_cwl_war
import config

ADMIN_DISCORD_ID = config.ADMIN_DISCORD_ID
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
            
            # Only send war state notification if state actually changed AND we have a previous state
            if war_state != self.last_war_state and self.last_war_state is not None:
                logger.info(f"War state changed from {self.last_war_state} to {war_state}")
                await self.send_war_state_notification(war_state, war_tag)
            elif self.last_war_state is None:
                logger.info(f"Initial war state detected: {war_state} (no notification sent)")
            
            # Update war state
            self.last_war_state = war_state
            
            # Detect new stars for each player
            if war_state in ["inWar", "warEnded"]:  # Only track stars during war
                clan_members = war_data.get('clan', {}).get('members', [])
                for member in clan_members:
                    tag = member.get('tag')
                    name = member.get('name')
                    attacks = member.get('attacks', [])
                    
                    # Calculate total stars from all attacks
                    total_stars = sum(attack.get('stars', 0) for attack in attacks)
                    prev_stars = self.last_player_stars.get(tag, 0)
                    
                    # Send notification for star increases (including 8+ star achievements)
                    if total_stars > prev_stars:
                        logger.info(f"{name} increased stars from {prev_stars} to {total_stars}")
                        await self.send_star_notification(name, tag, total_stars, prev_stars)
                    
                    # Update stored stars
                    self.last_player_stars[tag] = total_stars
            
            # Save cache after each poll
            save_cache({
                "last_war_state": self.last_war_state,
                "last_player_stars": self.last_player_stars
            })
            
        except Exception as e:
            logger.error(f"CWL polling error: {e}")
            import traceback
            logger.error(traceback.format_exc())

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
            
        stars_gained = stars - prev_stars
        
        if stars >= 8 and prev_stars < 8:
            await channel.send(f"🌟 **{name}** has reached **8+ stars** ({stars} total) in CWL! Consider subbing if needed.")
        elif stars_gained > 1:
            await channel.send(f"⭐ **{name}** gained {stars_gained} stars! Total: {stars} stars")
        else:
            await channel.send(f"⭐ **{name}** earned a new star! Total: {stars} stars")

    @discord.app_commands.command(name="force_sync", description="Force sync all commands globally (admin only).")
    @commands.is_owner()
    async def force_sync(self, interaction: discord.Interaction):
        """Force sync all commands globally (admin only)"""
        if interaction.user.id != int(ADMIN_DISCORD_ID):
            await interaction.response.send_message("❌ Only the bot owner can use this command.", ephemeral=True)
            return
        
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Clear existing commands first
            self.bot.tree.clear_commands(guild=None)
            self.bot.tree.clear_commands(guild=interaction.guild)
            
            # Force global sync
            global_synced = await self.bot.tree.sync()
            
            # Force guild sync
            guild_synced = await self.bot.tree.sync(guild=interaction.guild)
            
            await interaction.followup.send(
                f"🔄 **FORCE SYNC COMPLETE**\n"
                f"• Global: {len(global_synced)} command(s)\n"
                f"• Guild: {len(guild_synced)} command(s)\n"
                f"• Commands cleared and re-synced\n"
                f"• May take 5-15 minutes to appear in Discord",
                ephemeral=True
            )
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error in force sync: {str(e)}", ephemeral=True)

    @discord.app_commands.command(name="quick_sync", description="Quick sync without rate limits (Owner only)")
    async def quick_sync(self, interaction: discord.Interaction):
        """Quick sync that just refreshes the command tree without API calls"""
        if interaction.user.id != int(ADMIN_DISCORD_ID):
            await interaction.response.send_message("❌ Only the bot owner can use this command.", ephemeral=True)
            return
        
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Just refresh the command tree locally without syncing to Discord
            # This can help if commands are cached but not showing
            await self.bot.tree.fetch_commands(guild=interaction.guild)
            
            await interaction.followup.send(
                f"✅ **Quick sync complete!**\n"
                f"• Refreshed local command cache\n"
                f"• No API calls = no rate limits\n"
                f"• Commands should be available immediately\n"
                f"📝 Use `/sync_cwl_commands` if this doesn't work.",
                ephemeral=True
            )
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error in quick sync: {str(e)}", ephemeral=True)

    @discord.app_commands.command(name="sync_cwl_commands", description="Manually sync CWL commands (Owner only)")
    async def sync_cwl_commands(self, interaction: discord.Interaction):
        """
        Sync only the CWL notification commands for this guild. Owner/admin only.
        Guild-only sync to avoid global rate limits.
        """
        if interaction.user.id != int(ADMIN_DISCORD_ID):
            await interaction.response.send_message("❌ Only the bot owner can use this command.", ephemeral=True)
            return
            
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            # Try guild sync first, fallback to global if it fails
            try:
                guild_synced = await self.bot.tree.sync(guild=interaction.guild)
                guild_name = interaction.guild.name if interaction.guild else "Unknown Server"
                await interaction.followup.send(
                    f"✅ **Guild sync complete!**\n"
                    f"• Synced {len(guild_synced)} command(s) to **{guild_name}**\n"
                    f"• Guild-only sync = faster + no global rate limits\n" 
                    f"• Commands available in 1-2 minutes\n"
                    f"📝 Try `/cwl_test` to verify it worked!",
                    ephemeral=True
                )
            except Exception as guild_error:
                # Guild sync failed, try global sync
                global_synced = await self.bot.tree.sync()
                await interaction.followup.send(
                    f"⚠️ **Guild sync failed, used global sync instead**\n"
                    f"• Synced {len(global_synced)} command(s) globally\n"
                    f"• Commands will appear in ALL servers the bot is in\n"
                    f"• Commands available in 1-2 minutes\n"
                    f"📝 Try `/cwl_test` to verify it worked!\n"
                    f"• Guild error: {str(guild_error)[:100]}",
                    ephemeral=True
                )
        except discord.HTTPException as e:
            if "rate limit" in str(e).lower():
                await interaction.followup.send(
                    f"⏳ **Rate limited!** Try again in a few minutes.\n"
                    f"💡 Use `/quick_sync` for immediate refresh without API calls.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(f"❌ Failed to sync CWL commands: {e}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to sync CWL commands: {e}", ephemeral=True)

    @discord.app_commands.command(name="reset_cwl_cache", description="Reset CWL notification cache (Owner only)")
    async def reset_cwl_cache(self, interaction: discord.Interaction):
        """Reset the CWL notification cache (Owner only)"""
        if interaction.user.id != int(ADMIN_DISCORD_ID):
            await interaction.response.send_message("❌ Only the bot owner can use this command.", ephemeral=True)
            return
        
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Reset the cache
            self.last_war_state = None
            self.last_player_stars = {}
            
            # Save empty cache
            save_cache({
                "last_war_state": None,
                "last_player_stars": {}
            })
            
            await interaction.followup.send(
                "✅ **CWL cache reset!**\n"
                "• War state cleared\n"
                "• Player stars cleared\n"
                "• Next poll will treat everything as 'new'",
                ephemeral=True
            )
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error resetting cache: {str(e)}", ephemeral=True)

    @discord.app_commands.command(name="cwl_test", description="Simple test - verify CWL system is working")
    async def cwl_test(self, interaction: discord.Interaction):
        """Simple test command to verify the CWL system is working"""
        await interaction.response.send_message("✅ CWL Notification system is online and working!", ephemeral=True)

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
