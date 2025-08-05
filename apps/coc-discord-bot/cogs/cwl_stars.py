"""
CWL Stars Tracking Cog

This cog tracks Clan War League stars for players, fetching data from the Clash of Clans API.
It automatically checks for new stars and sends notifications when players reach 8+ stars.

Features:
- Automatic polling of CWL wars (every 4 hours)
- Star tracking and notification when players reach 8+ stars
- Commands to view star leaderboard and details
- Reset functionality for new CWL seasons
"""
import discord
from discord import app_commands
from discord.ext import commands, tasks
import config
import database_optimized as database
import logging

GUILD_ID = discord.Object(id=config.GUILD_ID)
import requests
import asyncio
from datetime import datetime, timedelta
import traceback

logger = logging.getLogger("cwl_stars")


class CWLStarsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_cwl_wars(self):
        """Fetch CWL wars for the clan"""
        try:
            api_token = config.get_api_token()
            clan_tag = config.CLAN_TAG
            
            if not api_token or not clan_tag:
                logger.error("Missing API token or clan tag for CWL fetching")
                return None
            
            # URL encode the clan tag
            encoded_tag = clan_tag.replace('#', '%23')
            
            # First, get the current war league group
            url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}/currentwar/leaguegroup"
            headers = {"Authorization": f"Bearer {api_token}"}
            
            logger.info(f"Fetching CWL group data from: {url}")
            
            response = requests.get(url, headers=headers, timeout=30)
            logger.info(f"CWL group API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch CWL group: {response.status_code} - {response.text}")
                return None
            
            group_data = response.json()
            logger.info(f"CWL group data received: {len(group_data.get('rounds', []))} rounds")
            
            # Get our clan's tag to find our wars
            our_clan_tag = clan_tag
            
            # Collect all war tags for our clan
            war_tags = []
            rounds = group_data.get('rounds', [])
            
            for round_num, round_data in enumerate(rounds, 1):
                war_tags_in_round = round_data.get('warTags', [])
                logger.info(f"Round {round_num}: {len(war_tags_in_round)} wars")
                
                for war_tag in war_tags_in_round:
                    if war_tag != '#0':  # Skip placeholder wars
                        war_tags.append((round_num, war_tag))
            
            logger.info(f"Found {len(war_tags)} potential wars to check")
            
            # Now fetch individual war details
            all_wars = []
            for round_num, war_tag in war_tags:
                try:
                    # Fetch individual war data
                    war_url = f"https://api.clashofclans.com/v1/clanwarleagues/wars/{war_tag.replace('#', '%23')}"
                    war_response = requests.get(war_url, headers=headers, timeout=30)
                    
                    if war_response.status_code != 200:
                        logger.warning(f"Failed to fetch war {war_tag}: {war_response.status_code}")
                        continue
                    
                    war_data = war_response.json()
                    
                    # Check if our clan is in this war
                    clan_in_war = False
                    our_clan_data = None
                    
                    if war_data.get('clan', {}).get('tag') == our_clan_tag:
                        clan_in_war = True
                        our_clan_data = war_data.get('clan', {})
                    elif war_data.get('opponent', {}).get('tag') == our_clan_tag:
                        clan_in_war = True
                        our_clan_data = war_data.get('opponent', {})
                    
                    if clan_in_war and our_clan_data:
                        logger.info(f"Found our clan in Round {round_num} war {war_tag}")
                        war_info = {
                            'round': round_num,
                            'war_tag': war_tag,
                            'state': war_data.get('state', 'unknown'),
                            'start_time': war_data.get('startTime'),
                            'end_time': war_data.get('endTime'),
                            'clan_data': our_clan_data
                        }
                        all_wars.append(war_info)
                
                except Exception as e:
                    logger.error(f"Error fetching war {war_tag}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(all_wars)} wars for our clan")
            return all_wars
        
        except Exception as e:
            logger.error(f"Error in fetch_cwl_wars: {e}")
            logger.error(traceback.format_exc())
            return None

    def extract_player_stars(self, wars):
        """Extract player stars from war data"""
        player_stars = {}
        
        for war in wars:
            clan_data = war.get('clan_data', {})
            members = clan_data.get('members', [])
            
            logger.info(f"Round {war['round']}: Processing {len(members)} members")
            
            for member in members:
                tag = member.get('tag', '')
                name = member.get('name', 'Unknown')
                
                # Count stars from attacks
                attacks = member.get('attacks', [])
                total_stars = sum(attack.get('stars', 0) for attack in attacks)
                
                if tag not in player_stars:
                    player_stars[tag] = {
                        'name': name,
                        'total_stars': 0,
                        'attacks': 0,
                        'wars_participated': 0
                    }
                
                player_stars[tag]['total_stars'] += total_stars
                player_stars[tag]['attacks'] += len(attacks)
                player_stars[tag]['wars_participated'] += 1
                
                if total_stars > 0:
                    logger.info(f"Player {name} ({tag}): {total_stars} stars in Round {war['round']}")
        
        return player_stars

    @app_commands.command(
        name="fetch_cwl_stars",
        description="Fetch and update CWL stars from Clash of Clans API"
    )
    @app_commands.guilds(GUILD_ID)
    async def fetch_cwl_stars(self, interaction: discord.Interaction):
        """Fetch CWL stars from the API and update database"""
        await interaction.response.defer()
        
        try:
            logger.info(f"CWL stars fetch requested by {interaction.user.display_name}")
            
            # Fetch wars from API
            await interaction.followup.send("🔄 Fetching CWL wars from Clash of Clans API...")
            wars = await self.fetch_cwl_wars()
            
            if not wars:
                await interaction.followup.send("❌ Failed to fetch CWL wars. Check if clan is in CWL or try again later.")
                return
            
            await interaction.followup.send(f"📊 Found {len(wars)} CWL wars. Processing player stars...")
            
            # Extract player stars
            player_stars = self.extract_player_stars(wars)
            
            if not player_stars:
                await interaction.followup.send("❌ No player data found in CWL wars.")
                return
            
            # Update database
            updated_count = 0
            for tag, player_data in player_stars.items():
                try:
                    # Update player's CWL stars in database
                    database.update_player_cwl_stars(tag, player_data['total_stars'])
                    updated_count += 1
                    logger.info(f"Updated {player_data['name']} ({tag}): {player_data['total_stars']} stars")
                except Exception as e:
                    logger.error(f"Failed to update player {tag}: {e}")
            
            # Create summary embed
            embed = discord.Embed(
                title="✅ CWL Stars Updated",
                description=f"Successfully fetched and updated CWL stars from {len(wars)} wars",
                color=0x00ff00
            )
            
            rounds_text = ', '.join([f"Round {w['round']}" for w in wars])
            embed.add_field(
                name="Wars Processed", 
                value=f"**Rounds:** {rounds_text}\n"
                      f"**Total Wars:** {len(wars)}",
                inline=False
            )
            
            embed.add_field(
                name="Players Updated",
                value=f"**Count:** {updated_count}\n"
                      f"**Total Stars:** {sum(p['total_stars'] for p in player_stars.values())}",
                inline=False
            )
            
            # Show top performers
            top_players = sorted(player_stars.values(), key=lambda x: x['total_stars'], reverse=True)[:5]
            if top_players:
                top_text = "\n".join([
                    f"⭐ {p['name']}: {p['total_stars']} stars ({p['attacks']} attacks)"
                    for p in top_players if p['total_stars'] > 0
                ])
                embed.add_field(
                    name="Top Performers",
                    value=top_text if top_text else "No attacks found yet",
                    inline=False
                )
            
            embed.add_field(
                name="Next Steps",
                value="• Use `/bonuses` to see updated CWL performance\n"
                      "• Use `/give_cwl_bonuses` to distribute rewards\n"
                      "• Data will be preserved when season resets",
                inline=False
            )
            
            embed.set_footer(text=f"Updated by {interaction.user.display_name}")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
            
            logger.info(f"CWL stars fetch completed: {updated_count} players updated, "
                       f"{sum(p['total_stars'] for p in player_stars.values())} total stars")
        
        except Exception as e:
            logger.error(f"Error in fetch_cwl_stars command: {e}")
            logger.error(traceback.format_exc())
            await interaction.followup.send(f"❌ Error fetching CWL stars: {str(e)}")

    @app_commands.command(
        name="cwl_leaderboard",
        description="Show current CWL stars leaderboard"
    )
    @app_commands.guilds(GUILD_ID)
    async def cwl_leaderboard(self, interaction: discord.Interaction):
        """Show CWL stars leaderboard"""
        await interaction.response.defer()
        
        try:
            players = database.get_player_data()
            cwl_players = [p for p in players if p.get('cwl_stars', 0) > 0]
            cwl_players.sort(key=lambda x: x.get('cwl_stars', 0), reverse=True)
            
            if not cwl_players:
                await interaction.followup.send("📊 No CWL stars recorded yet. Use `/fetch_cwl_stars` to update from API.")
                return
            
            embed = discord.Embed(
                title="⭐ CWL Stars Leaderboard",
                description="Current season CWL performance",
                color=0xffd700
            )
            
            leaderboard_text = ""
            for i, player in enumerate(cwl_players[:15], 1):
                stars = player.get('cwl_stars', 0)
                name = player.get('name', 'Unknown')
                
                # Add medal emojis for top 3
                medal = ""
                if i == 1:
                    medal = "🥇 "
                elif i == 2:
                    medal = "🥈 "
                elif i == 3:
                    medal = "🥉 "
                
                leaderboard_text += f"{medal}**{i}.** {name}: **{stars}** ⭐\n"
            
            embed.add_field(
                name="Top Performers",
                value=leaderboard_text,
                inline=False
            )
            
            total_stars = sum(p.get('cwl_stars', 0) for p in players)
            embed.add_field(
                name="Season Summary",
                value=f"**Total Players:** {len(cwl_players)}\n"
                      f"**Total Stars:** {total_stars}\n"
                      f"**Average:** {total_stars/len(cwl_players):.1f} stars per player",
                inline=False
            )
            
            embed.set_footer(text="Use /fetch_cwl_stars to update from API")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Error in cwl_leaderboard: {e}")
            await interaction.followup.send(f"❌ Error generating leaderboard: {str(e)}")


async def setup(bot):
    await bot.add_cog(CWLStarsCog(bot))
