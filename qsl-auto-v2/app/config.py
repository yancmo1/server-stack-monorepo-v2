from __future__ import annotations
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    # Only load .env automatically when running in Docker (compose passes envs anyway)
    _in_docker = Path('/.dockerenv').exists() or os.environ.get('IN_DOCKER') == '1'
    model_config = SettingsConfigDict(
        env_file='.env' if _in_docker else None,
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

    # Feature flags
    dry_run: bool = Field(default=True, alias='DRY_RUN')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')
    chunk_size: int = Field(default=25, alias='CHUNK_SIZE')
    email_rate_limit_per_min: int = Field(default=8, alias='EMAIL_RATE_LIMIT_PER_MIN')

    # Connector
    connector_base_url: str = Field(default='http://localhost:5557', alias='CONNECTOR_BASE_URL')
    connector_token: str = Field(default='please-change-me', alias='CONNECTOR_TOKEN')

    # Paths
    output_dir: Path = Field(default=Path('./output'), alias='OUTPUT_DIR')
    state_db: Path = Field(default=Path('./data/state.sqlite'), alias='STATE_DB')
    google_client_secret_path: Path = Field(default=Path('./secrets/google/credentials.json'), alias='GOOGLE_CLIENT_SECRET_PATH')
    google_token_path: Path = Field(default=Path('./secrets/google/token.pickle'), alias='GOOGLE_TOKEN_PATH')

    # From identity
    from_callsign: str = Field(default='W5XY', alias='FROM_CALLSIGN')
    from_operator_name: str = Field(default='Operator', alias='FROM_OPERATOR_NAME')
    from_email: str = Field(default='noreply@example.com', alias='FROM_EMAIL')

settings = Settings()

def _ensure_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False

# Ensure directories exist with graceful fallbacks for local/dev environments
if not _ensure_dir(settings.output_dir):
    # Fallback to a local writable folder
    fallback_output = Path('./output')
    fallback_output.mkdir(parents=True, exist_ok=True)
    settings.output_dir = fallback_output

if not _ensure_dir(settings.state_db.parent):
    fallback_data = Path('./data')
    fallback_data.mkdir(parents=True, exist_ok=True)
    settings.state_db = fallback_data / settings.state_db.name

if not _ensure_dir(settings.google_token_path.parent):
    fallback_secrets = Path('./secrets/google')
    fallback_secrets.mkdir(parents=True, exist_ok=True)
    settings.google_token_path = fallback_secrets / settings.google_token_path.name
