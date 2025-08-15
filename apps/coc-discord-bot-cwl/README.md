# coc-discord-bot-cwl (DEV)

A minimal, clean Clash of Clans Discord bot focused only on:
- CWL commands (status, schedule, leaderboard)
- /whois (by tag or by current clan name)

Design goals:
- No database dependency (reads live data from Clash API)
- Async HTTP via aiohttp (non-blocking)
- Small, testable, and safe to run locally against a test guild

## Requirements
- Python 3.11+
- Discord Bot Token with applications.commands
- Clash of Clans API token

## Environment variables
Set these environment variables in your shell before running:
- DISCORD_BOT_TOKEN
- DISCORD_GUILD_ID          # test guild ID (optional: if omitted, commands register globally)
- SUPERCELL_API_TOKEN
- CLAN_TAG                  # e.g. #ABC123
- SYNC_ON_START=true        # optional: force sync on boot

## Quick start
1) Create and invite a separate development bot to your test guild
2) Export env vars, then run:

   python apps/coc-discord-bot-cwl/bot.py --sync

3) Try commands:
- /cwl status
- /cwl schedule
- /cwl leaderboard
- /whois player: <#TAG>   or   /whois player: <player name in your clan>

Notes
- Global command sync can take minutes; prefer setting DISCORD_GUILD_ID for fast guild-only registration.
- This dev bot does NOT modify your database and does NOT overlap ports/processes with your production bot.
