import os
import platform

# All secrets are now managed via CI/CD environment variables only.
# No .env files or dotenv loading is used in any environment.

def safe_int_env(varname, default=None):
    val = os.getenv(varname)
    if val is None or val.strip() == "":
        if default is not None:
            return default
        raise ValueError(f"{varname} not found in environment")
    try:
        return int(val)
    except Exception:
        raise ValueError(f"{varname} must be an integer, got: '{val}'")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SUPERCELL_API_TOKEN = os.getenv("SUPERCELL_API_TOKEN")
if SUPERCELL_API_TOKEN:
    print(f"[CONFIG] SUPERCELL_API_TOKEN loaded: {SUPERCELL_API_TOKEN[:4]}...{SUPERCELL_API_TOKEN[-4:]} (length: {len(SUPERCELL_API_TOKEN)})")
else:
    print("[CONFIG] SUPERCELL_API_TOKEN not set!")
SUPERCELL_API_TOKEN_DEV = os.getenv("SUPERCELL_API_TOKEN_DEV")  # Development API token for different IP
CLAN_TAG = os.getenv("CLAN_TAG")
GUILD_ID = safe_int_env("DISCORD_GUILD_ID")
print(f"[CONFIG] ADMIN_DISCORD_ID raw value: {os.getenv('ADMIN_DISCORD_ID')}")
ADMIN_DISCORD_ID = safe_int_env("ADMIN_DISCORD_ID", None)
ADMIN_ROLE_ID = 552155579833909251
LEADER_ROLE_ID = 1378343994337267713
CO_LEADER_ROLE_ID = 439441365286518794
ELDER_ROLE_ID = 1378202569561866311
MEMBER_ROLE_ID = 1378202569561866311

# Add your CWL-Rewards channel ID here for bonus notifications
CWL_REWARDS_CHANNEL_ID = 553752047309160454  # CWL rewards channel

# Webhook URLs for notifications (optional - configure via /configure_webhook command)
# These can also be set via environment variables
WEBHOOK_URLS = {
    'member_join': os.getenv("WEBHOOK_MEMBER_JOIN"),
    'bonus_distribution': os.getenv("WEBHOOK_BONUS_DISTRIBUTION"),
    'clan_stats': os.getenv("WEBHOOK_CLAN_STATS"),
    'bot_health': os.getenv("WEBHOOK_BOT_HEALTH"),
    'war_alerts': os.getenv("WEBHOOK_WAR_ALERTS"),
    'general': os.getenv("WEBHOOK_GENERAL")
}

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "postgres")  # 'postgres' or 'sqlite'
POSTGRES_DB = os.getenv("POSTGRES_DB", "cocstack")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cocuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "yourpassword")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

# Debugging output for database configuration
print(f"[CONFIG DEBUG] POSTGRES_DB: {POSTGRES_DB}")

# Determine which database to use based on environment
is_docker = os.path.exists("/.dockerenv")  # Docker containers have this file

# Get environment mode from environment variable
env_mode = os.getenv("BOT_ENV", "development")
is_development = env_mode == "development"
is_production = env_mode == "production"

# Default to production database (safer for Pi deployments)
if DB_TYPE == "postgres":
    DB_PATH = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    print(f"[CONFIG] Using PostgreSQL database: {DB_PATH}")
else:
    if is_docker:
        # Docker environment - use different databases for dev/prod
        if is_development:
            DB_PATH = "/app/cwl_data_dev.db"  # Safe development database
            print(f"[CONFIG] Docker DEVELOPMENT environment detected, using database: {DB_PATH}")
        else:
            DB_PATH = "/app/cwl_data.db"  # Production database
            print(f"[CONFIG] Docker PRODUCTION environment detected, using database: {DB_PATH}")
    elif is_development:
        # Use local development database
        DB_PATH = "cwl_data.db"  # Use the local database file
        print(f"[CONFIG] Using development database: {DB_PATH}")
    elif is_production:
        DB_PATH = "/app/cwl_data.db"  # Production database
        print(f"[CONFIG] Using production database: {DB_PATH}")
    else:
        # Default to production database for safety
        DB_PATH = "/app/cwl_data.db"
        print(f"[CONFIG] No environment flag detected, defaulting to production database: {DB_PATH}")
        is_production = True

# Environment mode flag
DEV_MODE = is_development

# Function to get the appropriate API token based on environment
def get_api_token():
    """Get the appropriate Clash of Clans API token based on environment"""
    if DEV_MODE and SUPERCELL_API_TOKEN_DEV:
        print(f"[CONFIG] Using development API token for IP-restricted development environment")
        return SUPERCELL_API_TOKEN_DEV
    else:
        print(f"[CONFIG] Using production API token")
        return SUPERCELL_API_TOKEN

if not CLAN_TAG:
    raise ValueError("CLAN_TAG not found in environment")
if not SUPERCELL_API_TOKEN:
    raise ValueError("SUPERCELL_API_TOKEN not found in environment")
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN not found in environment")
if not GUILD_ID:
    raise ValueError("DISCORD_GUILD_ID not found in environment")
if not LEADER_ROLE_ID:
    raise ValueError("LEADER_ROLE_ID not found in environment")
# Ensure the CLAN_TAG is formatted correctly
# Map clan roles to Discord role names (customize as needed)
DISCORD_ROLE_NAMES = {
    "Admin": "Admin",
    "Leader": "Leader",
    "Co-Leader": "Co-Leader",
    "Elder": "Elder",
    "Member": "Member"
}

print(f"[CONFIG DEBUG] Current working directory: {os.getcwd()}")
print(f"[CONFIG DEBUG] CLAN_TAG loaded as: {CLAN_TAG}")

# Custom check: allow Leader role OR admin
async def is_leader_or_admin(interaction):
    # Only works in guilds
    if not interaction.guild:
        return False
    member = interaction.guild.get_member(interaction.user.id)
    if not member:
        return False
    leader_role_id = LEADER_ROLE_ID
    if any(role.id == leader_role_id for role in member.roles):
        return True
    if member.guild_permissions.administrator:
        return True
    return False

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
