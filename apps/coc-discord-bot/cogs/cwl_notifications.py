import discord
from discord.ext import tasks, commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime, timezone
import json
from typing import Optional
import os
from utils_supercell import get_current_cwl_war, get_cwl_round_schedule
import config

ADMIN_DISCORD_ID = config.ADMIN_DISCORD_ID
logger = logging.getLogger("cwl_notifications")
CACHE_PATH = os.path.join(os.path.dirname(__file__), "../data/cwl_notification_cache.json")

def load_cache():
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "last_war_state": None,
            "last_player_stars": {},
            "on_deck_sent": {}
        }

def save_cache(cache):
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f)
    except Exception as e:
        logger.error(f"Failed to save CWL notification cache: {e}")

from database_optimized import get_optimized_connection as _db_conn

class CWLNotifications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        cache = load_cache()
        self.last_war_state = cache.get("last_war_state")
        self.last_player_stars = cache.get("last_player_stars", {})
        # Track which ON DECK intervals have been announced per warTag, e.g., {"#WAR123": [60,30,15]}
        self.on_deck_sent = cache.get("on_deck_sent", {})
        self.cwl_polling_task.start()

    def _get_discord_ids_for_coc(self, tag: str, name: Optional[str] = None):
        ids = set()
        try:
            with _db_conn() as conn:
                cur = conn.cursor()
                for key in [tag, name]:
                    if not key:
                        continue
                    try:
                        cur.execute(
                            "SELECT discord_id FROM discord_coc_links WHERE LOWER(coc_name_or_tag) = LOWER(%s)",
                            (key,),
                        )
                        rows = cur.fetchall() or []
                        for r in rows:
                            # r is likely a tuple; first column is discord_id
                            try:
                                ids.add(str(r[0]))
                            except Exception:
                                continue
                    except Exception:
                        continue
        except Exception:
            return []
        return list(ids)

    async def cog_unload(self):
        self.cwl_polling_task.cancel()

    @tasks.loop(minutes=5)
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
                # Delay state change announcements by 5 minutes to reduce instant pings
                asyncio.create_task(self.delayed_war_state_notification(war_state, war_tag, delay_seconds=300))
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
            
            # Optional: near end-of-war on-deck alert (~30 minutes left)
            try:
                end_str = war_data.get('endTime')
                if end_str and war_state == 'inWar':
                    # CoC datetime format like 20250105T123456.000Z
                    end_dt = datetime.strptime(end_str[:15], '%Y%m%dT%H%M%S').replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    remaining = (end_dt - now).total_seconds()
                    # Send ON DECK reminders at 60, 30, and 15 minutes remaining (only once each per war)
                    remaining_minutes = int(remaining // 60)
                    for threshold in (60, 30, 15):
                        if remaining_minutes <= threshold and remaining_minutes >= 0:
                            sent_set = set(self.on_deck_sent.get(war_tag, []))
                            if threshold not in sent_set:
                                await self.send_on_deck_alert(war_data, threshold)
                                sent_set.add(threshold)
                                self.on_deck_sent[war_tag] = sorted(list(sent_set))
            except Exception:
                pass

            # Save cache after each poll
            save_cache({
                "last_war_state": self.last_war_state,
                "last_player_stars": self.last_player_stars,
                "on_deck_sent": self.on_deck_sent
            })
            
        except Exception as e:
            logger.error(f"CWL polling error: {e}")
            import traceback
            logger.error(traceback.format_exc())

    async def delayed_war_state_notification(self, state, war_tag, delay_seconds: int = 300):
        try:
            await asyncio.sleep(delay_seconds)
        except Exception:
            pass
        channel = self.bot.get_channel(config.CWL_REWARDS_CHANNEL_ID)
        if not channel:
            logger.warning("CWL rewards channel not found!")
            return
        if state == 'inWar':
            await channel.send(f"⚔️ A new CWL war has started! War tag: `{war_tag}`")
        elif state == 'warEnded':
            await self.post_war_end_summary()
        elif state == 'preparation':
            await channel.send(f"⏳ CWL war preparation day has begun. Get ready!")

    # Backwards-compat alias (in case other cogs call it)
    async def send_war_state_notification(self, state, war_tag):
        channel = self.bot.get_channel(config.CWL_REWARDS_CHANNEL_ID)
        if not channel:
            logger.warning("CWL rewards channel not found!")
            return
        if state == 'inWar':
            await channel.send(f"⚔️ A new CWL war has started! War tag: `{war_tag}`")
        elif state == 'warEnded':
            # Post a concise war-ended summary
            await self.post_war_end_summary()
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
            # Attempt to DM the linked Discord user if we have a mapping
            try:
                discord_ids = self._get_discord_ids_for_coc(tag, name)
                for did in discord_ids:
                    try:
                        user = await self.bot.fetch_user(int(did))
                        if user:
                            await user.send(f"🌟 Congrats! You hit **{stars}** stars in CWL. Keep it up!")
                    except Exception:
                        continue
            except Exception as dm_err:
                logger.warning(f"Could not DM for 8+ stars: {dm_err}")
        elif stars_gained > 1:
            await channel.send(f"⭐ **{name}** gained {stars_gained} stars! Total: {stars} stars")
        else:
            await channel.send(f"⭐ **{name}** earned a new star! Total: {stars} stars")

    async def send_on_deck_alert(self, war_data, threshold_minutes: int):
        channel = self.bot.get_channel(config.CWL_REWARDS_CHANNEL_ID)
        if not channel:
            return
        clan = war_data.get('clan', {})
        members = clan.get('members', [])
        pending = [m.get('name') for m in members if not m.get('attacks')]
        if not pending:
            return
        names = ', '.join(pending[:10]) + ('…' if len(pending) > 10 else '')
        if threshold_minutes == 60:
            msg = f"⏰ Awaiting CWL Attack - 1 hour remaining - {names}"
        elif threshold_minutes == 30:
            msg = f"⏳ Awaiting CWL Attack - 30 minutes remaining - {names}"
        else:
            msg = f"🚨 Awaiting CWL Attack - Final 15 minutes - {names}"
        await channel.send(f"📣 {msg}")

    async def post_war_end_summary(self):
        channel = self.bot.get_channel(config.CWL_REWARDS_CHANNEL_ID)
        if not channel:
            return
        # Build a simple summary from cached stars
        if not self.last_player_stars:
            await channel.send("✅ CWL war ended. Stars updated.")
            return
        # Sort by stars desc
        sorted_players = sorted(self.last_player_stars.items(), key=lambda kv: kv[1], reverse=True)
        top = sorted_players[:5]
        lines = []
        for tag, stars in top:
            lines.append(f"• <{tag}> — {stars}⭐")
        text = "\n".join(lines) if lines else "(no attacks recorded)"
        await channel.send(f"✅ War ended — Top performers:\n{text}")

    @discord.app_commands.command(name="cwl_schedule", description="Show current CWL round schedule")
    async def cwl_schedule(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            clan_tag = config.CLAN_TAG or ""
            schedule = get_cwl_round_schedule(clan_tag)
            if not schedule:
                await interaction.followup.send("No CWL schedule found.", ephemeral=True)
                return
            lines = []
            for s in schedule:
                lines.append(f"Round {s['round']}: {s.get('state','?')} — start {s.get('startTime','?')} end {s.get('endTime','?')}")
            await interaction.followup.send("\n".join(lines)[:1800], ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)

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
            self.on_deck_sent = {}
            
            # Save empty cache
            save_cache({
                "last_war_state": None,
                "last_player_stars": {},
                "on_deck_sent": {}
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

    @discord.app_commands.command(name="cwl_ping", description="Simple ping command for CWL system - everyone can use")
    async def cwl_ping_command(self, interaction: discord.Interaction):
        """Simple ping command that everyone can see and use"""
        await interaction.response.send_message("🏓 Pong! CWL Bot is working!", ephemeral=True)

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
