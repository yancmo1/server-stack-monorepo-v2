import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from typing import Optional

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
logger = get_logger("cwl")

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
        """Reset CWL statistics for new season"""
        logger.info(f"[COMMAND] /reset_cwl_stats invoked by {interaction.user.display_name}")
        await interaction.response.defer(ephemeral=True)
        
        try:
            # This would need database implementation
            # For now, just show what would be reset
            players = database.get_player_data()
            cwl_players = [p for p in players if p.get("cwl_stars", 0) > 0 or p.get("missed_attacks", 0) > 0]
            
            embed = discord.Embed(
                title="🔄 CWL Reset Preview",
                description="Preview of what would be reset for new CWL season",
                color=discord.Color.orange()
            )
            
            if cwl_players:
                total_stars = sum(p.get("cwl_stars", 0) for p in cwl_players)
                total_missed = sum(p.get("missed_attacks", 0) for p in cwl_players)
                
                embed.add_field(
                    name="📊 Current Stats to Reset",
                    value=f"**Players with CWL data:** {len(cwl_players)}\n"
                          f"**Total stars to reset:** {total_stars}\n"
                          f"**Total missed attacks to reset:** {total_missed}",
                    inline=False
                )
                
                embed.add_field(
                    name="⚠️ Note",
                    value="CWL reset functionality needs database implementation.\n"
                          "Contact admin to complete the reset process.",
                    inline=False
                )
            else:
                embed.add_field(
                    name="No Data to Reset",
                    value="No CWL statistics found to reset.",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in reset_cwl_stats command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error in CWL reset: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CWLCog(bot))
