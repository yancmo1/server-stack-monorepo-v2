#!/usr/bin/env python3
import asyncio
import discord
import config

async def check_commands():
    bot = discord.Client(intents=discord.Intents.default())
    await bot.login(config.DISCORD_BOT_TOKEN)
    
    tree = discord.app_commands.CommandTree(bot)
    commands = await tree.fetch_commands(guild=discord.Object(id=config.GUILD_ID))
    
    print(f"Total registered commands: {len(commands)}")
    for cmd in commands:
        print(f"  - {cmd.name}: {cmd.description}")
    
    await bot.close()

if __name__ == "__main__":
    asyncio.run(check_commands())
