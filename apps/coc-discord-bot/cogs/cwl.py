import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from typing import Optional, List

import config
import database_optimized as database
from logging_config import get_logger
from utils import (
    has_any_role_id, 
    is_admin, 
    is_admin_leader_co_leader, 
    is_admin_leader_co_elder_member
)

GUILD_ID = discord.Object(id=config.GUILD_ID)
logger = get_logger(__name__)

class CWLResetConfirmView(discord.ui.View):
    """Confirmation view for CWL reset with buttons"""
    
    def __init__(self, cwl_players, total_stars, total_missed):
        super().__init__(timeout=300)  # 5 minute timeout
        self.cwl_players = cwl_players
        self.total_stars = total_stars
        self.total_missed = total_missed
        
    @discord.ui.button(label="✅ Confirm Reset", style=discord.ButtonStyle.danger)
    async def confirm_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Perform the actual CWL reset"""
        await interaction.response.defer()
        
        try:
            # Save current season data to history before reset
            from datetime import datetime
            now = datetime.now()
            
            # Save season snapshot
            snapshot_result = database.save_cwl_season_snapshot(now.year, now.month)
            
            # Reset all CWL stats
            reset_count = database.reset_all_cwl_stars()
            missed_reset_count = database.reset_all_missed_attacks()
            
            # Create success embed
            embed = discord.Embed(
                title="✅ CWL Stats Reset Complete",
                description=f"CWL statistics have been reset for new season by {interaction.user.display_name}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 Reset Summary",
                value=f"**Players reset:** {len(self.cwl_players)}\n"
                      f"**Stars reset:** {self.total_stars}\n"
                      f"**Missed attacks reset:** {self.total_missed}\n"
                      f"**Database rows updated:** {reset_count + missed_reset_count}",
                inline=False
            )
            
            # Add history save info
            embed.add_field(
                name="💾 Season Data Archived",
                value=f"**Season:** {now.year}-{now.month:02d}\n"
                      f"**Players saved:** {snapshot_result['players_saved']}\n"
                      f"**Historical data preserved for trend analysis**",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Ready for New Season",
                value="All CWL stars and missed attacks have been reset to 0.\n"
                      "Players are ready for the new CWL season!",
                inline=False
            )
            
            embed.set_footer(text=f"Reset performed on {datetime.now().strftime('%Y-%m-%d at %H:%M UTC')}")
            
            # Disable all buttons
            self.clear_items()
            
            await interaction.edit_original_response(embed=embed, view=self)
            
            # Log the reset with history info
            logger.info(f"CWL stats reset completed by {interaction.user.display_name}: "
                       f"{len(self.cwl_players)} players, {self.total_stars} stars, {self.total_missed} missed attacks. "
                       f"Historical data saved for {now.year}-{now.month:02d}")
                       
        except Exception as e:
            logger.error(f"Error performing CWL reset: {e}")
            embed = discord.Embed(
                title="❌ Reset Failed",
                description=f"An error occurred during the reset: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=embed, view=None)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the reset operation"""
        embed = discord.Embed(
            title="❌ Reset Cancelled",
            description="CWL reset has been cancelled. No changes were made.",
            color=discord.Color.red()
        )
        
        # Clear buttons
        self.clear_items()
            
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_timeout(self):
        """Handle timeout"""
        self.clear_items()

logger = get_logger(__name__)

class CWLCog(commands.Cog):
    """CWL (Clan War League) management commands"""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="cwl_status",
        description="Show current CWL status and player participation — Admin, Leader, Co-Leader, Elder, Member"
    )
    @app_commands.check(is_admin_leader_co_elder_member)
    @app_commands.guilds(GUILD_ID)
    async def cwl_status(self, interaction: discord.Interaction):
        """Show current CWL status"""
        logger.info("[COMMAND] /cwl_status invoked")
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get player data to show CWL-related stats
            players = database.get_player_data()
            
            if not players:
                await interaction.followup.send("❌ No player data available", ephemeral=True)
                return
            
            # Filter for players with CWL activity
            cwl_players = [p for p in players if p.get("cwl_stars", 0) > 0 or p.get("missed_attacks", 0) > 0]
            
            embed = discord.Embed(
                title="🏆 CWL Status Overview",
                description=f"Current CWL participation and performance",
                color=discord.Color.gold()
            )
            
            # Summary stats
            total_players = len(players)
            active_cwl = len(cwl_players)
            total_stars = sum(p.get("cwl_stars", 0) for p in players)
            total_missed = sum(p.get("missed_attacks", 0) for p in players)
            
            embed.add_field(
                name="📊 CWL Summary",
                value=f"**Total Players:** {total_players}\n"
                      f"**CWL Participants:** {active_cwl}\n"
                      f"**Total Stars:** {total_stars}\n"
                      f"**Total Missed Attacks:** {total_missed}",
                inline=False
            )
            
            # Top performers (by stars)
            if cwl_players:
                top_performers = sorted(cwl_players, key=lambda p: p.get("cwl_stars", 0), reverse=True)[:5]
                top_text = []
                for i, player in enumerate(top_performers, 1):
                    stars = player.get("cwl_stars", 0)
                    missed = player.get("missed_attacks", 0)
                    top_text.append(f"{i}. {player.get('name', 'Unknown')} - {stars} ⭐ ({missed} missed)")
                
                embed.add_field(
                    name="🌟 Top Performers",
                    value="\n".join(top_text) if top_text else "No CWL activity recorded",
                    inline=False
                )
            
            # Players with missed attacks
            missed_players = [p for p in players if p.get("missed_attacks", 0) > 0]
            if missed_players:
                missed_text = []
                for player in sorted(missed_players, key=lambda p: p.get("missed_attacks", 0), reverse=True)[:5]:
                    missed = player.get("missed_attacks", 0)
                    missed_text.append(f"• {player.get('name', 'Unknown')} - {missed} missed")
                
                embed.add_field(
                    name="⚠️ Missed Attacks",
                    value="\n".join(missed_text) if missed_text else "No missed attacks",
                    inline=False
                )
            
            embed.set_footer(text="Use /player_details <name> for individual player CWL stats")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in cwl_status command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error retrieving CWL status: {e}", ephemeral=True)

    @app_commands.command(
        name="cwl_stars",
        description="Show CWL stars leaderboard — Admin, Leader, Co-Leader, Elder, Member"
    )
    @app_commands.check(is_admin_leader_co_elder_member)
    @app_commands.guilds(GUILD_ID)
    @app_commands.describe(player_name="Show stars for specific player (optional)")
    async def cwl_stars(self, interaction: discord.Interaction, player_name: Optional[str] = None):
        """Show CWL stars leaderboard or specific player stars"""
        logger.info(f"[COMMAND] /cwl_stars invoked for player: {player_name or 'all'}")
        await interaction.response.defer(ephemeral=True)
        
        try:
            players = database.get_player_data()
            
            if player_name:
                # Show specific player
                target_player = None
                for player in players:
                    if player.get("name", "").lower() == player_name.lower():
                        target_player = player
                        break
                
                if not target_player:
                    await interaction.followup.send(f"❌ Player '{player_name}' not found", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title=f"⭐ CWL Stars: {target_player.get('name', 'Unknown')}",
                    color=discord.Color.blue()
                )
                
                stars = target_player.get("cwl_stars", 0)
                missed = target_player.get("missed_attacks", 0)
                bonus_count = target_player.get("bonus_count", 0)
                
                embed.add_field(
                    name="CWL Performance",
                    value=f"**Stars:** {stars} ⭐\n"
                          f"**Missed Attacks:** {missed}\n"
                          f"**CWL Bonuses:** {bonus_count}",
                    inline=False
                )
                
                # Calculate performance rating
                if stars >= 8 and missed == 0:
                    rating = "🟢 Excellent"
                elif stars >= 6 and missed <= 1:
                    rating = "🟡 Good"
                elif stars >= 4:
                    rating = "🟠 Average"
                else:
                    rating = "🔴 Needs Improvement"
                
                embed.add_field(
                    name="Performance Rating",
                    value=rating,
                    inline=False
                )
                
            else:
                # Show leaderboard
                embed = discord.Embed(
                    title="⭐ CWL Stars Leaderboard",
                    description="Current CWL star rankings",
                    color=discord.Color.gold()
                )
                
                # Get players with CWL activity
                cwl_players = [p for p in players if p.get("cwl_stars", 0) > 0 or p.get("missed_attacks", 0) > 0]
                
                if not cwl_players:
                    embed.add_field(
                        name="No CWL Data",
                        value="No CWL activity recorded yet this season.",
                        inline=False
                    )
                else:
                    # Sort by stars (desc), then by missed attacks (asc)
                    cwl_players.sort(key=lambda p: (-p.get("cwl_stars", 0), p.get("missed_attacks", 0)))
                    
                    # Top 15 players
                    leaderboard = []
                    for i, player in enumerate(cwl_players[:15], 1):
                        name = player.get("name", "Unknown")
                        stars = player.get("cwl_stars", 0)
                        missed = player.get("missed_attacks", 0)
                        
                        # Add performance indicator
                        if stars >= 8 and missed == 0:
                            indicator = "🟢"
                        elif stars >= 6 and missed <= 1:
                            indicator = "🟡"
                        elif missed > 2:
                            indicator = "🔴"
                        else:
                            indicator = "⚪"
                        
                        leaderboard.append(f"{i:2d}. {indicator} {name} - {stars} ⭐ ({missed} missed)")
                    
                    embed.add_field(
                        name="🏆 Top Performers",
                        value="\n".join(leaderboard) if leaderboard else "No data available",
                        inline=False
                    )
                    
                    # Summary
                    total_stars = sum(p.get("cwl_stars", 0) for p in cwl_players)
                    total_missed = sum(p.get("missed_attacks", 0) for p in cwl_players)
                    avg_stars = total_stars / len(cwl_players) if cwl_players else 0
                    
                    embed.add_field(
                        name="📊 CWL Statistics",
                        value=f"**Participants:** {len(cwl_players)}\n"
                              f"**Total Stars:** {total_stars}\n"
                              f"**Average Stars:** {avg_stars:.1f}\n"
                              f"**Total Missed:** {total_missed}",
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in cwl_stars command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error retrieving CWL stars: {e}", ephemeral=True)

    @cwl_stars.autocomplete("player_name")
    async def autocomplete_cwl_player_name(self, interaction: discord.Interaction, current: str):
        """Provide autocomplete suggestions for player names"""
        try:
            if hasattr(database, 'get_autocomplete_names'):
                names = database.get_autocomplete_names(current)
                return [app_commands.Choice(name=n, value=n) for n in names[:25]]
            else:
                players = database.get_player_data()
                if current:
                    filtered = [p.get("name", "") for p in players 
                              if current.lower() in p.get("name", "").lower()]
                else:
                    filtered = [p.get("name", "") for p in players]
                return [app_commands.Choice(name=n, value=n) for n in filtered[:25]]
        except Exception:
            return []

    @app_commands.command(
        name="reset_cwl_stats",
        description="Reset CWL stats for new season — Admin, Leader, Co-Leader"
    )
    @app_commands.check(is_admin_leader_co_leader)
    @app_commands.guilds(GUILD_ID)
    async def reset_cwl_stats(self, interaction: discord.Interaction):
        """Reset CWL statistics for new season with button confirmation"""
        logger.info(f"[COMMAND] /reset_cwl_stats invoked by {interaction.user.display_name}")
        await interaction.response.defer(ephemeral=True)
        
        try:
            players = database.get_player_data()
            cwl_players = [p for p in players if p.get("cwl_stars", 0) > 0 or p.get("missed_attacks", 0) > 0]
            
            if not cwl_players:
                await interaction.followup.send("✅ No CWL data to reset.", ephemeral=True)
                return
            
            # Calculate stats for preview
            total_stars = sum(p.get("cwl_stars", 0) for p in cwl_players)
            total_missed = sum(p.get("missed_attacks", 0) for p in cwl_players)
            
            # Show confirmation embed with buttons
            embed = discord.Embed(
                title="⚠️ CWL Reset Confirmation",
                description="Are you sure you want to reset all CWL statistics for a new season?",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="📊 Data to Reset",
                value=f"**Players with CWL data:** {len(cwl_players)}\n"
                      f"**Total stars to reset:** {total_stars}\n"
                      f"**Total missed attacks to reset:** {total_missed}",
                inline=False
            )
            
            # Show top performers that will be reset
            stars_leaders = sorted([p for p in cwl_players if p.get("cwl_stars", 0) > 0], 
                                 key=lambda p: p.get("cwl_stars", 0), reverse=True)[:5]
            if stars_leaders:
                stars_text = []
                for i, player in enumerate(stars_leaders, 1):
                    stars_text.append(f"{i}. **{player['name']}**: ⭐{player.get('cwl_stars', 0)} ❌{player.get('missed_attacks', 0)}")
                
                embed.add_field(
                    name="🏆 Top 5 Current Leaders",
                    value="\n".join(stars_text),
                    inline=False
                )
            
            embed.add_field(
                name="💾 Historical Data Protection",
                value="✅ Current season data will be automatically saved to history before reset\n"
                      "⚠️ This action cannot be undone after confirmation",
                inline=False
            )
            
            # Create confirmation view with buttons
            view = CWLResetConfirmView(cwl_players, total_stars, total_missed)
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in reset_cwl_stats command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while preparing CWL reset.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="cwl_history", description="View CWL season history")
    @app_commands.describe(
        season_year="Year of the season to view (default: all seasons)",
        season_month="Month of the season to view (default: all seasons)", 
        player="View history for specific player only"
    )
    async def cwl_history(self, interaction: discord.Interaction, season_year: Optional[int] = None, season_month: Optional[int] = None, player: Optional[str] = None):
        """View CWL season history and trends"""
        await interaction.response.defer()
        
        try:
            if player:
                # Get specific player history
                history = database.get_player_cwl_season_history(player, limit=10)
                
                if not history:
                    embed = discord.Embed(
                        title="❌ No History Found",
                        description=f"No CWL season history found for **{player}**",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title=f"⭐ CWL History: {player}",
                    description="Season performance history",
                    color=discord.Color.blue()
                )
                
                for season in history:
                    season_name = f"{season['season_year']}-{season['season_month']:02d}"
                    performance = "🟢 Excellent" if season['cwl_stars'] >= 8 and season['missed_attacks'] == 0 else \
                                 "🟡 Good" if season['cwl_stars'] >= 6 and season['missed_attacks'] <= 1 else \
                                 "🟠 Average" if season['cwl_stars'] >= 4 else "🔴 Poor"
                    
                    embed.add_field(
                        name=f"Season {season_name}",
                        value=f"⭐ {season['cwl_stars']} stars\n❌ {season['missed_attacks']} missed\n{performance}",
                        inline=True
                    )
                
            else:
                # Get season overview
                history = database.get_cwl_season_history(season_year, season_month, limit=20)
                
                if not history:
                    embed = discord.Embed(
                        title="❌ No History Found",
                        description="No CWL season history found for the specified criteria",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                if season_year and season_month:
                    embed = discord.Embed(
                        title=f"⭐ CWL Season {season_year}-{season_month:02d}",
                        description="Top performers from this season",
                        color=discord.Color.gold()
                    )
                else:
                    embed = discord.Embed(
                        title="⭐ Recent CWL History",
                        description="Recent season performances",
                        color=discord.Color.gold()
                    )
                
                # Group by season if showing all
                if not (season_year and season_month):
                    current_season = None
                    season_data = []
                    
                    for record in history:
                        season_key = f"{record['season_year']}-{record['season_month']:02d}"
                        if current_season != season_key:
                            if season_data:
                                # Add previous season
                                top_3 = sorted(season_data, key=lambda x: x['cwl_stars'], reverse=True)[:3]
                                value = "\n".join([f"⭐ {p['player_name']}: {p['cwl_stars']} stars" for p in top_3])
                                embed.add_field(name=f"Season {current_season}", value=value, inline=True)
                            current_season = season_key
                            season_data = []
                        season_data.append(record)
                    
                    # Add last season
                    if season_data:
                        top_3 = sorted(season_data, key=lambda x: x['cwl_stars'], reverse=True)[:3]
                        value = "\n".join([f"⭐ {p['player_name']}: {p['cwl_stars']} stars" for p in top_3])
                        embed.add_field(name=f"Season {current_season}", value=value, inline=True)
                else:
                    # Show specific season details
                    for i, record in enumerate(history[:10]):
                        performance = "🟢" if record['cwl_stars'] >= 8 and record['missed_attacks'] == 0 else \
                                     "🟡" if record['cwl_stars'] >= 6 and record['missed_attacks'] <= 1 else \
                                     "🟠" if record['cwl_stars'] >= 4 else "🔴"
                        
                        embed.add_field(
                            name=f"{i+1}. {record['player_name']}",
                            value=f"{performance} ⭐{record['cwl_stars']} ❌{record['missed_attacks']}",
                            inline=True
                        )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in cwl_history command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while retrieving CWL history.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @cwl_history.autocomplete('player')
    async def cwl_history_player_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocomplete for player names in cwl_history command"""
        try:
            names = database.get_autocomplete_names(current)
            return [app_commands.Choice(name=name, value=name) for name in names[:25]]
        except Exception:
            return []

async def setup(bot):
    await bot.add_cog(CWLCog(bot))
