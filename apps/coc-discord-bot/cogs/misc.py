# cogs/misc.py
import json
import asyncio
from datetime import datetime
from typing import Optional

import discord
import requests
from discord import app_commands
from discord.ext import commands

import config
import database_optimized as database
from logging_config import get_logger
from utils import (
    has_any_role_id, 
    is_admin, 
    is_admin_leader_co_leader, 
    is_admin_leader_co_elder_member,
    is_newbie,
    format_last_bonus
)

GUILD_ID = discord.Object(id=config.GUILD_ID)
logger = get_logger("misc")

class MiscCog(commands.Cog):
    """Miscellaneous utility commands"""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Test bot responsiveness — Admin")
    @app_commands.check(is_admin)
    @app_commands.guilds(GUILD_ID)
    async def ping(self, interaction: discord.Interaction):
        """Simple ping command to test bot responsiveness"""
        logger.info("[COMMAND] /ping invoked")
        try:
            await interaction.response.send_message("🏓 Pong!", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in ping command: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    @app_commands.command(
        name="show_help", 
        description="Show available bot commands — Admin, Leader, Co-Leader, Elder, Member"
    )
    @app_commands.check(is_admin_leader_co_elder_member)
    @app_commands.guilds(GUILD_ID)
    @app_commands.describe(category="Show commands for specific category (optional)")
    async def show_help(self, interaction: discord.Interaction, category: Optional[str] = None):
        """Show help information for bot commands"""
        logger.info("[COMMAND] /show_help invoked")
        try:
            embed = discord.Embed(
                title="🤖 Bot Commands Help",
                description="Available commands organized by category",
                color=discord.Color.blue()
            )
            
            # Player Management Commands
            embed.add_field(
                name="👥 Player Management",
                value=(
                    "• `/list_players` - View all clan players\n"
                    "• `/player_details <name>` - Get detailed player info\n"
                    "• `/myrole` - Show your clan and Discord roles"
                ),
                inline=False
            )
            
            # Bonus Management Commands
            embed.add_field(
                name="🏆 Bonus Management",
                value=(
                    "• `/give_cwl_bonuses [count]` - Award CWL bonuses (Admin/Leader/Co)\n"
                    "• `/bonus_history_all` - View all player bonus history\n"
                    "• `/on_deck` - See which players are currently on deck for bonuses"
                ),
                inline=False
            )
            
            # Roster Management Commands
            embed.add_field(
                name="📋 Roster Management",
                value=(
                    "• `/roster_update` - Update player roster from API (Admin/Leader/Co)\n"
                    "• Database automatically syncs with Clash of Clans API"
                ),
                inline=False
            )
            
            # Utility Commands
            embed.add_field(
                name="🔧 Utilities",
                value=(
                    "• `/ping` - Test bot responsiveness (Admin)\n"
                    "• `/api_test` - Test Clash of Clans API connection (Admin)\n"
                    "• `/show_help` - Show this help message"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🧭 Quick Navigation",
                value=(
                    "**Role Access Levels:**\n"
                    "• Admin: Full access to all commands\n"
                    "• Leader/Co-Leader: Management commands\n"
                    "• Elder/Member: Read-only and basic commands"
                ),
                inline=False
            )
            
            embed.set_footer(text="Use /command_name for detailed help on specific commands")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in show_help command: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    @app_commands.command(name="api_test", description="Test Clash of Clans API connection — Admin")
    @app_commands.check(is_admin)
    @app_commands.guilds(GUILD_ID)
    async def api_test(self, interaction: discord.Interaction):
        """Test the Clash of Clans API connection"""
        logger.info("[COMMAND] /api_test invoked")
        await interaction.response.defer(ephemeral=True)
        
        try:
            clan_tag = config.CLAN_TAG
            if not clan_tag:
                await interaction.followup.send("❌ CLAN_TAG not configured", ephemeral=True)
                return
                
            api_token = config.SUPERCELL_API_TOKEN
            if not api_token:
                await interaction.followup.send("❌ SUPERCELL_API_TOKEN not configured", ephemeral=True)
                return
            
            headers = {"Authorization": f"Bearer {api_token}"}
            
            # Test clan info endpoint
            url = f"https://api.clashofclans.com/v1/clans/{clan_tag.replace('#', '%23')}"
            
            start_time = datetime.now()
            response = requests.get(url, headers=headers, timeout=10)
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                clan_data = response.json()
                embed = discord.Embed(
                    title="✅ API Test Successful",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Response Time", 
                    value=f"{response_time:.0f}ms", 
                    inline=True
                )
                embed.add_field(
                    name="Status Code", 
                    value=response.status_code, 
                    inline=True
                )
                embed.add_field(
                    name="Clan Info",
                    value=f"**{clan_data.get('name', 'Unknown')}**\n"
                          f"Members: {clan_data.get('members', 0)}\n"
                          f"Level: {clan_data.get('clanLevel', '?')}",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ API Test Failed",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Status Code", 
                    value=response.status_code, 
                    inline=True
                )
                embed.add_field(
                    name="Response Time", 
                    value=f"{response_time:.0f}ms", 
                    inline=True
                )
                embed.add_field(
                    name="Error",
                    value=response.text[:500] if response.text else "No error message",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except requests.RequestException as e:
            embed = discord.Embed(
                title="❌ API Connection Failed",
                description=f"Network error: {e}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in api_test command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error testing API: {e}", ephemeral=True)

    @app_commands.command(name="db_test", description="Test PostgreSQL database connection — Admin")
    @app_commands.check(is_admin)
    @app_commands.guilds(GUILD_ID)
    async def db_test(self, interaction: discord.Interaction):
        """Test the PostgreSQL database connection"""
        logger.info("[COMMAND] /db_test invoked")
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Test database connection and basic queries
            players = database.get_player_data()
            
            embed = discord.Embed(
                title="✅ Database Test Successful",
                description="PostgreSQL connection working correctly",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Connection Status",
                value="✅ Connected to PostgreSQL",
                inline=False
            )
            
            embed.add_field(
                name="Player Data",
                value=f"**Total Players:** {len(players)}\n"
                      f"**Sample Player:** {players[0].get('name', 'Unknown') if players else 'No players found'}",
                inline=False
            )
            
            # Test bonus history
            try:
                bonus_history = database.get_bonus_history(limit=5)
                embed.add_field(
                    name="Bonus History",
                    value=f"**Recent Bonuses:** {len(bonus_history)} found",
                    inline=True
                )
            except Exception as bonus_error:
                embed.add_field(
                    name="Bonus History",
                    value=f"⚠️ Error: {bonus_error}",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Database Test Failed",
                description=f"PostgreSQL connection error: {e}",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="Error Details",
                value=str(e)[:500],
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.error(f"Database test failed: {e}", exc_info=True)

    @app_commands.command(
        name="myrole", 
        description="Show your current clan role and Discord role"
    )
    @app_commands.guilds(GUILD_ID)
    async def myrole(self, interaction: discord.Interaction):
        """Show user's clan and Discord role information"""
        logger.info(f"[COMMAND] /myrole invoked by {interaction.user.display_name}")
        try:
            user = interaction.user
            member = interaction.guild.get_member(user.id) if interaction.guild else None
            
            embed = discord.Embed(
                title="🎭 Your Role Information",
                color=discord.Color.blue()
            )
            
            # Discord roles
            if member:
                discord_roles = [role.name for role in member.roles if role.name != "@everyone"]
                embed.add_field(
                    name="Discord Roles",
                    value=", ".join(discord_roles) if discord_roles else "No special roles",
                    inline=False
                )
                
                # Check specific bot permission roles
                permissions = []
                if is_admin(interaction):
                    permissions.append("🔴 Admin")
                elif is_admin_leader_co_leader(interaction):
                    permissions.append("🟡 Leader/Co-Leader")
                elif is_admin_leader_co_elder_member(interaction):
                    permissions.append("🟢 Elder/Member")
                else:
                    permissions.append("⚪ No bot permissions")
                
                embed.add_field(
                    name="Bot Permissions",
                    value="\n".join(permissions),
                    inline=False
                )
            
            # Try to get clan role from database
            try:
                players = database.get_player_data()
                user_player = None
                
                # Look for player by Discord name or similar
                for player in players:
                    if (player.get("name", "").lower() == user.display_name.lower() or
                        player.get("name", "").lower() == user.name.lower()):
                        user_player = player
                        break
                
                if user_player:
                    embed.add_field(
                        name="Clash of Clans Info",
                        value=f"**Name:** {user_player.get('name', 'Unknown')}\n"
                              f"**Role:** {user_player.get('role', 'Unknown')}\n"
                              f"**Town Hall:** {user_player.get('townhall_level', '?')}\n"
                              f"**Tag:** {user_player.get('tag', 'Unknown')}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Clash of Clans Info",
                        value="No clan member found matching your Discord name.\n"
                              "Contact leadership if this is incorrect.",
                        inline=False
                    )
            except Exception as db_error:
                logger.warning(f"Could not retrieve clan info: {db_error}")
                embed.add_field(
                    name="Clash of Clans Info",
                    value="Unable to retrieve clan information at this time.",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in myrole command: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    @app_commands.command(
        name="link_coc_account",
        description="Link your Discord account to a Clash of Clans player — All Members"
    )
    @app_commands.guilds(GUILD_ID)
    @app_commands.describe(player_name="Your Clash of Clans player name")
    async def link_coc_account(self, interaction: discord.Interaction, player_name: str):
        """Link Discord account to a Clash of Clans player"""
        logger.info(f"[COMMAND] /link_coc_account invoked by {interaction.user.display_name} for {player_name}")
        try:
            # Get all players from database
            players = database.get_player_data()
            
            # Find player by name (case insensitive)
            matching_player = None
            for player in players:
                if player.get("name", "").lower() == player_name.lower():
                    matching_player = player
                    break
            
            if not matching_player:
                # Show available players for suggestion
                available_names = [p.get("name", "") for p in players[:10]]
                await interaction.response.send_message(
                    f"❌ Player '{player_name}' not found in clan.\n\n"
                    f"Available players include: {', '.join(available_names)}\n"
                    f"(Showing first 10 players)",
                    ephemeral=True
                )
                return
            
            # For now, just provide confirmation - actual linking would require database schema update
            embed = discord.Embed(
                title="🔗 Account Link Request",
                description=f"Link request for **{matching_player.get('name')}**",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Player Details",
                value=f"**Name:** {matching_player.get('name', 'Unknown')}\n"
                      f"**Tag:** {matching_player.get('tag', 'Unknown')}\n"
                      f"**Role:** {matching_player.get('role', 'Unknown')}\n"
                      f"**Town Hall:** {matching_player.get('townhall_level', '?')}",
                inline=False
            )
            
            embed.add_field(
                name="Status",
                value="✅ Player found and verified!\n"
                      "Note: Full linking system coming soon.\n"
                      "Contact leadership to complete the link.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in link_coc_account command: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    @link_coc_account.autocomplete("player_name")
    async def autocomplete_player_name(self, interaction: discord.Interaction, current: str):
        """Provide autocomplete suggestions for player names"""
        try:
            if hasattr(database, 'get_autocomplete_names'):
                names = database.get_autocomplete_names(current)
                return [app_commands.Choice(name=n, value=n) for n in names[:25]]
            else:
                # Fallback: get all players and filter
                players = database.get_player_data()
                if current:
                    filtered = [p.get("name", "") for p in players 
                              if current.lower() in p.get("name", "").lower()]
                else:
                    filtered = [p.get("name", "") for p in players]
                return [app_commands.Choice(name=n, value=n) for n in filtered[:25]]
        except Exception:
            return []

    @app_commands.command(name="test_new_command", description="Test if new commands can be added")
    async def test_new_command(self, interaction: discord.Interaction):
        """Simple test to see if we can add new commands"""
        await interaction.response.send_message("✅ New command is working in misc.py!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MiscCog(bot))
