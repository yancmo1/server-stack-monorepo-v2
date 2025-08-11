from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from tabulate import tabulate

import config
import database_optimized as database
from config import is_leader_or_admin
from utils import has_any_role_id, is_admin, is_admin_leader_co_leader, is_newbie, format_last_bonus, days_ago
from utils_supercell import get_player_clan_history, get_player_profile

MAX_MESSAGE_CHUNK_LENGTH = 1900

import logging
logger = logging.getLogger("players")

class PlayersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # list_players defined later with full implementation

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
        tag = player.get("tag")
        if not tag:
            await interaction.response.send_message(
                f"Player `{player_name}` has no tag on file; cannot record missed attack.", ephemeral=True
            )
            return
        try:
            new_count = database.increment_player_missed_by_tag(tag, by=1)
            await interaction.response.send_message(
                f"Recorded a missed attack for `{player_name}`. Total missed: {new_count}"
            )
        except Exception as e:
            await interaction.response.send_message(
                f"Failed to record missed attack: {e}", ephemeral=True
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

        await interaction.response.defer()

        name = player.get('name', player_name)
        tag = player.get('tag', '')
        clean_tag = tag.replace('#','') if tag else ''
        cos_url = f"https://www.clashofstats.com/players/{name}-{clean_tag}" if clean_tag else None

        profile = get_player_profile(tag) if tag else None

        # Top line: Name (link to COS)
        title_name = f"[{name} {tag}]({cos_url})" if cos_url else f"{name} {tag or ''}"
        embed = discord.Embed(title=f"Who is {name}?", color=discord.Color.gold())
        embed.add_field(name="Player", value=title_name, inline=False)

        # Role, League, TH with weapon
        role = player.get('role') or 'Member'
        league = profile.get('league', {}).get('name') if profile else None
        town_hall = profile.get('townHallLevel') if profile else None
        th_weapon = profile.get('townHallWeaponLevel') if profile else None
        line2 = f"{role}"
        if league:
            line2 += f" | {league}"
        if town_hall:
            line2 += f" | TH{town_hall}{' (Weapon '+str(th_weapon)+')' if th_weapon else ''}"
        embed.add_field(name="Role · League · Town Hall", value=line2, inline=False)

        # Heroes current|max
        def hero_level(name_key: str):
            if not profile:
                return None, None
            for h in profile.get('heroes', []) or []:
                if h.get('name') == name_key:
                    return h.get('level'), h.get('maxLevel')
            return None, None
        hero_names = ["Barbarian King","Archer Queen","Grand Warden","Royal Champion","Battle Machine"]
        hero_lines = []
        for hn in hero_names:
            cur, mx = hero_level(hn)
            if cur is not None:
                emoji = {
                    "Barbarian King":"🛡️",
                    "Archer Queen":"🏹",
                    "Grand Warden":"🧙",
                    "Royal Champion":"🏇",
                    "Battle Machine":"🤖",
                }.get(hn, "⭐")
                hero_lines.append(f"{emoji} {hn}: {cur}{'|'+str(mx) if mx else ''}")
        if hero_lines:
            embed.add_field(name="Heroes (current|max)", value=" | ".join(hero_lines), inline=False)

        # Progress metrics (counts based on profiles arrays lengths)
        def count_progress(key: str):
            if not profile:
                return None
            items = profile.get(key, []) or []
            maxed = sum(1 for it in items if it.get('level') == it.get('maxLevel'))
            return maxed, len(items)
        heroes_prog = (sum(1 for h in (profile.get('heroes', []) or []) if h.get('level')==h.get('maxLevel')), len(profile.get('heroes', []) or [])) if profile else (None,None)
        troops_prog = count_progress('troops')
        spells_prog = count_progress('spells')
        def fmt_prog(t):
            if not t or t[0] is None:
                return "N/A"
            cur, total = t
            pct = int((cur/total)*100) if total else 0
            color = "🟩" if pct>=80 else ("🟨" if pct>=50 else "🟥")
            return f"{color} {cur}/{total} ({pct}%)"
        pm_lines = []
        pm_lines.append(f"Heroes: {fmt_prog(heroes_prog)}")
        if troops_prog:
            pm_lines.append(f"Troops: {fmt_prog(troops_prog)}")
        if spells_prog:
            pm_lines.append(f"Spells: {fmt_prog(spells_prog)}")
        embed.add_field(name="Progress", value=" | ".join(pm_lines), inline=False)

        # XP and War Stars
        xp = profile.get('expLevel') if profile else player.get('xp_level')
        stars = profile.get('warStars') if profile else player.get('war_stars')
        embed.add_field(name="XP · War Stars", value=f"{xp or 'N/A'} · {stars or 'N/A'}", inline=False)

        # Notes and Join Date
        notes = player.get('notes')
        join_date = player.get('join_date')
        footer_bits = []
        if join_date:
            footer_bits.append(f"Joined: {join_date}")
        if notes:
            footer_bits.append(f"Notes: {notes}")
        if footer_bits:
            embed.set_footer(text=" | ".join(footer_bits))

        # Last 5 clans and avg days
        avg_days = 0
        history = get_player_clan_history(tag) if tag else []
        if history:
            days_list = [c['days_in_clan'] for c in history if c['days_in_clan'] > 0]
            if days_list:
                avg_days = sum(days_list) // len(days_list)
            hist_lines = [f"• {c['clan_name']} — {c['days_in_clan']} days ({c['join_date']} → {c['leave_date']})" for c in history]
            embed.add_field(name="Last 5 Clans", value="\n".join(hist_lines), inline=False)
        if avg_days:
            embed.add_field(name="Avg Days/Clan", value=str(avg_days), inline=True)

        await interaction.followup.send(embed=embed)

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
