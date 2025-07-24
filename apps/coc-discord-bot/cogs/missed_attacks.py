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
logger = get_logger("missed_attacks")

class MissedAttacksCog(commands.Cog):
    """Missed attacks tracking and management"""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="missed_attacks_summary",
        description="Show missed attacks summary — Admin, Leader, Co-Leader, Elder, Member"
    )
    @app_commands.check(is_admin_leader_co_elder_member)
    @app_commands.guilds(GUILD_ID)
    async def missed_attacks_summary(self, interaction: discord.Interaction):
        """Show summary of players with missed attacks"""
        logger.info("[COMMAND] /missed_attacks_summary invoked")
        await interaction.response.defer(ephemeral=True)
        
        try:
            players = database.get_player_data()
            
            # Filter players with missed attacks
            missed_players = [p for p in players if p.get("missed_attacks", 0) > 0]
            
            embed = discord.Embed(
                title="⚠️ Missed Attacks Summary",
                description="Players with missed attacks this season",
                color=discord.Color.orange()
            )
            
            if not missed_players:
                embed.add_field(
                    name="✅ Excellent!",
                    value="No missed attacks recorded this season!",
                    inline=False
                )
            else:
                # Sort by missed attacks (highest first)
                missed_players.sort(key=lambda p: p.get("missed_attacks", 0), reverse=True)
                
                # Group by missed attack count
                high_offenders = [p for p in missed_players if p.get("missed_attacks", 0) >= 3]
                medium_offenders = [p for p in missed_players if 1 <= p.get("missed_attacks", 0) < 3]
                
                if high_offenders:
                    high_text = []
                    for player in high_offenders:
                        missed = player.get("missed_attacks", 0)
                        high_text.append(f"🔴 {player.get('name', 'Unknown')} - {missed} missed")
                    
                    embed.add_field(
                        name="🚨 High Priority (3+ missed)",
                        value="\n".join(high_text),
                        inline=False
                    )
                
                if medium_offenders:
                    medium_text = []
                    for player in medium_offenders:
                        missed = player.get("missed_attacks", 0)
                        medium_text.append(f"🟡 {player.get('name', 'Unknown')} - {missed} missed")
                    
                    embed.add_field(
                        name="⚠️ Watch List (1-2 missed)",
                        value="\n".join(medium_text),
                        inline=False
                    )
                
                # Summary statistics
                total_missed = sum(p.get("missed_attacks", 0) for p in missed_players)
                total_players = len(players)
                clean_players = total_players - len(missed_players)
                
                embed.add_field(
                    name="📊 Statistics",
                    value=f"**Total Players:** {total_players}\n"
                          f"**Players with Missed Attacks:** {len(missed_players)}\n"
                          f"**Players with Clean Record:** {clean_players}\n"
                          f"**Total Missed Attacks:** {total_missed}",
                    inline=False
                )
            
            embed.set_footer(text="Use /player_details <name> for individual player stats")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in missed_attacks_summary: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

    @app_commands.command(
        name="player_missed_attacks",
        description="Show missed attacks for specific player — Admin, Leader, Co-Leader, Elder, Member"
    )
    @app_commands.check(is_admin_leader_co_elder_member)
    @app_commands.guilds(GUILD_ID)
    @app_commands.describe(player_name="Player name to check missed attacks")
    async def player_missed_attacks(self, interaction: discord.Interaction, player_name: str):
        """Show missed attacks for a specific player"""
        logger.info(f"[COMMAND] /player_missed_attacks invoked for {player_name}")
        await interaction.response.defer(ephemeral=True)
        
        try:
            players = database.get_player_data()
            
            # Find the player
            target_player = None
            for player in players:
                if player.get("name", "").lower() == player_name.lower():
                    target_player = player
                    break
            
            if not target_player:
                await interaction.followup.send(f"❌ Player '{player_name}' not found", ephemeral=True)
                return
            
            missed = target_player.get("missed_attacks", 0)
            
            embed = discord.Embed(
                title=f"⚠️ Missed Attacks: {target_player.get('name', 'Unknown')}",
                color=discord.Color.red() if missed >= 3 else discord.Color.orange() if missed > 0 else discord.Color.green()
            )
            
            # Performance rating
            if missed == 0:
                rating = "🟢 Perfect Attendance"
                description = "This player has no missed attacks!"
            elif missed <= 2:
                rating = "🟡 Watch List"
                description = f"This player has {missed} missed attack(s). Monitor for improvement."
            else:
                rating = "🔴 High Priority"
                description = f"This player has {missed} missed attacks. Requires immediate attention."
            
            embed.description = description
            
            embed.add_field(
                name="Missed Attacks",
                value=f"**{missed}** missed attacks this season",
                inline=True
            )
            
            embed.add_field(
                name="Performance Rating",
                value=rating,
                inline=True
            )
            
            # Add CWL context if available
            cwl_stars = target_player.get("cwl_stars", 0)
            if cwl_stars > 0:
                embed.add_field(
                    name="CWL Performance",
                    value=f"⭐ {cwl_stars} stars earned",
                    inline=True
                )
            
            # Add bonus context
            bonus_count = target_player.get("bonus_count", 0)
            embed.add_field(
                name="Bonus History",
                value=f"🏆 {bonus_count} bonuses received",
                inline=True
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in player_missed_attacks: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

    @player_missed_attacks.autocomplete("player_name")
    async def autocomplete_missed_attacks_player(self, interaction: discord.Interaction, current: str):
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
        name="reset_missed_attacks",
        description="Reset missed attacks for new season — Admin, Leader, Co-Leader"
    )
    @app_commands.check(is_admin_leader_co_leader)
    @app_commands.guilds(GUILD_ID)
    async def reset_missed_attacks(self, interaction: discord.Interaction):
        """Reset missed attacks for new season (preview only)"""
        logger.info(f"[COMMAND] /reset_missed_attacks invoked by {interaction.user.display_name}")
        await interaction.response.defer(ephemeral=True)
        
        try:
            players = database.get_player_data()
            missed_players = [p for p in players if p.get("missed_attacks", 0) > 0]
            
            embed = discord.Embed(
                title="🔄 Reset Missed Attacks Preview",
                description="Preview of missed attacks that would be reset",
                color=discord.Color.orange()
            )
            
            if missed_players:
                total_missed = sum(p.get("missed_attacks", 0) for p in missed_players)
                
                embed.add_field(
                    name="📊 Current Stats to Reset",
                    value=f"**Players with missed attacks:** {len(missed_players)}\n"
                          f"**Total missed attacks to reset:** {total_missed}",
                    inline=False
                )
                
                # Show top offenders
                if len(missed_players) > 0:
                    sorted_players = sorted(missed_players, key=lambda p: p.get("missed_attacks", 0), reverse=True)
                    top_offenders = []
                    for player in sorted_players[:5]:
                        missed = player.get("missed_attacks", 0)
                        top_offenders.append(f"• {player.get('name', 'Unknown')} - {missed} missed")
                    
                    embed.add_field(
                        name="🔴 Top Missed Attacks (to be reset)",
                        value="\n".join(top_offenders),
                        inline=False
                    )
                
                embed.add_field(
                    name="⚠️ Note",
                    value="Missed attacks reset functionality needs database implementation.\n"
                          "Contact admin to complete the reset process for new CWL season.",
                    inline=False
                )
            else:
                embed.add_field(
                    name="✅ No Data to Reset",
                    value="No missed attacks recorded to reset.",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in reset_missed_attacks: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MissedAttacksCog(bot))
