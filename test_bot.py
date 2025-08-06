#!/usr/bin/env python3
"""
Minimal test bot to verify Discord slash commands are working
"""
import discord
from discord.ext import commands
import os
import sys

# Add the shared config path
sys.path.append('shared/config')
sys.path.append('apps/coc-discord-bot')

# Load environment variables from the .env file
from dotenv import load_dotenv
load_dotenv('shared/config/.env')

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID_STR = os.getenv("DISCORD_GUILD_ID")

if not DISCORD_BOT_TOKEN or not GUILD_ID_STR:
    print("Missing environment variables!")
    exit(1)

GUILD_ID = int(GUILD_ID_STR)

print(f"Token: {DISCORD_BOT_TOKEN[:10]}...")
print(f"Guild ID: {GUILD_ID}")

class TestBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        
        # Add test commands
        @self.tree.command(name="test_ping", description="Simple test command")
        async def test_ping(interaction: discord.Interaction):
            await interaction.response.send_message("✅ Test command works!", ephemeral=True)
        
        @self.tree.command(name="test_cwl", description="Test CWL system")
        async def test_cwl(interaction: discord.Interaction):
            await interaction.response.send_message("✅ CWL commands are working!", ephemeral=True)
        
        # Sync commands to guild
        guild = discord.Object(id=GUILD_ID)
        synced = await self.tree.sync(guild=guild)
        print(f'Synced {len(synced)} commands to guild {GUILD_ID}')
        
        # Also try global sync
        global_synced = await self.tree.sync()
        print(f'Synced {len(global_synced)} commands globally')

if __name__ == "__main__":
    bot = TestBot()
    bot.run(DISCORD_BOT_TOKEN)
