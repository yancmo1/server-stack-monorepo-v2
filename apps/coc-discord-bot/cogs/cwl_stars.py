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
import asyncio

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
                        
                        # Get opponent data
                        opponent_data = None
                        if war_data.get('clan', {}).get('tag') == our_clan_tag:
                            # We are 'clan', opponent is 'opponent'
                            opponent_data = war_data.get('opponent', {})
                        else:
                            # We are 'opponent', opponent is 'clan'
                            opponent_data = war_data.get('clan', {})
                        
                        war_info = {
                            'round': round_num,
                            'war_tag': war_tag,
                            'state': war_data.get('state', 'unknown'),
                            'start_time': war_data.get('startTime'),
                            'end_time': war_data.get('endTime'),
                            'clan_data': our_clan_data,
                            'opponent_data': opponent_data
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
        """Extract player stars from war data and return detailed war information"""
        player_stars = {}
        war_details = []
        
        for war in wars:
            clan_data = war.get('clan_data', {})
            opponent_data = war.get('opponent_data', {})
            members = clan_data.get('members', [])
            war_state = war.get('state', 'unknown')
            
            # Create detailed war info
            war_info = {
                'round': war['round'],
                'opponent': opponent_data.get('name', 'Unknown'),
                'our_stars': clan_data.get('stars', 0),
                'opponent_stars': opponent_data.get('stars', 0),
                'our_destruction': clan_data.get('destructionPercentage', 0),
                'opponent_destruction': opponent_data.get('destructionPercentage', 0),
                'result': '🏆 Victory' if clan_data.get('stars', 0) > opponent_data.get('stars', 0) else 
                         '🤝 Tie' if clan_data.get('stars', 0) == opponent_data.get('stars', 0) else '❌ Defeat',
                'state': war_state,
                'players': []
            }
            
            logger.info(f"Round {war['round']}: Processing {len(members)} members vs {war_info['opponent']} (State: {war_state})")
            logger.info(f"Round {war['round']}: Our {war_info['our_stars']} vs Opponent {war_info['opponent_stars']} stars")
            
            # Get all players who attacked (for missed attack calculation)
            attackers = set()
            for member in members:
                attacks = member.get('attacks', [])
                if attacks:
                    attackers.add(member.get('tag', ''))
            
            logger.info(f"Round {war['round']}: {len(attackers)} out of {len(members)} players attacked")
            
            # Determine if we should count missed attacks based on war state
            should_count_missed = war_state in ['warEnded'] or (war_state == 'inWar' and len(attackers) > len(members) * 0.7)
            
            for member in members:
                tag = member.get('tag', '')
                name = member.get('name', 'Unknown')
                
                # Count stars from attacks
                attacks = member.get('attacks', [])
                total_stars = sum(attack.get('stars', 0) for attack in attacks)
                total_destruction = sum(attack.get('destructionPercentage', 0) for attack in attacks)
                avg_destruction = round(total_destruction / max(len(attacks), 1), 1)
                
                # Calculate missed attacks - only for ended wars or when most players have attacked
                missed_attacks = 0
                if should_count_missed and len(attacks) == 0 and len(attackers) > 0:
                    missed_attacks = 1
                
                # Add to war player details
                war_info['players'].append({
                    'name': name,
                    'tag': tag,
                    'stars': total_stars,
                    'attacks': len(attacks),
                    'missed_attacks': missed_attacks,
                    'avg_destruction': avg_destruction
                })
                
                # Add to overall player stats
                if tag not in player_stars:
                    player_stars[tag] = {
                        'name': name,
                        'total_stars': 0,
                        'attacks': 0,
                        'missed_attacks': 0,
                        'wars_participated': 0
                    }
                
                player_stars[tag]['total_stars'] += total_stars
                player_stars[tag]['attacks'] += len(attacks)
                player_stars[tag]['missed_attacks'] += missed_attacks
                player_stars[tag]['wars_participated'] += 1
                
                if total_stars > 0:
                    logger.info(f"Player {name} ({tag}): {total_stars} stars in Round {war['round']}")
                if missed_attacks > 0:
                    logger.info(f"Player {name} ({tag}): {missed_attacks} missed attacks in Round {war['round']}")
            
            # Sort players by stars in this war
            war_info['players'].sort(key=lambda p: p['stars'], reverse=True)
            war_details.append(war_info)
        
        return player_stars, war_details

    async def send_war_details(self, interaction, war_details):
        """Send detailed war results page by page"""
        for war_info in war_details:
            war_state = war_info.get('state', 'unknown')
            
            # Determine title and color based on war state
            if war_state == 'preparation':
                title_prefix = "⏳ CWL Round"
                description_suffix = "**Preparation Day**"
                color = 0x9932cc  # Purple for preparation
            elif war_state == 'inWar':
                title_prefix = "⚔️ CWL Round"
                description_suffix = "**War Day - In Progress**"
                color = 0xffa500  # Orange for ongoing
            elif war_state == 'warEnded':
                title_prefix = "✅ CWL Round"
                description_suffix = war_info['result']
                color = 0x00ff00 if '🏆' in war_info['result'] else 0xff0000 if '❌' in war_info['result'] else 0xffff00
            else:
                title_prefix = "⚔️ CWL Round"
                description_suffix = war_info['result']
                color = 0x808080  # Gray for unknown
            
            embed = discord.Embed(
                title=f"{title_prefix} {war_info['round']} Results",
                description=f"**vs {war_info['opponent']}**\n{description_suffix}",
                color=color
            )
            
            # War summary
            embed.add_field(
                name="📊 War Summary",
                value=f"**Our Stars:** {war_info['our_stars']} ⭐\n"
                      f"**Opponent Stars:** {war_info['opponent_stars']} ⭐\n"
                      f"**Our Destruction:** {war_info['our_destruction']:.1f}%\n"
                      f"**Opponent Destruction:** {war_info['opponent_destruction']:.1f}%",
                inline=True
            )
            
            # Top performers in this war
            top_performers = war_info['players'][:8]  # Show top 8
            if top_performers:
                performers_text = []
                for i, player in enumerate(top_performers, 1):
                    star_emoji = "⭐" * player['stars'] if player['stars'] <= 3 else f"{player['stars']}⭐"
                    
                    # Only show missed indicator for ended wars or when most have attacked
                    missed_indicator = ""
                    if war_state == 'warEnded' and player['missed_attacks'] > 0:
                        missed_indicator = " ❌"
                    elif war_state == 'inWar' and player['attacks'] == 0:
                        missed_indicator = " ⏳"  # Pending attack
                    elif player['missed_attacks'] > 0:
                        missed_indicator = " ❌"
                    
                    performers_text.append(
                        f"{i}. **{player['name']}**: {star_emoji}{missed_indicator} "
                        f"({player['attacks']} attacks, {player['avg_destruction']}% avg)"
                    )
                
                embed.add_field(
                    name="🏆 Top Performers",
                    value="\n".join(performers_text),
                    inline=False
                )
            
            # Show missed attacks only for ended wars, or pending attacks for ongoing wars
            if war_state == 'warEnded':
                missed_players = [p for p in war_info['players'] if p['missed_attacks'] > 0]
                if missed_players:
                    missed_text = []
                    for player in missed_players[:10]:  # Show up to 10 missed
                        missed_text.append(f"❌ **{player['name']}** - {player['missed_attacks']} missed")
                    
                    embed.add_field(
                        name="⚠️ Missed Attacks",
                        value="\n".join(missed_text),
                        inline=False
                    )
            elif war_state == 'inWar':
                pending_players = [p for p in war_info['players'] if p['attacks'] == 0]
                if pending_players:
                    pending_text = []
                    for player in pending_players[:10]:  # Show up to 10 pending
                        pending_text.append(f"⏳ **{player['name']}** - Attack pending")
                    
                    embed.add_field(
                        name="⏳ Pending Attacks",
                        value="\n".join(pending_text),
                        inline=False
                    )
            elif war_state == 'preparation':
                embed.add_field(
                    name="📋 War Status",
                    value="War lineup is being prepared. Attacks will begin soon!",
                    inline=False
                )
            
            # War statistics
            total_attacks = sum(p['attacks'] for p in war_info['players'])
            total_war_stars = sum(p['stars'] for p in war_info['players'])
            total_missed = sum(p['missed_attacks'] for p in war_info['players'])
            participants = len([p for p in war_info['players'] if p['attacks'] > 0])
            
            stats_value = f"**Participants:** {participants}/{len(war_info['players'])}\n"
            stats_value += f"**Total Attacks:** {total_attacks}\n"
            stats_value += f"**Total Stars:** {total_war_stars}\n"
            
            if war_state == 'warEnded':
                stats_value += f"**Missed Attacks:** {total_missed}\n"
            elif war_state == 'inWar':
                pending_count = len([p for p in war_info['players'] if p['attacks'] == 0])
                stats_value += f"**Pending Attacks:** {pending_count}\n"
            
            if total_attacks > 0:
                stats_value += f"**Avg Stars/Attack:** {total_war_stars/total_attacks:.1f}"
            
            embed.add_field(
                name="📈 War Stats",
                value=stats_value,
                inline=True
            )
            
            await interaction.followup.send(embed=embed)
            
            # Small delay between war pages to avoid rate limits
            await asyncio.sleep(0.5)

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
            
            # Initialize the processed wars table
            database.create_processed_wars_table()
            
            # Fetch wars from API
            await interaction.followup.send("🔄 Fetching CWL wars from Clash of Clans API...")
            wars = await self.fetch_cwl_wars()
            
            if not wars:
                await interaction.followup.send("❌ Failed to fetch CWL wars. Check if clan is in CWL or try again later.")
                return
            
            # Check which wars are new (not processed yet)
            new_wars = []
            already_processed = []
            
            for war in wars:
                war_tag = war.get('war_tag', '')
                if war_tag and not database.check_war_already_processed(war_tag):
                    new_wars.append(war)
                else:
                    already_processed.append(war)
            
            await interaction.followup.send(
                f"📊 Found {len(wars)} CWL wars total. "
                f"{len(new_wars)} new wars to process, {len(already_processed)} already processed."
            )
            
            if not new_wars:
                await interaction.followup.send("✅ All wars have been processed already. No new data to update.")
                return
            
            # Extract player stars and war details from new wars only
            player_stars, war_details = self.extract_player_stars(new_wars)
            
            if not player_stars:
                await interaction.followup.send("❌ No player data found in new CWL wars.")
                return
            
            # Get current database values to add to (not replace)
            current_players = database.get_player_data()
            current_cwl_data = {p.get('tag'): {
                'cwl_stars': p.get('cwl_stars', 0),
                'missed_attacks': p.get('missed_attacks', 0)
            } for p in current_players}
            
            # Update database with incremental data
            updated_count = 0
            for tag, player_data in player_stars.items():
                try:
                    # Add new stars and missed attacks to existing totals
                    current_stars = current_cwl_data.get(tag, {}).get('cwl_stars', 0)
                    current_missed = current_cwl_data.get(tag, {}).get('missed_attacks', 0)
                    
                    new_total_stars = current_stars + player_data['total_stars']
                    new_total_missed = current_missed + player_data['missed_attacks']
                    
                    # Update player's CWL data in database
                    database.update_player_cwl_data(tag, new_total_stars, new_total_missed)
                    updated_count += 1
                    
                    logger.info(f"Updated {player_data['name']} ({tag}): "
                              f"{new_total_stars} total stars (+{player_data['total_stars']}), "
                              f"{new_total_missed} total missed (+{player_data['missed_attacks']})")
                except Exception as e:
                    logger.error(f"Failed to update player {tag}: {e}")
            
            # Mark wars as processed
            for war in new_wars:
                war_tag = war.get('war_tag', '')
                if war_tag:
                    database.mark_war_processed(war_tag)
            
            # Send detailed war-by-war results for new wars only
            if new_wars:
                await interaction.followup.send("📋 **New War Details:**")
                await self.send_war_details(interaction, war_details)
            
            # Create summary embed
            embed = discord.Embed(
                title="✅ CWL Stars Updated",
                description=f"Successfully processed {len(new_wars)} new CWL wars",
                color=0x00ff00
            )
            
            if new_wars:
                rounds_text = ', '.join([f"Round {w['round']}" for w in new_wars])
                embed.add_field(
                    name="New Wars Processed", 
                    value=f"**Rounds:** {rounds_text}\n"
                          f"**New Wars:** {len(new_wars)}",
                    inline=False
                )
            
            if already_processed:
                processed_rounds = ', '.join([f"Round {w['round']}" for w in already_processed])
                embed.add_field(
                    name="Previously Processed", 
                    value=f"**Rounds:** {processed_rounds}\n"
                          f"**Wars:** {len(already_processed)}",
                    inline=False
                )
            
            embed.add_field(
                name="Players Updated",
                value=f"**Count:** {updated_count}\n"
                      f"**New Stars Added:** {sum(p['total_stars'] for p in player_stars.values())}\n"
                      f"**New Missed Attacks:** {sum(p['missed_attacks'] for p in player_stars.values())}",
                inline=False
            )
            
            # Show top performers from new data
            if player_stars:
                top_players = sorted(player_stars.values(), key=lambda x: x['total_stars'], reverse=True)[:5]
                top_text = "\n".join([
                    f"⭐ {p['name']}: +{p['total_stars']} stars, +{p['missed_attacks']} missed"
                    for p in top_players if p['total_stars'] > 0 or p['missed_attacks'] > 0
                ])
                embed.add_field(
                    name="New Activity (This Fetch)",
                    value=top_text if top_text else "No new activity found",
                    inline=False
                )
            
            embed.add_field(
                name="Next Steps",
                value="• Use `/bonuses` to see updated CWL performance\n"
                      "• Use `/give_cwl_bonuses` to distribute rewards\n"
                      "• Run command again to fetch any new completed wars\n"
                      "• Data is safely accumulated (no duplicates)",
                inline=False
            )
            
            embed.set_footer(text=f"Updated by {interaction.user.display_name} • Wars safely tracked")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
            
            logger.info(f"CWL stars fetch completed: {updated_count} players updated, "
                       f"{sum(p['total_stars'] for p in player_stars.values())} new stars added, "
                       f"{sum(p['missed_attacks'] for p in player_stars.values())} new missed attacks")
        
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
                missed = player.get('missed_attacks', 0)
                name = player.get('name', 'Unknown')
                
                # Add medal emojis for top 3
                medal = ""
                if i == 1:
                    medal = "🥇 "
                elif i == 2:
                    medal = "🥈 "
                elif i == 3:
                    medal = "🥉 "
                
                # Add missed attacks indicator
                missed_indicator = f" (❌{missed})" if missed > 0 else ""
                
                leaderboard_text += f"{medal}**{i}.** {name}: **{stars}** ⭐{missed_indicator}\n"
            
            embed.add_field(
                name="Top Performers",
                value=leaderboard_text,
                inline=False
            )
            
            # Show missed attacks summary
            all_players = [p for p in players if p.get('cwl_stars', 0) > 0 or p.get('missed_attacks', 0) > 0]
            total_stars = sum(p.get('cwl_stars', 0) for p in all_players)
            total_missed = sum(p.get('missed_attacks', 0) for p in all_players)
            players_with_missed = len([p for p in all_players if p.get('missed_attacks', 0) > 0])
            
            embed.add_field(
                name="Season Summary",
                value=f"**Active Players:** {len(cwl_players)}\n"
                      f"**Total Stars:** {total_stars}\n"
                      f"**Total Missed Attacks:** {total_missed}\n"
                      f"**Players with Missed Attacks:** {players_with_missed}\n"
                      f"**Average Stars:** {total_stars/len(cwl_players):.1f} per player",
                inline=False
            )
            
            # Show worst missed attacks
            if players_with_missed > 0:
                missed_players = [p for p in all_players if p.get('missed_attacks', 0) > 0]
                missed_players.sort(key=lambda x: x.get('missed_attacks', 0), reverse=True)
                
                worst_missed = []
                for player in missed_players[:5]:
                    missed = player.get('missed_attacks', 0)
                    stars = player.get('cwl_stars', 0)
                    worst_missed.append(f"❌ {player.get('name', 'Unknown')}: {missed} missed ({stars} ⭐)")
                
                embed.add_field(
                    name="⚠️ Most Missed Attacks",
                    value="\n".join(worst_missed),
                    inline=False
                )
            
            embed.set_footer(text="Use /fetch_cwl_stars to update from API • ❌ = missed attacks")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Error in cwl_leaderboard: {e}")
            await interaction.followup.send(f"❌ Error generating leaderboard: {str(e)}")


    @app_commands.command(
        name="debug_cwl_api",
        description="Debug CWL API response (Admin only)"
    )
    @app_commands.guilds(GUILD_ID)
    async def debug_cwl_api(self, interaction: discord.Interaction):
        """Debug the CWL API response to see raw data"""
        # Check admin permissions
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ This command requires server membership.", ephemeral=True)
            return
        
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ This command requires admin permissions.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Fetch a single war for debugging
            wars = await self.fetch_cwl_wars()
            
            if not wars:
                await interaction.followup.send("❌ No wars found to debug", ephemeral=True)
                return
            
            # Take the first war for detailed analysis
            war = wars[0]
            
            embed = discord.Embed(
                title="🐛 CWL API Debug Info",
                description=f"Debug info for Round {war['round']}",
                color=0x9932cc
            )
            
            # War basic info
            clan_data = war.get('clan_data', {})
            opponent_data = war.get('opponent_data', {})
            
            embed.add_field(
                name="War Info",
                value=f"**Round:** {war['round']}\n"
                      f"**State:** {war.get('state', 'unknown')}\n"
                      f"**War Tag:** {war.get('war_tag', 'unknown')}",
                inline=False
            )
            
            embed.add_field(
                name="Our Clan Data",
                value=f"**Name:** {clan_data.get('name', 'Unknown')}\n"
                      f"**Tag:** {clan_data.get('tag', 'Unknown')}\n"
                      f"**Stars:** {clan_data.get('stars', 0)}\n"
                      f"**Destruction:** {clan_data.get('destructionPercentage', 0)}%\n"
                      f"**Members:** {len(clan_data.get('members', []))}",
                inline=True
            )
            
            embed.add_field(
                name="Opponent Data",
                value=f"**Name:** {opponent_data.get('name', 'Unknown')}\n"
                      f"**Tag:** {opponent_data.get('tag', 'Unknown')}\n"
                      f"**Stars:** {opponent_data.get('stars', 0)}\n"
                      f"**Destruction:** {opponent_data.get('destructionPercentage', 0)}%\n"
                      f"**Members:** {len(opponent_data.get('members', []))}",
                inline=True
            )
            
            # Sample player data
            members = clan_data.get('members', [])
            if members:
                sample_member = members[0]
                attacks = sample_member.get('attacks', [])
                
                embed.add_field(
                    name="Sample Player",
                    value=f"**Name:** {sample_member.get('name', 'Unknown')}\n"
                          f"**Tag:** {sample_member.get('tag', 'Unknown')}\n"
                          f"**Attacks:** {len(attacks)}\n"
                          f"**Stars:** {sum(a.get('stars', 0) for a in attacks)}",
                    inline=False
                )
                
                if attacks:
                    attack = attacks[0]
                    embed.add_field(
                        name="Sample Attack",
                        value=f"**Target:** {attack.get('defenderTag', 'Unknown')}\n"
                              f"**Stars:** {attack.get('stars', 0)}\n"
                              f"**Destruction:** {attack.get('destructionPercentage', 0)}%",
                        inline=False
                    )
            
            # Show total wars found
            rounds_list = ', '.join([f"Round {w['round']}" for w in wars])
            embed.add_field(
                name="Total Wars Found",
                value=f"**Count:** {len(wars)}\n"
                      f"**Rounds:** {rounds_list}",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in debug_cwl_api: {e}")
            await interaction.followup.send(f"❌ Debug error: {str(e)}", ephemeral=True)

    @app_commands.command(
        name="clear_cwl_data",
        description="Clear current CWL stars and missed attacks (Admin only)"
    )
    @app_commands.guilds(GUILD_ID)
    async def clear_cwl_data(self, interaction: discord.Interaction):
        """Clear current CWL season data"""
        # Check if user has admin permissions
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ This command requires server membership.", ephemeral=True)
            return
        
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ This command requires admin permissions.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get current stats before clearing
            players = database.get_player_data()
            cwl_players = [p for p in players if p.get('cwl_stars', 0) > 0 or p.get('missed_attacks', 0) > 0]
            
            total_stars = sum(p.get('cwl_stars', 0) for p in cwl_players)
            total_missed = sum(p.get('missed_attacks', 0) for p in cwl_players)
            
            # Clear the data
            affected_rows = database.reset_cwl_season_data()
            
            embed = discord.Embed(
                title="🗑️ CWL Data Cleared",
                description="Successfully cleared current CWL season data",
                color=0xff6600
            )
            
            embed.add_field(
                name="📊 Data Cleared",
                value=f"**Players Affected:** {affected_rows}\n"
                      f"**Stars Cleared:** {total_stars}\n"
                      f"**Missed Attacks Cleared:** {total_missed}",
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Note",
                value="CWL stars and missed attacks have been reset to zero.\n"
                      "Use `/fetch_cwl_stars` to re-fetch fresh data from API.\n"
                      "Consider also running `/reset_processed_wars` to reprocess all wars.",
                inline=False
            )
            
            embed.add_field(
                name="Next Steps",
                value="1. Run `/reset_processed_wars` (optional - to reprocess all wars)\n"
                      "2. Run `/fetch_cwl_stars` to get fresh CWL data\n"
                      "3. Check `/cwl_leaderboard` to verify clean slate",
                inline=False
            )
            
            embed.set_footer(text=f"Cleared by {interaction.user.display_name}")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"CWL data cleared by {interaction.user.display_name}: {affected_rows} players, {total_stars} stars, {total_missed} missed attacks")
        
        except Exception as e:
            logger.error(f"Error clearing CWL data: {e}")
            await interaction.followup.send(f"❌ Error clearing data: {str(e)}", ephemeral=True)

    @app_commands.command(
        name="reset_processed_wars",
        description="Reset processed wars tracking (Admin only - for testing)"
    )
    @app_commands.guilds(GUILD_ID)
    async def reset_processed_wars(self, interaction: discord.Interaction):
        """Reset the processed wars table for testing"""
        # Check if user has admin permissions (simplified check)
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ This command requires server membership.", ephemeral=True)
            return
        
        # Basic admin check - user needs to be able to manage server
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ This command requires admin permissions.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            with database.get_optimized_connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM processed_wars")
                deleted_count = cur.rowcount
            
            embed = discord.Embed(
                title="🔄 Processed Wars Reset",
                description=f"Cleared {deleted_count} processed war records",
                color=0xff9900
            )
            
            embed.add_field(
                name="Effect",
                value="All wars will be processed as 'new' on next `/fetch_cwl_stars` run.\n"
                      "This will re-add stars and missed attacks to database totals.",
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Warning",
                value="Only use this for testing or if you need to reprocess wars.\n"
                      "Consider using `/clear_cwl_data` first to avoid duplicates.",
                inline=False
            )
            
            embed.add_field(
                name="Recommended Workflow",
                value="1. `/clear_cwl_data` - Clear current CWL data\n"
                      "2. `/reset_processed_wars` - Reset war tracking\n"
                      "3. `/fetch_cwl_stars` - Re-fetch all wars fresh",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"Processed wars table reset by {interaction.user.display_name}")
        
        except Exception as e:
            logger.error(f"Error resetting processed wars: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(CWLStarsCog(bot))
