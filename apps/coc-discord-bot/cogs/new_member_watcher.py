import discord
from discord.ext import commands, tasks
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Set, Optional, List

import config
import database_optimized as database
from cogs.roster import fetch_clan_members
import requests

logger = logging.getLogger("new_member_watcher")

ANNOUNCE_CHANNEL_ID: Optional[int] = getattr(config, 'CWL_REWARDS_CHANNEL_ID', None)

# Simple in-memory cache of last seen member tags
_last_seen: Set[str] = set()

class NewMemberWatcher(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.loop_interval_minutes = 5
        self._task = self.poll_for_new_members
        self._task.start()

    async def cog_unload(self):
        try:
            self._task.cancel()
        except Exception:
            pass

    @tasks.loop(minutes=5)
    async def poll_for_new_members(self):
        await self.bot.wait_until_ready()
        # Load current members from API
        members: List[Dict] = fetch_clan_members()
        if not members:
            return
        # Normalize tags from API
        current_tags: Set[str] = {str(m.get('tag')).upper() for m in members if m.get('tag')}
        # Get tags present in DB (persistent baseline)
        try:
            db_players = database.get_player_data()
        except Exception:
            db_players = []
        db_tags: Set[str] = {str(p.get('tag')).upper() for p in db_players if p.get('tag')}
        # Initialize runtime cache
        global _last_seen
        if not _last_seen:
            _last_seen = set(db_tags)
        # New members are those in current API but not in DB
        new_tags = [t for t in current_tags if t not in db_tags]
        if not new_tags:
            return
        # Announce each new member (avoid duplicates within one runtime using _last_seen)
        for tag in new_tags:
            if tag in _last_seen:
                continue
            try:
                m = next((mm for mm in members if str(mm.get('tag','')).upper() == tag), None)
                if not m:
                    continue
                await self.announce_new_member(m)
            except Exception as e:
                logger.warning(f"Failed to announce new member {tag}: {e}")
            finally:
                _last_seen.add(tag)

    async def announce_new_member(self, member: Dict):
        channel_id = int(ANNOUNCE_CHANNEL_ID) if isinstance(ANNOUNCE_CHANNEL_ID, int) else None
        channel = self.bot.get_channel(channel_id) if channel_id else None
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            logger.warning("Announcement channel not found for new member joins")
            return
        name = member.get('name')
        tag = member.get('tag') or ""
        # Try to ensure DB has this player (creates minimal row if missing)
        try:
            if tag:
                database.ensure_player_exists_by_tag(tag, name)
        except Exception:
            pass
        # Fetch richer stats from official API
        stats = self.fetch_player_stats(tag) if tag else {}
        th = stats.get('townHallLevel') if stats else None
        trophies = stats.get('trophies') if stats else None
        war_stars = stats.get('warStars') if stats else None
        heroes = stats.get('heroes', []) if stats else []
        hero_summary = ", ".join([f"{h.get('name','?')} {h.get('level','?')}" for h in heroes if h.get('village') == 'home'])
        # Links: Clash of Stats search and in-game deep link
        safe_tag = tag.replace('#','%23') if tag else ''
        cos_url = f"https://www.clashofstats.com/search/{safe_tag}"
        deep_link = f"https://link.clashofclans.com/?action=OpenPlayerProfile&tag={safe_tag}"
        embed = discord.Embed(
            title=f"New Member Joined: {name}",
            description=f"Welcome {name}!",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Tag", value=tag or "?", inline=True)
        if th:
            embed.add_field(name="Town Hall", value=str(th), inline=True)
        if trophies is not None:
            embed.add_field(name="Trophies", value=str(trophies), inline=True)
        if war_stars is not None:
            embed.add_field(name="War Stars", value=str(war_stars), inline=True)
        if hero_summary:
            embed.add_field(name="Heroes", value=hero_summary[:1024], inline=False)
        embed.add_field(name="Links", value=f"[In-Game Profile]({deep_link}) | [Clash of Stats]({cos_url})", inline=False)
        try:
            await channel.send(content=f"🎉 Welcome <{tag}> {name} to the clan!", embed=embed)
        except Exception as e:
            logger.warning(f"Failed to send new member embed: {e}")

    def fetch_player_stats(self, player_tag: str):
        try:
            token = config.get_api_token()
            tag = player_tag.replace('#', '%23')
            url = f"https://api.clashofclans.com/v1/players/{tag}"
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.get(url, headers=headers, timeout=10, verify=not config.DEV_MODE)
            if r.status_code != 200:
                return {}
            return r.json()
        except Exception:
            return {}

async def setup(bot):
    await bot.add_cog(NewMemberWatcher(bot))
