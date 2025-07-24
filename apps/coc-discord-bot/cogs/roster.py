from datetime import datetime

import discord
import requests
from discord import app_commands
from discord.ext import commands

import config
import database_optimized as database
from config import is_leader_or_admin
from utils import has_any_role_id, is_admin, is_admin_leader_co_leader, is_newbie, format_last_bonus, days_ago

GUILD_ID = discord.Object(id=config.GUILD_ID)

import logging
logger = logging.getLogger("roster")


def fetch_clan_members():
    logger.debug("Entered fetch_clan_members")
    clan_tag = config.CLAN_TAG or ""
    url = f"https://api.clashofclans.com/v1/clans/{clan_tag.replace('#', '%23')}/members"
    api_token = config.get_api_token()
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        logger.debug(f"About to make API request to {url} with headers {headers}")
        resp = requests.get(url, headers=headers, timeout=10, verify=not config.DEV_MODE)
        logger.info(f"API request complete, status: {resp.status_code}")
        logger.info(f"API raw response: {resp.text}")
        if resp.status_code == 403:
            logger.error("API request returned 403 Forbidden - IP not authorized for this API key")
            return []
        elif resp.status_code == 404:
            logger.error("API request returned 404 Not Found - clan not found")
            return []
        resp.raise_for_status()
        data = resp.json()
        logger.debug("JSON parsed")
        members = data.get("items", [])
        if not members:
            logger.warning("API returned empty member list - this might be an IP restriction issue")
            return []
        logger.info(f"Successfully fetched {len(members)} clan members")
        return [
            {
                "name": m["name"],
                "tag": m["tag"],
                "role": m.get("role", "Member")
                .replace("coLeader", "Co-Leader")
                .replace("admin", "Elder")
                .replace("member", "Member")
                .replace("leader", "Leader"),
            }
            for m in data.get("items", [])
        ]
    except Exception as e:
        logger.debug(f"Error in fetch_clan_members: {e}")
        return []


def add_removed_player(name, tag):
    safe_name = name or "Unknown"
    safe_tag = tag or "Unknown"
    with database.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO removed_players (name, tag, removed_date) VALUES (%s, %s, %s)",
            (safe_name, safe_tag, datetime.utcnow().strftime("%Y-%m-%d")),
        )
        conn.commit()


class RosterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="roster_update",
        description="Roster Update — Admin, Leader, Co-Leader"
    )
    @app_commands.check(is_admin_leader_co_leader)
    @app_commands.guilds(GUILD_ID)
    async def rosterupdate(self, interaction: discord.Interaction):
        logger.debug("rosterupdate handler CALLED!")
        try:
            try:
                await interaction.response.defer(ephemeral=True)
            except Exception as e:
                logger.error(f"Could not defer interaction: {e}")
                return
            logger.debug("Starting fetch_clan_members")
            coc_players = fetch_clan_members()
            logger.info(f"fetch_clan_members returned {len(coc_players)} players")
            if len(coc_players) == 0:
                error_msg = (
                    "⚠️ **SAFETY CHECK FAILED** ⚠️\n\n"
                    "API returned 0 clan members. This is likely due to:\n"
                    "• IP address not authorized for current API key\n"
                    "• API connectivity issues\n"
                    "• Clan API temporarily unavailable\n\n"
                    "**Roster update cancelled to prevent mass player deletion.**\n\n"
                    "Please check your API key configuration and try again."
                )
                await interaction.followup.send(error_msg, ephemeral=True)
                return
            db_players = database.get_player_data()
            logger.info(f"get_player_data returned {len(db_players)} players")
            if len(db_players) > 10 and len(coc_players) < len(db_players) * 0.5:
                warning_msg = (
                    "⚠️ **SAFETY WARNING** ⚠️\n\n"
                    f"API returned {len(coc_players)} players but database has {len(db_players)} players.\n"
                    "This represents a significant drop (>50%) which may indicate an API issue.\n\n"
                    "**Roster update cancelled for safety.**\n\n"
                    "If this is expected (e.g., mass clan departure), please verify manually."
                )
                await interaction.followup.send(warning_msg, ephemeral=True)
                return
            coc_tags = set(p["tag"] for p in coc_players)
            db_tags = set(p["tag"] for p in db_players)
            logger.debug("API tags: %s", [p["tag"] for p in coc_players])
            logger.debug("DB tags: %s", [p["tag"] for p in db_players])
            logger.debug("coc_players: %s", coc_players)
            logger.debug("db_players: %s", db_players)
            with database.get_connection() as conn:
                cur = conn.cursor()
                for p in coc_players:
                    cur.execute(
                        "UPDATE players SET role = %s WHERE LOWER(name) = LOWER(%s)",
                        (p["role"], p["name"]),
                    )
                conn.commit()
            new_players = [p for p in coc_players if p["tag"] not in db_tags]
            logger.info(f"{len(new_players)} new players to add")
            for p in new_players:
                p = {k: v for k, v in p.items() if k != 'id'}
                database.add_player(
                    name=p.get("name", ""),
                    tag=p.get("tag", ""),
                    join_date=datetime.utcnow().strftime("%Y-%m-%d"),
                    bonus_eligibility=1,
                    bonus_count=0,
                    last_bonus_date=None,
                    missed_attacks=0,
                    notes=None,
                    role=p.get("role", "")
                )
            removed_players = [p for p in db_players if p["tag"] not in coc_tags]
            logger.info(f"{len(removed_players)} players to remove")
            for p in removed_players:
                logger.debug(f"Removing player: name='{p.get('name')}', tag='{p.get('tag')}'")
                add_removed_player(p.get("name"), p.get("tag"))
                with database.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "DELETE FROM players WHERE tag = %s",
                        (p.get("tag"),)
                    )
                    conn.commit()
            msg = (
                f"Roster updated!\n"
                f"Added: {', '.join(p['name'] for p in new_players) or 'None'}\n"
                f"Removed: {', '.join(p['name'] for p in removed_players) or 'None'}"
            )
            logger.info("Roster update complete")
            await interaction.followup.send(msg, ephemeral=True)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"/rosterupdate: {e}\n{tb}")
            try:
                await interaction.followup.send(f"Error: {e}", ephemeral=True)
            except Exception as e2:
                logger.error(f"Could not send error message: {e2}")
        finally:
            logger.debug("/rosterupdate finished (finally block)")


async def setup(bot):
    await bot.add_cog(RosterCog(bot))
