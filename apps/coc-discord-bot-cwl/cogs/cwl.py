import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from datetime import datetime
from typing import List, Dict, Any, Optional
import urllib.parse

import config

API_BASE = "https://api.clashofclans.com/v1"

async def coc_get(session: aiohttp.ClientSession, path: str) -> Optional[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {config.SUPERCELL_API_TOKEN}"}
    async with session.get(API_BASE + path, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
        if resp.status != 200:
            return None
        return await resp.json()

class CWLCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="cwl_status", description="Show current CWL status")
    async def cwl_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        tag = config.CLAN_TAG or ""
        enc = urllib.parse.quote(tag, safe='')
        async with aiohttp.ClientSession() as session:
            group = await coc_get(session, f"/clans/{enc}/currentwar/leaguegroup")
            if not group or not group.get("rounds"):
                await interaction.followup.send("No CWL group data available.", ephemeral=True)
                return
            # Try to get the most recent war info
            war_tag = None
            for rd in reversed(group.get("rounds", [])):
                for wt in rd.get("warTags", []) or []:
                    if wt and wt != "#0":
                        war_tag = wt
                        break
                if war_tag:
                    break
            embed = discord.Embed(title="CWL Status", color=discord.Color.gold())
            if not war_tag:
                embed.description = "CWL group exists but wars are not available yet."
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            war_enc = urllib.parse.quote(war_tag, safe='')
            war = await coc_get(session, f"/clanwarleagues/wars/{war_enc}")
            if not war:
                embed.description = "Could not fetch current war details."
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            clan = war.get('clan', {})
            opp = war.get('opponent', {})
            state = war.get('state', 'unknown')
            embed.add_field(name="State", value=state, inline=True)
            embed.add_field(name="vs", value=f"{opp.get('name','?')}", inline=True)
            embed.add_field(name="Stars", value=f"{clan.get('stars',0)} - {opp.get('stars',0)}", inline=True)
            embed.add_field(name="Destruction", value=f"{clan.get('destructionPercentage',0)}% - {opp.get('destructionPercentage',0)}%", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="cwl_schedule", description="Show CWL schedule")
    async def cwl_schedule(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        tag = config.CLAN_TAG or ""
        enc = urllib.parse.quote(tag, safe='')
        async with aiohttp.ClientSession() as session:
            group = await coc_get(session, f"/clans/{enc}/currentwar/leaguegroup")
            if not group:
                await interaction.followup.send("No CWL group data.", ephemeral=True)
                return
            lines: List[str] = []
            for i, rd in enumerate(group.get('rounds', []), 1):
                war_tags = [wt for wt in (rd.get('warTags') or []) if wt and wt != '#0']
                lines.append(f"Round {i}: {', '.join(war_tags) if war_tags else 'TBD'}")
            await interaction.followup.send("\n".join(lines)[:1800] or "No schedule yet.", ephemeral=True)

    @app_commands.command(name="cwl_leaderboard", description="CWL stars leaderboard (current war)")
    async def cwl_leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        tag = config.CLAN_TAG or ""
        enc = urllib.parse.quote(tag, safe='')
        async with aiohttp.ClientSession() as session:
            group = await coc_get(session, f"/clans/{enc}/currentwar/leaguegroup")
            if not group:
                await interaction.followup.send("No CWL group data.", ephemeral=True)
                return
            war_tag = None
            for rd in reversed(group.get("rounds", [])):
                for wt in rd.get("warTags", []) or []:
                    if wt and wt != "#0":
                        war_tag = wt
                        break
                if war_tag:
                    break
            if not war_tag:
                await interaction.followup.send("No war available yet.", ephemeral=True)
                return
            war_enc = urllib.parse.quote(war_tag, safe='')
            war = await coc_get(session, f"/clanwarleagues/wars/{war_enc}")
            if not war:
                await interaction.followup.send("Could not fetch war details.", ephemeral=True)
                return
            members = (war.get('clan') or {}).get('members', [])
            lb = sorted(
                (
                    {
                        'name': m.get('name','?'),
                        'stars': sum(a.get('stars',0) for a in (m.get('attacks') or []))
                    }
                    for m in members
                ),
                key=lambda x: x['stars'], reverse=True
            )
            if not lb:
                await interaction.followup.send("No stars yet.", ephemeral=True)
                return
            lines = []
            for i, p in enumerate(lb[:15], 1):
                medal = "\U0001F947 " if i==1 else "\U0001F948 " if i==2 else "\U0001F949 " if i==3 else ""
                lines.append(f"{medal}{i}. {p['name']}: {p['stars']}\u2B50")
            embed = discord.Embed(title="CWL Stars (current war)", description="\n".join(lines), color=discord.Color.gold())
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(CWLCog(bot))
