CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    tag TEXT UNIQUE,
    join_date TEXT,
    bonus_eligibility INTEGER DEFAULT 1,
    bonus_count INTEGER DEFAULT 0,
    last_bonus_date TEXT,
    missed_attacks INTEGER DEFAULT 0,
    notes TEXT,
    role TEXT DEFAULT '',
    active INTEGER DEFAULT 1,
    cwl_stars INTEGER DEFAULT 0,
    inactive INTEGER DEFAULT 0,
    location TEXT DEFAULT 'Unknown',
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    favorite_troop TEXT,
    location_updated TEXT
);

CREATE TABLE IF NOT EXISTS removed_players (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    tag TEXT NOT NULL,
    removed_date TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS missed_attacks_history (
    id SERIAL PRIMARY KEY,
    player_tag TEXT NOT NULL,
    player_name TEXT NOT NULL,
    war_tag TEXT NOT NULL,
    round_num INTEGER NOT NULL,
    date_processed TEXT NOT NULL,
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
    attack_time TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bonus_history (
    id SERIAL PRIMARY KEY,
    player_name TEXT NOT NULL,
    player_tag TEXT,
    awarded_date TEXT NOT NULL,
    awarded_by TEXT NOT NULL,
    bonus_type TEXT DEFAULT 'CWL',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cwl_history (
    id SERIAL PRIMARY KEY,
    season_year INTEGER NOT NULL,
    season_month INTEGER NOT NULL,
    reset_date TEXT NOT NULL,
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
    war_date TEXT NOT NULL,
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
