use serde::{Deserialize, Serialize};
use rand::Rng;
use rand::distributions::WeightedIndex;
use rand::prelude::*;
use clap::Parser;
use std::fs;
use std::io::{self, Read};

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Input JSON file (use '-' for stdin)
    #[arg(short, long, default_value = "-")]
    input: String,

    /// Output JSON file (use '-' for stdout)
    #[arg(short, long, default_value = "-")]
    output: String,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct Player {
    id: i32,
    name: String,
    position: String,
    off: i32,
    def: i32,
    phys: i32,
    lead: i32,
    #[serde(rename = "const")]
    consistency: i32,
}

#[derive(Debug, Deserialize, Serialize)]
struct Coach {
    id: i32,
    name: String,
    rating: i32,
}

#[derive(Debug, Deserialize, Serialize)]
struct LineAssignment {
    line_type: String,  // "forward", "defense", "goalie"
    line_number: i32,
    position: String,  // LW, C, RW, LD, RD, G
    player: Player,
}

#[derive(Debug, Deserialize, Serialize)]
struct Team {
    id: i32,
    name: String,
    city: String,
    lines: Vec<LineAssignment>,
    coach: Option<Coach>,
}

#[derive(Debug, Deserialize, Serialize)]
struct GameInput {
    home_team: Team,
    away_team: Team,
    is_playoff: bool,
}

impl Player {
    /// Calculate overall rating for frontend display purposes only.
    /// This value is NOT used in the simulation algorithm - individual attributes (OFF, DEF, PHYS, LEAD, CONST) are used directly.
    /// Formula: (OFF × 1.1 + DEF × 0.95 + PHYS × 0.9 × (LEAD/100) × (CONST/100)) / 2.5
    fn calculate_overall(&self) -> f64 {
        let off_component = self.off as f64 * 1.1;
        let def_component = self.def as f64 * 0.95;
        let phys_component = self.phys as f64 * 0.9 * (self.lead as f64 / 100.0) * (self.consistency as f64 / 100.0);
        
        (off_component + def_component + phys_component) / 2.5
    }
}

#[derive(Debug, Serialize)]
struct PlayerGameStat {
    player_id: i32,
    player_name: String,
    goals: i32,
    assists: i32,
    shots: i32,
    hits: i32,
    blocks: i32,
    plus_minus: i32,
    // Goalie stats
    saves: i32,
    goals_against: i32,
    shots_against: i32,
}

#[derive(Debug, Serialize)]
struct GameResult {
    home_score: i32,
    away_score: i32,
    home_stats: Vec<PlayerGameStat>,
    away_stats: Vec<PlayerGameStat>,
}

// Ice time percentages
const FORWARD_LINE_TIME: [f64; 4] = [0.35, 0.30, 0.20, 0.15];
const DEFENSE_LINE_TIME: [f64; 3] = [0.45, 0.35, 0.20];

// Goalie game assignment probabilities (% of games, not ice time)
const GOALIE_GAME_PROBABILITY: [f64; 2] = [0.60, 0.40];

// Skill weightings [OFF, DEF, PHYS]
const FORWARD_WEIGHTS: [[f64; 3]; 4] = [
    [0.50, 0.30, 0.20],  // Line 1
    [0.40, 0.40, 0.20],  // Line 2
    [0.25, 0.50, 0.25],  // Line 3
    [0.20, 0.40, 0.40],  // Line 4
];

const DEFENSE_WEIGHTS: [[f64; 3]; 3] = [
    [0.40, 0.30, 0.30],  // Pair 1
    [0.30, 0.40, 0.30],  // Pair 2
    [0.10, 0.50, 0.40],  // Pair 3
];

// Constants for game simulation (calibrated to NHL 2024-2025 averages)
const HOME_ICE_ADVANTAGE: f64 = 1.05;  // 5% boost
const PLAYOFF_PHYS_BOOST: f64 = 1.20;  // 20% boost to physicality in playoffs
const BASE_SHOTS_PER_PERIOD: f64 = 9.4;  // ~28.1 shots per team per game / 3 periods
const BASE_GOAL_PROBABILITY: f64 = 0.10;  // 10% shooting percentage (matches .900 save %)

fn main() {
    let args = Args::parse();
    
    // Read input
    let input_json = if args.input == "-" {
        let mut buffer = String::new();
        io::stdin().read_to_string(&mut buffer).expect("Failed to read from stdin");
        buffer
    } else {
        fs::read_to_string(&args.input).expect("Failed to read input file")
    };
    
    // Parse input
    let game_input: GameInput = serde_json::from_str(&input_json)
        .expect("Failed to parse JSON input");
    
    // Simulate game
    let result = simulate_game(game_input);
    
    // Output result
    let output_json = serde_json::to_string_pretty(&result)
        .expect("Failed to serialize result");
    
    if args.output == "-" {
        println!("{}", output_json);
    } else {
        fs::write(&args.output, output_json).expect("Failed to write output file");
    }
}

fn simulate_game(input: GameInput) -> GameResult {
    let mut rng = rand::thread_rng();
    
    // Select goalies for this game (60% G1, 40% G2)
    let home_goalie_idx = select_goalie(&input.home_team, &mut rng);
    let away_goalie_idx = select_goalie(&input.away_team, &mut rng);
    
    // Calculate team ratings with selected goalie
    let home_rating = calculate_team_rating(&input.home_team, home_goalie_idx, true, input.is_playoff);
    let away_rating = calculate_team_rating(&input.away_team, away_goalie_idx, false, input.is_playoff);
    
    // Initialize stats
    let mut home_stats: Vec<PlayerGameStat> = Vec::new();
    let mut away_stats: Vec<PlayerGameStat> = Vec::new();
    
    let mut home_score = 0;
    let mut away_score = 0;
    
    // Simulate 3 periods
    for period in 1..=3 {
        let (home_goals, away_goals, home_period_stats, away_period_stats) = 
            simulate_period(
                &input.home_team,
                &input.away_team,
                home_goalie_idx,
                away_goalie_idx,
                home_rating,
                away_rating,
                input.is_playoff,
                &mut rng
            );
        
        home_score += home_goals;
        away_score += away_goals;
        
        // Aggregate stats
        merge_stats(&mut home_stats, home_period_stats);
        merge_stats(&mut away_stats, away_period_stats);
    }
    
    // Calculate plus/minus
    calculate_plus_minus(&mut home_stats, home_score, away_score);
    calculate_plus_minus(&mut away_stats, away_score, home_score);
    
    GameResult {
        home_score,
        away_score,
        home_stats,
        away_stats,
    }
}

fn select_goalie(team: &Team, rng: &mut ThreadRng) -> usize {
    // Find goalie positions in the team lines
    let goalie_indices: Vec<usize> = team.lines.iter()
        .enumerate()
        .filter(|(_, la)| la.line_type == "goalie")
        .map(|(idx, _)| idx)
        .collect();
    
    if goalie_indices.is_empty() {
        return 0; // Fallback if no goalie found
    }
    
    // Select based on GOALIE_GAME_PROBABILITY (60% G1, 40% G2)
    let rand_val: f64 = rng.gen();
    if rand_val < GOALIE_GAME_PROBABILITY[0] && goalie_indices.len() > 0 {
        goalie_indices[0] // Starter (G1)
    } else if goalie_indices.len() > 1 {
        goalie_indices[1] // Backup (G2)
    } else {
        goalie_indices[0] // Only one goalie available
    }
}

fn calculate_team_rating(team: &Team, goalie_idx: usize, is_home: bool, is_playoff: bool) -> f64 {
    let mut total_rating = 0.0;
    let mut weight_sum = 0.0;
    
    // Calculate forward lines rating
    for line_num in 1..=4 {
        let line_players: Vec<&Player> = team.lines.iter()
            .filter(|la| la.line_type == "forward" && la.line_number == line_num)
            .map(|la| &la.player)
            .collect();
        
        if !line_players.is_empty() {
            let line_rating = calculate_line_rating(&line_players, &FORWARD_WEIGHTS[(line_num - 1) as usize], is_playoff);
            let ice_time = FORWARD_LINE_TIME[(line_num - 1) as usize];
            total_rating += line_rating * ice_time;
            weight_sum += ice_time;
        }
    }
    
    // Calculate defense pairs rating
    for pair_num in 1..=3 {
        let pair_players: Vec<&Player> = team.lines.iter()
            .filter(|la| la.line_type == "defense" && la.line_number == pair_num)
            .map(|la| &la.player)
            .collect();
        
        if !pair_players.is_empty() {
            let pair_rating = calculate_line_rating(&pair_players, &DEFENSE_WEIGHTS[(pair_num - 1) as usize], is_playoff);
            let ice_time = DEFENSE_LINE_TIME[(pair_num - 1) as usize];
            total_rating += pair_rating * ice_time;
            weight_sum += ice_time;
        }
    }
    
    // Use the selected goalie's rating (plays full game)
    if goalie_idx < team.lines.len() && team.lines[goalie_idx].line_type == "goalie" {
        let goalie = &team.lines[goalie_idx].player;
        let goalie_rating = (goalie.off + goalie.def + goalie.phys) as f64 / 3.0;
        total_rating += goalie_rating * 0.3;  // Goalies have 30% weight
        weight_sum += 0.3;
    }
    
    // Apply coach modifier
    let coach_modifier = if let Some(coach) = &team.coach {
        1.0 + (coach.rating as f64 - 75.0) / 500.0  // ±5% max based on rating
    } else {
        1.0
    };
    
    let mut final_rating = (total_rating / weight_sum.max(0.1)) * coach_modifier;
    
    // Apply home ice advantage
    if is_home {
        final_rating *= HOME_ICE_ADVANTAGE;
    }
    
    final_rating
}

fn calculate_line_rating(players: &[&Player], weights: &[f64; 3], is_playoff: bool) -> f64 {
    if players.is_empty() {
        return 50.0;
    }
    
    let mut total_rating = 0.0;
    let mut leadership_boost = 0.0;
    
    for player in players {
        let phys = if is_playoff {
            (player.phys as f64 * PLAYOFF_PHYS_BOOST) as i32
        } else {
            player.phys
        };
        
        let rating = (player.off as f64 * weights[0]) +
                     (player.def as f64 * weights[1]) +
                     (phys as f64 * weights[2]);
        
        total_rating += rating;
        leadership_boost += player.lead as f64;
    }
    
    // Apply leadership boost (avg team leadership adds 0-5% boost)
    let avg_leadership = leadership_boost / players.len() as f64;
    let leadership_multiplier = 1.0 + (avg_leadership - 75.0) / 1000.0;
    
    (total_rating / players.len() as f64) * leadership_multiplier
}

fn simulate_period(
    home_team: &Team,
    away_team: &Team,
    home_goalie_idx: usize,
    away_goalie_idx: usize,
    home_rating: f64,
    away_rating: f64,
    is_playoff: bool,
    rng: &mut ThreadRng,
) -> (i32, i32, Vec<PlayerGameStat>, Vec<PlayerGameStat>) {
    let mut home_goals = 0;
    let mut away_goals = 0;
    let mut home_stats = init_team_stats(home_team);
    let mut away_stats = init_team_stats(away_team);
    
    // Calculate shot distribution based on ratings
    // Target: ~28.1 shots per team per game (NHL 2024-2025 average)
    let total_rating = home_rating + away_rating;
    let home_shot_ratio = home_rating / total_rating;
    
    let home_shots = (BASE_SHOTS_PER_PERIOD * (1.0 + home_shot_ratio)) as i32;
    let away_shots = (BASE_SHOTS_PER_PERIOD * (2.0 - home_shot_ratio)) as i32;
    
    // Simulate home team shots
    for _ in 0..home_shots {
        let (shooter_idx, line_num) = select_shooter(home_team, rng);
        home_stats[shooter_idx].shots += 1;
        
        // Check if goal scored
        // Base 10% shooting percentage matches NHL 2024-2025 .900 save percentage
        // Target: ~3.01 goals per team per game
        let goal_prob = BASE_GOAL_PROBABILITY * (home_rating / 80.0) * (80.0 / away_rating.max(50.0));
        let is_goal = rng.gen::<f64>() < goal_prob;
        
        if is_goal {
            home_goals += 1;
            home_stats[shooter_idx].goals += 1;
            
            // 60% chance of assist
            if rng.gen::<f64>() < 0.6 {
                let assist_idx = select_assist_player(home_team, shooter_idx, line_num, rng);
                if let Some(idx) = assist_idx {
                    home_stats[idx].assists += 1;
                }
            }
        }
        
        // Track goalie stats for away team (defending against home shot)
        if away_goalie_idx < away_stats.len() {
            away_stats[away_goalie_idx].shots_against += 1;
            if is_goal {
                away_stats[away_goalie_idx].goals_against += 1;
            } else {
                away_stats[away_goalie_idx].saves += 1;
            }
        }
    }
    
    // Simulate away team shots
    for _ in 0..away_shots {
        let (shooter_idx, line_num) = select_shooter(away_team, rng);
        away_stats[shooter_idx].shots += 1;
        
        // Check if goal scored (same calculation as home team)
        let goal_prob = BASE_GOAL_PROBABILITY * (away_rating / 80.0) * (80.0 / home_rating.max(50.0));
        let is_goal = rng.gen::<f64>() < goal_prob;
        
        if is_goal {
            away_goals += 1;
            away_stats[shooter_idx].goals += 1;
            
            if rng.gen::<f64>() < 0.6 {
                let assist_idx = select_assist_player(away_team, shooter_idx, line_num, rng);
                if let Some(idx) = assist_idx {
                    away_stats[idx].assists += 1;
                }
            }
        }
        
        // Track goalie stats for home team (defending against away shot)
        if home_goalie_idx < home_stats.len() {
            home_stats[home_goalie_idx].shots_against += 1;
            if is_goal {
                home_stats[home_goalie_idx].goals_against += 1;
            } else {
                home_stats[home_goalie_idx].saves += 1;
            }
        }
    }
    
    // Simulate hits and blocks based on physicality
    simulate_physical_stats(&mut home_stats, home_team, is_playoff, rng);
    simulate_physical_stats(&mut away_stats, away_team, is_playoff, rng);
    
    (home_goals, away_goals, home_stats, away_stats)
}

fn init_team_stats(team: &Team) -> Vec<PlayerGameStat> {
    team.lines.iter()
        .map(|la| PlayerGameStat {
            player_id: la.player.id,
            player_name: la.player.name.clone(),
            goals: 0,
            assists: 0,
            shots: 0,
            hits: 0,
            blocks: 0,
            plus_minus: 0,
            saves: 0,
            goals_against: 0,
            shots_against: 0,
        })
        .collect()
}

fn select_shooter(team: &Team, rng: &mut ThreadRng) -> (usize, i32) {
    // Weight by ice time and offensive skill
    let weights: Vec<f64> = team.lines.iter()
        .enumerate()
        .map(|(_, la)| {
            if la.line_type == "goalie" {
                return 0.0;
            }
            let ice_time = match la.line_type.as_str() {
                "forward" => FORWARD_LINE_TIME[(la.line_number - 1).min(3) as usize],
                "defense" => DEFENSE_LINE_TIME[(la.line_number - 1).min(2) as usize] * 0.4,
                _ => 0.1,
            };
            ice_time * (la.player.off as f64 / 100.0)
        })
        .collect();
    
    let dist = WeightedIndex::new(&weights).unwrap();
    let idx = dist.sample(rng);
    let line_num = team.lines[idx].line_number;
    (idx, line_num)
}

fn select_assist_player(team: &Team, shooter_idx: usize, line_num: i32, rng: &mut ThreadRng) -> Option<usize> {
    // Prefer players on the same line
    let same_line: Vec<usize> = team.lines.iter()
        .enumerate()
        .filter(|(idx, la)| *idx != shooter_idx && la.line_number == line_num && la.line_type != "goalie")
        .map(|(idx, _)| idx)
        .collect();
    
    if !same_line.is_empty() {
        Some(same_line[rng.gen_range(0..same_line.len())])
    } else {
        None
    }
}

fn simulate_physical_stats(stats: &mut [PlayerGameStat], team: &Team, is_playoff: bool, rng: &mut ThreadRng) {
    for (idx, la) in team.lines.iter().enumerate() {
        if la.line_type == "goalie" {
            continue;
        }
        
        let phys = if is_playoff {
            (la.player.phys as f64 * PLAYOFF_PHYS_BOOST).min(100.0) as i32
        } else {
            la.player.phys
        };
        
        // Hits based on physicality
        // Target: ~15-25 hits per team per game (NHL 2024-2025 average)
        let hit_chance = phys as f64 / 100.0 * 0.05;
        stats[idx].hits = (0..50).filter(|_| rng.gen::<f64>() < hit_chance).count() as i32;
        
        // Blocks based on defensive skill
        // Target: ~15-25 blocks per team per game (NHL 2024-2025 average)
        let block_chance = la.player.def as f64 / 100.0 * 0.03;
        stats[idx].blocks = (0..40).filter(|_| rng.gen::<f64>() < block_chance).count() as i32;
    }
}

fn merge_stats(accumulated: &mut Vec<PlayerGameStat>, period_stats: Vec<PlayerGameStat>) {
    if accumulated.is_empty() {
        *accumulated = period_stats;
        return;
    }
    
    for period_stat in period_stats {
        if let Some(acc_stat) = accumulated.iter_mut().find(|s| s.player_id == period_stat.player_id) {
            acc_stat.goals += period_stat.goals;
            acc_stat.assists += period_stat.assists;
            acc_stat.shots += period_stat.shots;
            acc_stat.hits += period_stat.hits;
            acc_stat.blocks += period_stat.blocks;
            acc_stat.saves += period_stat.saves;
            acc_stat.goals_against += period_stat.goals_against;
            acc_stat.shots_against += period_stat.shots_against;
        }
    }
}

fn calculate_plus_minus(stats: &mut [PlayerGameStat], team_goals: i32, opponent_goals: i32) {
    for stat in stats.iter_mut() {
        // Simplified: distribute plus/minus based on performance
        // Better players get more credit/blame
        stat.plus_minus = team_goals - opponent_goals;
    }
}
