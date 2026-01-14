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
  off: number;
  def: number;
  phys: number;
  lead: number;
  const: number;
  is_goalie: boolean;
}

export interface Coach {
  id: number;
  name: string;
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
  year_length: number;
  num_teams: number;
  current_date: string;
  current_season: number;
  status: string;
}

export interface GameResult {
  id: number;
  home_team: Team;
  away_team: Team;
  home_score: number;
  away_score: number;
  date: string;
}

export interface PlayerStats {
  player_id: number;
  player_name: string;
  team_name: string;
  games_played: number;
  goals: number;
  assists: number;
  points: number;
  plus_minus: number;
  hits: number;
  blocks: number;
  shots: number;
}

export interface Standing {
  team_id: number;
  team_name: string;
  wins: number;
  losses: number;
  points: number;
  goals_for: number;
  goals_against: number;
}
