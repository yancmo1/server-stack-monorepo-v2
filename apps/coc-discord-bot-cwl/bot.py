import asyncio
import logging
import os
import sys
import platform

import discord
from discord.ext import commands
from discord import app_commands

import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("cwl-dev-bot")

intents = discord.Intents.none()
intents.guilds = True

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        # Load cogs
        await self.load_extension("cogs.cwl")
        await self.load_extension("cogs.whois")
        # Sync on start if requested
        if config.SYNC_ON_START:
            await self.sync_commands()

    async def sync_commands(self):
        try:
            if config.DISCORD_GUILD_ID:
                guild = discord.Object(id=config.DISCORD_GUILD_ID)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} commands to guild {config.DISCORD_GUILD_ID}")
            else:
                synced = await self.tree.sync()
                logger.info(f"Globally synced {len(synced)} commands (can take a few minutes to appear)")
        except Exception as e:
            logger.error(f"Command sync failed: {e}")

bot = Bot()

@bot.event
async def on_ready():
    user = bot.user
    uid = user.id if user else "?"
    logger.info(f"Logged in as {user} (ID: {uid}) on {platform.node()}")

async def main(sync_only: bool = False):
    if sync_only:
        async with bot:
            await bot.setup_hook()
            await bot.sync_commands()
        return
    async with bot:
        # config enforces presence, but cast to str for type-checkers
        await bot.start(str(config.DISCORD_BOT_TOKEN))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--sync', action='store_true', help='Sync commands and exit')
    args = parser.parse_args()
    asyncio.run(main(sync_only=args.sync))
