import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from typing import Optional, Dict, Any
import urllib.parse

import config

API_BASE = "https://api.clashofclans.com/v1"

async def coc_get(session: aiohttp.ClientSession, path: str) -> Optional[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {config.SUPERCELL_API_TOKEN}"}
    async with session.get(API_BASE + path, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
        if resp.status != 200:
            return None
        return await resp.json()

class Whois(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whois", description="Show player info by tag or name in current clan")
    @app_commands.describe(player="#TAG or player name in your clan")
    async def whois(self, interaction: discord.Interaction, player: str):
        await interaction.response.defer(ephemeral=True)
        async with aiohttp.ClientSession() as session:
            # If looks like a tag, query player API directly; else search current clan members by name
            if player.strip().startswith('#') or player.strip().startswith('%23'):
                tag = player.strip()
                enc_tag = urllib.parse.quote(tag, safe='')
                data = await coc_get(session, f"/players/{enc_tag}")
                if not data:
                    await interaction.followup.send("Player not found.", ephemeral=True)
                    return
                await interaction.followup.send(embed=self._profile_embed(data), ephemeral=True)
                return
            # Search clan member list for name match
            tag = config.CLAN_TAG or ""
            enc = urllib.parse.quote(tag, safe='')
            clan = await coc_get(session, f"/clans/{enc}")
            member = None
            for m in (clan or {}).get('memberList', []):
                if m.get('name', '').lower() == player.lower():
                    member = m
                    break
            if not member:
                await interaction.followup.send("No clan member by that name.", ephemeral=True)
                return
            enc_tag = urllib.parse.quote(member.get('tag',''), safe='')
            data = await coc_get(session, f"/players/{enc_tag}")
            if not data:
                await interaction.followup.send("Profile lookup failed.", ephemeral=True)
                return
            await interaction.followup.send(embed=self._profile_embed(data), ephemeral=True)

    def _profile_embed(self, p: Dict[str, Any]) -> discord.Embed:
        name = p.get('name','?'); tag = p.get('tag','')
        embed = discord.Embed(title=f"Who is {name}?", color=discord.Color.gold())
        league = (p.get('league') or {}).get('name')
        th = p.get('townHallLevel'); thw = p.get('townHallWeaponLevel')
        embed.add_field(name="Tag", value=tag or "?", inline=True)
        if league:
            embed.add_field(name="League", value=league, inline=True)
        if th:
            embed.add_field(name="Town Hall", value=f"TH{th}{' (W'+str(thw)+')' if thw else ''}", inline=True)
        # Hero progress (show current|max short)
        names = ["Barbarian King","Archer Queen","Grand Warden","Royal Champion"]
        hero_bits = []
        for n in names:
            cur = None; mx = None
            for h in p.get('heroes', []) or []:
                if h.get('name') == n:
                    cur, mx = h.get('level'), h.get('maxLevel'); break
            if cur is not None:
                hero_bits.append(f"{n.split()[1]} {cur}{'|'+str(mx) if mx else ''}")
        if hero_bits:
            embed.add_field(name="Heroes", value=" | ".join(hero_bits), inline=False)
        # War stars and XP
        embed.add_field(name="War Stars", value=str(p.get('warStars', 0)), inline=True)
        embed.add_field(name="XP", value=str(p.get('expLevel', 0)), inline=True)
        return embed

async def setup(bot):
    await bot.add_cog(Whois(bot))
