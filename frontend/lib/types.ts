export interface User {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
}

export interface Player {
  id: number;
  name: string;
  position: string;
  player_type?: string;
  era?: string;
  off: number;
  def: number;
  phys: number;
  lead: number;
  const: number;
  is_goalie: boolean;
  overall?: number;
}

export interface Coach {
  id: number;
  name: string;
  coach_type?: string;
  era?: string;
  rating: number;
}

export interface Team {
  id: number;
  name: string;
  city: string;
  conference: string;
  user_controlled: boolean;
}

export interface Simulation {
  id: number;
  user_id: number;
  name?: string | null;
  year_length: number;
  num_teams: number;
  current_date: string;
  current_season: number;
  status: string;
  created_at?: string;
  draft_pick?: number;
  is_active?: boolean;
}

export interface GameResult {
  id: number;
  home_team: Team;
  away_team: Team;
  home_score: number;
  away_score: number;
  date: string;
}

export interface PlayoffGame {
  id: number;
  home_team_id: number;
  away_team_id: number;
  home_score: number | null;
  away_score: number | null;
  date: string | null;
}

export interface PlayoffSeries {
  id: number;
  round: number;
  higher_seed_team_id: number;
  lower_seed_team_id: number;
  higher_seed_wins: number;
  lower_seed_wins: number;
  status: string;
  winner_team_id: number | null;
  next_game_number: number;
  higher_seed_team: Team | null;
  lower_seed_team: Team | null;
  last_game: PlayoffGame | null;
}

export interface PlayoffBracket {
  rounds: Record<string, PlayoffSeries[]>;
  season: number;
  status: string;
}

export interface PlayerStats {
  player_id: number;
  player_name: string;
  player_overall?: number;
  team_name?: string;
  position: string;
  games_played: number;
  goals: number;
  assists: number;
  points: number;
  plus_minus: number;
  hits: number;
  blocks: number;
  shots: number;
  // Goalie stats
  saves?: number;
  goals_against?: number;
  shots_against?: number;
  save_percentage?: number | null;
  goals_against_average?: number | null;
  wins?: number | null;
}

export interface Standing {
  team_id: number;
  team_name: string;
  wins: number;
  losses: number;
  ot_losses: number;
  points: number;
  goals_for: number;
  goals_against: number;
}
