-- Legend Hockey League (LHL) Database Schema
-- PostgreSQL Database Schema Documentation
-- Generated from SQLAlchemy models

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SIMULATIONS TABLE
-- ============================================
CREATE TABLE simulations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100),  -- Optional name for the simulation
    year_length INTEGER NOT NULL,  -- 20-25 years
    num_teams INTEGER NOT NULL,  -- 4, 6, 8, 10, 12
    current_season INTEGER DEFAULT 1,
    current_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',  -- draft, season, playoffs, completed
    draft_pick INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,  -- False if user quit/left the simulation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_simulations_user_id ON simulations(user_id);
CREATE INDEX idx_simulations_status ON simulations(status);
CREATE INDEX idx_simulations_is_active ON simulations(is_active);

-- ============================================
-- PLAYERS TABLE
-- ============================================
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    position VARCHAR(3) NOT NULL,  -- C, LW, RW, D, G
    off INTEGER NOT NULL,  -- Offense (0-100)
    def INTEGER NOT NULL,  -- Defense (0-100)
    phys INTEGER NOT NULL,  -- Physicality (0-100)
    lead INTEGER NOT NULL,  -- Leadership (0-100)
    const INTEGER NOT NULL,  -- Consistency (0-100)
    is_goalie BOOLEAN DEFAULT FALSE,
    player_type VARCHAR(50),  -- Player classification type
    era VARCHAR(50)  -- Era the player represents
);

CREATE INDEX idx_players_position ON players(position);
CREATE INDEX idx_players_is_goalie ON players(is_goalie);

-- ============================================
-- COACHES TABLE
-- ============================================
CREATE TABLE coaches (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    rating INTEGER NOT NULL,  -- Overall coaching rating (0-100)
    coach_type VARCHAR(50),  -- Coach classification type
    era VARCHAR(50)  -- Era the coach represents
);

-- ============================================
-- TEAMS TABLE
-- ============================================
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    simulation_id INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,  -- MTL, BOS, etc
    city VARCHAR(100) NOT NULL,  -- Montreal, Boston, etc
    conference VARCHAR(10) NOT NULL,  -- Eastern, Western
    user_controlled BOOLEAN DEFAULT FALSE,
    coach_id INTEGER REFERENCES coaches(id)
);

CREATE INDEX idx_teams_simulation_id ON teams(simulation_id);
CREATE INDEX idx_teams_user_controlled ON teams(user_controlled);
CREATE INDEX idx_teams_conference ON teams(conference);

-- ============================================
-- ROSTERS TABLE (Team-Player associations)
-- ============================================
CREATE TABLE rosters (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id),
    simulation_id INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    season_acquired INTEGER DEFAULT 1
);

CREATE INDEX idx_rosters_team_id ON rosters(team_id);
CREATE INDEX idx_rosters_player_id ON rosters(player_id);
CREATE INDEX idx_rosters_simulation_id ON rosters(simulation_id);
CREATE UNIQUE INDEX idx_rosters_unique ON rosters(team_id, player_id, simulation_id);

-- ============================================
-- LINE ASSIGNMENTS TABLE
-- ============================================
CREATE TABLE line_assignments (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id),
    line_type VARCHAR(10) NOT NULL,  -- forward, defense, goalie
    line_number INTEGER NOT NULL,  -- 1-4 for forwards, 1-3 for defense, 1-2 for goalies
    position VARCHAR(3) NOT NULL  -- LW, C, RW, LD, RD, G
);

CREATE INDEX idx_line_assignments_team_id ON line_assignments(team_id);
CREATE INDEX idx_line_assignments_player_id ON line_assignments(player_id);
CREATE INDEX idx_line_assignments_line_type ON line_assignments(line_type);

-- ============================================
-- GAMES TABLE
-- ============================================
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    simulation_id INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    season INTEGER NOT NULL,
    date DATE NOT NULL,
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    home_score INTEGER,
    away_score INTEGER,
    is_playoff BOOLEAN DEFAULT FALSE,
    playoff_round INTEGER,  -- 1-4
    simulated BOOLEAN DEFAULT FALSE,
    series_id INTEGER REFERENCES playoff_series(id)  -- Reference to playoff series
);

CREATE INDEX idx_games_simulation_id ON games(simulation_id);
CREATE INDEX idx_games_season ON games(season);
CREATE INDEX idx_games_date ON games(date);
CREATE INDEX idx_games_home_team_id ON games(home_team_id);
CREATE INDEX idx_games_away_team_id ON games(away_team_id);
CREATE INDEX idx_games_is_playoff ON games(is_playoff);

-- ============================================
-- PLAYER STATS TABLE (Per-game statistics)
-- ============================================
CREATE TABLE player_stats (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    
    -- Skater stats
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    shots INTEGER DEFAULT 0,
    hits INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    plus_minus INTEGER DEFAULT 0,
    
    -- Goalie stats
    saves INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    shots_against INTEGER DEFAULT 0
);

CREATE INDEX idx_player_stats_game_id ON player_stats(game_id);
CREATE INDEX idx_player_stats_player_id ON player_stats(player_id);
CREATE INDEX idx_player_stats_team_id ON player_stats(team_id);
CREATE UNIQUE INDEX idx_player_stats_unique ON player_stats(game_id, player_id);

-- ============================================
-- STANDINGS TABLE (Season standings)
-- ============================================
CREATE TABLE standings (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    simulation_id INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    season INTEGER NOT NULL,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    ot_losses INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0
);

CREATE INDEX idx_standings_team_id ON standings(team_id);
CREATE INDEX idx_standings_simulation_id ON standings(simulation_id);
CREATE INDEX idx_standings_season ON standings(season);
CREATE UNIQUE INDEX idx_standings_unique ON standings(team_id, simulation_id, season);

-- ============================================
-- PLAYOFF SERIES TABLE
-- ============================================
CREATE TABLE playoff_series (
    id SERIAL PRIMARY KEY,
    simulation_id INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    season INTEGER NOT NULL,
    round INTEGER NOT NULL,  -- 1-4 (Quarterfinals, Semifinals, Finals, Stanley Cup)
    higher_seed_team_id INTEGER NOT NULL REFERENCES teams(id),
    lower_seed_team_id INTEGER NOT NULL REFERENCES teams(id),
    higher_seed_wins INTEGER DEFAULT 0,
    lower_seed_wins INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'in_progress',  -- in_progress, completed
    winner_team_id INTEGER REFERENCES teams(id),
    next_game_number INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_playoff_series_simulation_id ON playoff_series(simulation_id);
CREATE INDEX idx_playoff_series_season ON playoff_series(season);
CREATE INDEX idx_playoff_series_round ON playoff_series(round);
CREATE INDEX idx_playoff_series_status ON playoff_series(status);

-- ============================================
-- TROPHIES TABLE
-- ============================================
CREATE TABLE trophies (
    id SERIAL PRIMARY KEY,
    simulation_id INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    season INTEGER NOT NULL,
    trophy_name VARCHAR(100) NOT NULL,
    trophy_type VARCHAR(20) NOT NULL,  -- e.g., art_ross, hart, conn_smythe, stanley_cup
    player_id INTEGER REFERENCES players(id),  -- For player awards
    team_id INTEGER REFERENCES teams(id),  -- For team awards
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trophies_simulation_id ON trophies(simulation_id);
CREATE INDEX idx_trophies_season ON trophies(season);
CREATE INDEX idx_trophies_trophy_type ON trophies(trophy_type);
CREATE INDEX idx_trophies_player_id ON trophies(player_id);
CREATE INDEX idx_trophies_team_id ON trophies(team_id);

-- ============================================
-- NOTES
-- ============================================
-- All timestamps use CURRENT_TIMESTAMP by default
-- Foreign keys use ON DELETE CASCADE where appropriate
-- Indexes are created for commonly queried columns
-- Unique constraints prevent duplicate entries where logical
