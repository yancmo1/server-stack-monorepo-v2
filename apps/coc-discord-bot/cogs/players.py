from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from tabulate import tabulate

import config
import database_optimized as database
from config import is_leader_or_admin
from utils import has_any_role_id, is_admin, is_admin_leader_co_leader, is_newbie, format_last_bonus, days_ago
from utils_supercell import get_player_clan_history

MAX_MESSAGE_CHUNK_LENGTH = 1900

import logging
logger = logging.getLogger("players")

class PlayersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="list_players",
        description="List All Players  Admin, Leader, Co-Leader",
    )
    @app_commands.check(is_admin_leader_co_leader)
    @app_commands.guilds(discord.Object(id=config.GUILD_ID))
    @app_commands.describe(
        sort_by="Sort players by this field",
    )
    async def list_players(
        self,
        interaction: discord.Interaction,
        sort_by: Optional[str] = "name",
    ):
        await interaction.response.defer(ephemeral=True)
        players = database.get_player_data()

    @app_commands.command(
        name="record_missed",
        description="Record Missed — Admin, Leader, Co-Leader",
    )
    @app_commands.check(is_admin_leader_co_leader)
    @app_commands.guilds(discord.Object(id=config.GUILD_ID))
    @app_commands.describe(player_name="The name of the player who missed an attack.")
    async def record_missed_attack(
        self, interaction: discord.Interaction, player_name: str
    ):
        player = database.get_player_by_name(player_name)
        if not player:
            await interaction.response.send_message(
                f"Player `{player_name}` not found.", ephemeral=True
            )
            return
        database.update_player_missed_attacks(player_name)
        await interaction.response.send_message(
            f"Recorded a missed attack for `{player_name}`."
        )

    @record_missed_attack.autocomplete("player_name")
    async def autocomplete_player_name(
        self, interaction: discord.Interaction, current: str):
        names = database.get_autocomplete_names(current)
        return [app_commands.Choice(name=n, value=n) for n in names[:25]]

    @app_commands.command(
        name="who_is",
        description="Who is? — Show player info, last 5 clans, and average days per clan (mobile friendly)",
    )
    @app_commands.check(is_admin_leader_co_leader)
    @app_commands.guilds(discord.Object(id=config.GUILD_ID))
    @app_commands.describe(player_name="The name of the player to show details for.")
    async def who_is(
        self, interaction: discord.Interaction, player_name: str
    ):
        player = database.get_player_by_name(player_name)
        if not player:
            await interaction.response.send_message(
                f"Player `{player_name}` not found.", ephemeral=True
            )
            return
        # Compose the response in the requested format
        lines = []
        lines.append(f"Who is {player.get('name', player_name)}?")
        # Role
        if player.get('role'):
            lines.append(str(player['role']))
        # Join Date
        if player.get('join_date'):
            lines.append(f"Join Date: {player['join_date']}")
        # Notes
        if player.get('notes'):
            lines.append(f"Notes: {player['notes']}")
        # Last 5 Clans & Average stay (from Supercell API)
        lines.append("Last 5 Clans & Days in Each (from Supercell API):")
        last_clans = []
        avg_days = 0
        tag = player.get('tag')
        if tag:
            history = get_player_clan_history(tag)
            if history:
                last_clans = [f"{c['clan_name']} ({c['join_date']} - {c['leave_date']}) — {c['days_in_clan']} days" for c in history]
                days_list = [c['days_in_clan'] for c in history if c['days_in_clan'] > 0]
                if days_list:
                    avg_days = sum(days_list) // len(days_list)
        if last_clans:
            lines.extend(last_clans)
        if avg_days:
            lines.append(f"Avg Days/Clan: {avg_days}")
        await interaction.response.send_message("\n".join(lines))

    @who_is.autocomplete("player_name")
    async def autocomplete_who_is(
        self, interaction: discord.Interaction, current: str):
        logger.info(f"[AUTOCOMPLETE] who_is called with current='{current}'")
        names = database.get_autocomplete_names(current)
        logger.info(f"[AUTOCOMPLETE] who_is returning: {names}")
        return [app_commands.Choice(name=n, value=n) for n in names[:25]]

    @app_commands.command(
        name="list_players",
        description="List All Players — Admin, Leader, Co-Leader",
    )
    @app_commands.check(is_admin_leader_co_leader)
    @app_commands.guilds(discord.Object(id=config.GUILD_ID))
    @app_commands.describe(
        sort_by="Sort players by this field",
    )
    async def list_players(
        self,
        interaction: discord.Interaction,
        sort_by: Optional[str] = "name",
    ):
        await interaction.response.defer(ephemeral=True)
        players = database.get_player_data()
        if not players:
            await interaction.followup.send(
                "No players found in the database.", ephemeral=True
            )
            return
        try:
            import requests
            clan_tag = config.CLAN_TAG or ""
            if not clan_tag:
                await interaction.followup.send(
                    "⚠️ No clan tag configured. Showing all database players.",
                    ephemeral=True,
                )
            else:
                api_token = config.SUPERCELL_API_TOKEN or ""
                if not api_token:
                    await interaction.followup.send(
                        "⚠️ No API token configured. Showing all database players.",
                        ephemeral=True,
                    )
                else:
                    headers = {"Authorization": f"Bearer {api_token}"}
                    url = f"https://api.clashofclans.com/v1/clans/{clan_tag.replace('#', '%23')}"
                    resp = requests.get(url, headers=headers, timeout=10, verify=not config.DEV_MODE)
                    if resp.status_code == 200:
                        clan_data = resp.json()
                        active_tags = set()
                        for member in clan_data.get("memberList", []):
                            member_tag = member.get("tag")
                            if member_tag:
                                active_tags.add(member_tag.replace('#', ''))
                        filtered_players = []
                        for p in players:
                            player_tag = p.get("tag")
                            if player_tag:
                                clean_tag = player_tag.replace("#", "")
                                if clean_tag in active_tags:
                                    filtered_players.append(p)
                        players = filtered_players
                    else:
                        await interaction.followup.send(
                            "⚠️ Could not fetch current clan roster. Showing all database players.",
                            ephemeral=True,
                        )
        except Exception as e:
            await interaction.followup.send(
                f"⚠️ Could not fetch current clan roster: {str(e)}. Showing all database players.",
                ephemeral=True,
            )
        valid_sort_fields = [
            "name",
            "role",
            "missed_attacks",
            "bonus_count",
            "join_date",
        ]
        if sort_by not in valid_sort_fields:
            sort_by = "name"
        def sort_key(player):
            value = player.get(sort_by)
            if value is None:
                return ""
            return str(value).lower() if isinstance(value, str) else value
        players.sort(key=sort_key)
        player_lines = []
        for player in players:
            name = player.get("name", "Unknown")
            role = player.get("role", "Unknown")
            missed_attacks = player.get("missed_attacks", 0) or 0
            bonus_count = player.get("bonus_count", 0) or 0
            bonus_eligibility = player.get("bonus_eligibility", 1)
            inactive = player.get("inactive", 0)
            tag = player.get("tag", "N/A")
            notes = player.get("notes", "")
            eligibility_icon = "✅" if bonus_eligibility else "❌"
            active_icon = "🔴" if inactive else "🟢"
            role_icon = {
                "Leader": "👑",
                "Co-Leader": "🔥",
                "Elder": "⭐",
                "Member": "👤",
            }.get(role, "❓")
            player_line = f"{role_icon} **{name}** ({tag})\n"
            player_line += (
                f"   Role: {role} | Missed: {missed_attacks} | Bonuses: {bonus_count} | Eligible: {eligibility_icon} | CWL: {active_icon}"
            )
            if notes:
                player_line += f"\n   📝 {notes}"
            player_lines.append(player_line)
        if not player_lines:
            await interaction.followup.send("No active players found.", ephemeral=True)
            return
        chunk_size = 15
        total_players = len(player_lines)
        for i in range(0, len(player_lines), chunk_size):
            chunk = player_lines[i : i + chunk_size]
            chunk_start = i + 1
            chunk_end = min(i + chunk_size, total_players)
            embed = discord.Embed(
                title=f"📋 Player List ({chunk_start}-{chunk_end} of {total_players})",
                description="\n\n".join(chunk),
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="Legend",
                value="👑 Leader | 🔥 Co-Leader | ⭐ Elder | 👤 Member\n✅ Bonus Eligible | ❌ Not Eligible | 🟢 CWL Active | 🔴 CWL Inactive",
                inline=False,
            )
            embed.set_footer(
                text=f"Sorted by: {sort_by} | Active players only"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @list_players.autocomplete("sort_by")
    async def autocomplete_sort_by(
        self, interaction: discord.Interaction, current: str):
        fields = ["name", "role", "missed_attacks", "bonus_count", "join_date"]
        matching = [field for field in fields if field.startswith(current.lower())]
        return [app_commands.Choice(name=field, value=field) for field in matching[:5]]


async def setup(bot):
    await bot.add_cog(PlayersCog(bot))
    # Force command tree sync to ensure Discord registers autocomplete
    await bot.tree.sync()
