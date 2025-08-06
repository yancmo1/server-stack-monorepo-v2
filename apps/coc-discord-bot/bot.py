# Main.py
# This is the main file for your Discord  bot. It initializes the bot, loads cogs, and handles command synchronization.
import asyncio
import traceback
import os
import platform
import discord
from discord.ext import commands
from discord import app_commands
import sys

import config
from logging_config import setup_logging, get_logger, log_performance
from utils_email import send_crash_email

# Determine environment (development or production)
is_development = os.path.exists(".development")
is_production = os.path.exists(".production")

# Initialize logging system
setup_logging()
logger = get_logger("bot")

if is_development:
    logger.info("🧪 Running in DEVELOPMENT mode")
    logger.info(f"🧪 System: {platform.system()}")
    logger.info(f"🧪 Using database: {config.DB_PATH}")
elif is_production:
    logger.info("🚀 Running in PRODUCTION mode")
    logger.info(f"🚀 System: {platform.system()}")
    logger.info(f"🚀 Using database: {config.DB_PATH}")
else:
    # Default to production mode if no flags exist (safer for Pi deployments)
    logger.warning("⚠️ No environment flag detected, defaulting to PRODUCTION mode")
    logger.warning("⚠️ Create .development file locally or .production file on your server")
    is_production = True

logger.info("If you see this, Python output is working!")

intents = discord.Intents.default()
intents.message_content = True  # Enable if you want to process message content
intents.members = True  # Enable member events for slash commands and role sync


class CustomBot(commands.Bot):
    async def setup_hook(self):
        logger.info("Setup hook starting...")
        try:
            for cmd in self.tree.get_commands():
                logger.debug(f"Found command: {cmd.name}")
        except Exception as e:
            logger.error(f"Error in setup_hook: {e}")


bot = CustomBot(command_prefix="!", intents=intents)

COGS = [
    "cogs.bonuses",
    "cogs.roster", 
    "cogs.players",
    "cogs.misc",
    "cogs.cwl",
    "cogs.missed_attacks",
    # Advanced cogs to be added later:
    # "cogs.link",
    "cogs.cwl_stars", 
    "cogs.notifications",
    # "cogs.rolesync",
    "cogs.command_groups",
    # "cogs.error_monitoring",
    # "cogs.performance_monitoring",
]

@bot.event
async def on_ready():
    user_id = bot.user.id if bot.user else "Unknown"
    logger.info(f"Bot connected as {bot.user} (ID: {user_id})")
    try:
        logger.info("Loading cogs...")
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}", exc_info=True)
        # Only sync commands if .sync_commands file exists
        if os.path.exists(".sync_commands"):
            await bot.tree.sync(guild=discord.Object(id=config.GUILD_ID))
            logger.info(f"Synced commands to guild {config.GUILD_ID}")
        else:
            logger.info("Skipping command sync to avoid rate limits.")
    except Exception as e:
        logger.error(f"Failed in on_ready: {e}", exc_info=True)

async def main():
    try:
        if not config.DISCORD_BOT_TOKEN:
            raise RuntimeError("DISCORD_BOT_TOKEN is not set in the environment.")
        logger.info("Starting bot...")
        await bot.start(config.DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        err_str = str(e)
        if 'Improper token' in err_str or 'LoginFailure' in err_str or '401 Unauthorized' in err_str:
            subject = "ClashCWLBot CRITICAL: Discord Token Error"
            body = f"Bot failed to start due to token error.\n\nError: {err_str}\n\nCheck your Discord Developer Portal."
            send_crash_email(subject, body)
            logger.critical("Bot exiting due to Discord token error. Notification sent.")
            sys.exit(10)
        subject = "ClashCWLBot CRITICAL: Bot Crash"
        body = f"Bot crashed with error:\n{err_str}\n\nCheck logs for details."
        send_crash_email(subject, body)
        logger.critical("Bot exiting due to crash. Notification sent.")
        import time
        time.sleep(30)
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ClashCWLBot runner")
    parser.add_argument("--sync-commands", action="store_true", help="Manually sync slash commands (PRODUCTION SAFE)")
    parser.add_argument("--healthcheck", action="store_true", help="Run health check and exit")
    args = parser.parse_args()
    manual_sync_flag = args.sync_commands
    
    # Handle health check
    if args.healthcheck:
        logger.info("🏥 Running health check...")
        try:
            # Basic health checks
            if not config.DISCORD_BOT_TOKEN:
                logger.error("❌ DISCORD_BOT_TOKEN not found")
                sys.exit(1)
            if not config.CLAN_TAG:
                logger.error("❌ CLAN_TAG not found")
                sys.exit(1)
            # Check if we can import required modules
            import discord
            logger.info("✅ Discord module imported successfully")
            logger.info("✅ Health check passed")
            sys.exit(0)
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            sys.exit(1)
    
    logger.info(f"Bot starting from file: {__file__} | Date: 2025-07-17")
    logger.info(f"DISCORD_BOT_TOKEN loaded: {str(config.DISCORD_BOT_TOKEN)[:4]}...{str(config.DISCORD_BOT_TOKEN)[-4:]}")
    logger.info(f"GMAIL_USER loaded: {str(config.GMAIL_USER)[:4]}...{str(config.GMAIL_USER)[-4:]}")
    logger.info(f"GMAIL_PASS loaded: {str(config.GMAIL_PASS)[:4]}...{str(config.GMAIL_PASS)[-4:]}")
    asyncio.run(main())
