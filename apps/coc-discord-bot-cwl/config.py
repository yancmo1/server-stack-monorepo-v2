import os
import sys

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0")) or None
SUPERCELL_API_TOKEN = os.getenv("SUPERCELL_API_TOKEN")
CLAN_TAG = os.getenv("CLAN_TAG")
SYNC_ON_START = os.getenv("SYNC_ON_START", "false").lower() in ("1","true","yes")

if not DISCORD_BOT_TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN is required")
if not SUPERCELL_API_TOKEN:
    raise RuntimeError("SUPERCELL_API_TOKEN is required")
if not CLAN_TAG:
    raise RuntimeError("CLAN_TAG is required (e.g. #ABC123)")

if __name__ == "__main__":
    # Minimal healthcheck hook: `python config.py --healthcheck`
    if len(sys.argv) > 1 and sys.argv[1] == "--healthcheck":
        # Validate envs are present
        missing = []
        if not DISCORD_BOT_TOKEN:
            missing.append("DISCORD_BOT_TOKEN")
        if not SUPERCELL_API_TOKEN:
            missing.append("SUPERCELL_API_TOKEN")
        if not CLAN_TAG:
            missing.append("CLAN_TAG")
        if missing:
            print("Missing:", ",".join(missing))
            sys.exit(1)
        print("ok")
        sys.exit(0)
