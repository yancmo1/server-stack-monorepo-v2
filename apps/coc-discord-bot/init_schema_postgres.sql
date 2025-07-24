-- Postgres schema for coc-discord-bot

CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    tag TEXT UNIQUE,
    join_date TIMESTAMP,
    bonus_eligibility BOOLEAN DEFAULT TRUE,
    bonus_count INTEGER DEFAULT 0,
    last_bonus_date TIMESTAMP,
    missed_attacks INTEGER DEFAULT 0,
    notes TEXT,
    role TEXT DEFAULT '',
    active BOOLEAN DEFAULT TRUE,
    cwl_stars INTEGER DEFAULT 0,
    inactive BOOLEAN DEFAULT FALSE,
    location TEXT DEFAULT 'Unknown',
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    favorite_troop TEXT,
    location_updated TIMESTAMP
);

CREATE TABLE IF NOT EXISTS removed_players (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    tag TEXT NOT NULL,
    removed_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS missed_attacks_history (
    id SERIAL PRIMARY KEY,
    player_tag TEXT NOT NULL,
    player_name TEXT NOT NULL,
    war_tag TEXT NOT NULL,
    round_num INTEGER NOT NULL,
    date_processed TIMESTAMP NOT NULL,
    UNIQUE(player_tag, war_tag)
);

CREATE TABLE IF NOT EXISTS war_attacks (
    id SERIAL PRIMARY KEY,
    player_tag TEXT NOT NULL,
    player_name TEXT NOT NULL,
    war_tag TEXT NOT NULL,
    attack_order INTEGER,
    defender_tag TEXT,
    stars INTEGER,
    destruction_percentage DOUBLE PRECISION,
    attack_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bonus_history (
    id SERIAL PRIMARY KEY,
    player_name TEXT NOT NULL,
    player_tag TEXT,
    awarded_date TIMESTAMP NOT NULL,
    awarded_by TEXT NOT NULL,
    bonus_type TEXT DEFAULT 'CWL',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cwl_history (
    id SERIAL PRIMARY KEY,
    season_year INTEGER NOT NULL,
    season_month INTEGER NOT NULL,
    reset_date TIMESTAMP NOT NULL,
    player_name TEXT NOT NULL,
    player_tag TEXT,
    missed_attacks INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_name) REFERENCES players(name) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cwl_stars_history (
    id SERIAL PRIMARY KEY,
    player_name TEXT NOT NULL,
    player_tag TEXT,
    war_date TIMESTAMP NOT NULL,
    war_round INTEGER NOT NULL,
    stars_earned INTEGER NOT NULL,
    total_stars INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_name) REFERENCES players(name) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS discord_coc_links (
    discord_id TEXT PRIMARY KEY,
    coc_name_or_tag TEXT NOT NULL,
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
CREATE INDEX IF NOT EXISTS idx_players_tag ON players(tag);
CREATE INDEX IF NOT EXISTS idx_players_bonus_eligibility ON players(bonus_eligibility);
CREATE INDEX IF NOT EXISTS idx_players_inactive ON players(inactive);
CREATE INDEX IF NOT EXISTS idx_players_location ON players(location);
CREATE INDEX IF NOT EXISTS idx_players_coordinates ON players(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_removed_players_tag ON removed_players(tag);
CREATE INDEX IF NOT EXISTS idx_removed_players_removed_date ON removed_players(removed_date);
CREATE INDEX IF NOT EXISTS idx_missed_attacks_history_player_tag ON missed_attacks_history(player_tag);
CREATE INDEX IF NOT EXISTS idx_missed_attacks_history_war_tag ON missed_attacks_history(war_tag);
CREATE INDEX IF NOT EXISTS idx_war_attacks_player_tag ON war_attacks(player_tag);
CREATE INDEX IF NOT EXISTS idx_war_attacks_war_tag ON war_attacks(war_tag);
CREATE INDEX IF NOT EXISTS idx_bonus_history_player_name ON bonus_history(player_name);
CREATE INDEX IF NOT EXISTS idx_bonus_history_awarded_date ON bonus_history(awarded_date);
CREATE INDEX IF NOT EXISTS idx_cwl_history_player_name ON cwl_history(player_name);
CREATE INDEX IF NOT EXISTS idx_cwl_stars_history_player_name ON cwl_stars_history(player_name);
CREATE INDEX IF NOT EXISTS idx_cwl_stars_history_war_date ON cwl_stars_history(war_date);
CREATE INDEX IF NOT EXISTS idx_discord_links_discord_id ON discord_coc_links(discord_id);
