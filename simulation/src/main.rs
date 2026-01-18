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
    #[serde(default)]
    player_type: String,
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
    #[serde(default)]
    coach_type: String,
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
    #[serde(default = "default_play_style")]
    play_style: String,
}

fn default_play_style() -> String {
    "possession".to_string()
}

#[derive(Debug, Deserialize, Serialize)]
struct GameInput {
    home_team: Team,
    away_team: Team,
    is_playoff: bool,
}

#[derive(Debug, Clone, Copy)]
enum ShotQuality {
    HighDanger,   // xG ~0.16 (slot, odd-man rush, rebound)
    MediumDanger, // xG ~0.065 (between circles, point shot screen)
    LowDanger,    // xG ~0.024 (perimeter, point shot no screen)
}

impl ShotQuality {
    fn base_xg(&self) -> f64 {
        // Reduced by 20% total from original for realistic ~2.6 goals/game
        match self {
            ShotQuality::HighDanger => 0.16,
            ShotQuality::MediumDanger => 0.065,
            ShotQuality::LowDanger => 0.024,
        }
    }
}

#[derive(Debug, Clone)]
struct PlayStyleModifiers {
    shot_volume: f64,
    high_danger_chance: f64,
    turnover_rate: f64,
    odd_man_rush: f64,
    physical_bonus: f64,
    rebound_goals: f64,
}

impl Default for PlayStyleModifiers {
    fn default() -> Self {
        PlayStyleModifiers {
            shot_volume: 1.0,
            high_danger_chance: 1.0,
            turnover_rate: 1.0,
            odd_man_rush: 1.0,
            physical_bonus: 1.0,
            rebound_goals: 1.0,
        }
    }
}

fn get_style_modifiers(style: &str) -> PlayStyleModifiers {
    match style.to_lowercase().as_str() {
        "trap" => PlayStyleModifiers {
            shot_volume: 0.85,
            high_danger_chance: 0.90,
            turnover_rate: 1.20,
            odd_man_rush: 0.80,
            physical_bonus: 1.0,
            rebound_goals: 0.90,
        },
        "possession" => PlayStyleModifiers {
            shot_volume: 0.95,
            high_danger_chance: 1.25,
            turnover_rate: 0.80,
            odd_man_rush: 0.90,
            physical_bonus: 0.90,
            rebound_goals: 1.0,
        },
        "dump_chase" => PlayStyleModifiers {
            shot_volume: 1.10,
            high_danger_chance: 0.90,
            turnover_rate: 1.0,
            odd_man_rush: 0.85,
            physical_bonus: 1.40,
            rebound_goals: 1.25,
        },
        "rush" => PlayStyleModifiers {
            shot_volume: 1.05,
            high_danger_chance: 1.15,
            turnover_rate: 1.10,
            odd_man_rush: 1.35,
            physical_bonus: 0.85,
            rebound_goals: 0.95,
        },
        "shoot_crash" => PlayStyleModifiers {
            shot_volume: 1.25,
            high_danger_chance: 1.0,
            turnover_rate: 1.05,
            odd_man_rush: 0.90,
            physical_bonus: 1.20,
            rebound_goals: 1.20,
        },
        _ => PlayStyleModifiers::default(),
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
    time_on_ice: i32,  // in seconds
    takeaways: i32,
    giveaways: i32,
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
    went_to_overtime: bool,
    went_to_shootout: bool,
}

// Ice time percentages (in seconds for a 60-minute game = 3600 seconds)
const GAME_LENGTH_SECONDS: i32 = 3600;
const FORWARD_LINE_TIME: [f64; 4] = [0.35, 0.30, 0.20, 0.15];
const DEFENSE_LINE_TIME: [f64; 3] = [0.45, 0.35, 0.20];

// Goalie game assignment probabilities
const GOALIE_GAME_PROBABILITY: [f64; 2] = [0.60, 0.40];

// Constants for game simulation (calibrated to NHL 2024-2025 averages)
const HOME_ICE_ADVANTAGE: f64 = 1.05;
const PLAYOFF_PHYS_BOOST: f64 = 1.20;
const BASE_PLAYS_PER_PERIOD: i32 = 50;  // ~50 plays per period (calibrated for ~3 goals/team/game)
const OT_PLAYS: i32 = 10;  // Fewer plays in 5-min OT
const SHOT_ATTEMPT_RATE: f64 = 0.25;  // 25% of plays result in shot attempt

// ============ TEAM ATTRIBUTE CALCULATIONS ============

/// Calculate average DEF rating of a team's skaters (weighted by ice time)
fn calculate_team_defense_rating(team: &Team) -> f64 {
    let mut total_def = 0.0;
    let mut total_weight = 0.0;
    
    for la in &team.lines {
        if la.line_type == "goalie" {
            continue;
        }
        
        let ice_time = match la.line_type.as_str() {
            "forward" => FORWARD_LINE_TIME[(la.line_number - 1).min(3) as usize],
            "defense" => DEFENSE_LINE_TIME[(la.line_number - 1).min(2) as usize],
            _ => 0.1,
        };
        
        // Defensive player types provide extra suppression
        let type_bonus = get_player_type_defense_bonus(&la.player.player_type);
        
        total_def += la.player.def as f64 * ice_time * type_bonus;
        total_weight += ice_time;
    }
    
    if total_weight > 0.0 {
        total_def / total_weight
    } else {
        75.0  // Default
    }
}

/// Get defensive bonus for player types
/// Valid types: Power Forward, Playmaker, Offensive, Two-Way, Sniper, Power Defense, Gamer, Defensive
fn get_player_type_defense_bonus(player_type: &str) -> f64 {
    match player_type.to_lowercase().as_str() {
        "defensive" => 1.15,       // +15% defensive impact
        "power defense" => 1.12,
        "two-way" | "two way" => 1.08,
        "gamer" => 1.05,           // Clutch players play smart defense
        "power forward" => 1.0,
        "offensive" => 0.90,       // Offensive D less defensive
        "playmaker" => 0.92,
        "sniper" => 0.88,
        _ => 1.0,
    }
}

/// Calculate team intimidation factor based on PHYS (reduces opponent shooting)
fn calculate_team_intimidation(team: &Team, is_playoff: bool) -> f64 {
    let mut total_phys = 0.0;
    let mut total_weight = 0.0;
    
    for la in &team.lines {
        if la.line_type == "goalie" {
            continue;
        }
        
        let ice_time = match la.line_type.as_str() {
            "forward" => FORWARD_LINE_TIME[(la.line_number - 1).min(3) as usize],
            "defense" => DEFENSE_LINE_TIME[(la.line_number - 1).min(2) as usize],
            _ => 0.1,
        };
        
        // Physical player types contribute more to intimidation
        let type_bonus = get_player_type_intimidation_bonus(&la.player.player_type);
        
        let phys = if is_playoff {
            (la.player.phys as f64 * PLAYOFF_PHYS_BOOST).min(100.0)
        } else {
            la.player.phys as f64
        };
        
        total_phys += phys * ice_time * type_bonus;
        total_weight += ice_time;
    }
    
    let avg_phys = if total_weight > 0.0 {
        total_phys / total_weight
    } else {
        75.0
    };
    
    // Intimidation factor: 90 PHYS avg = ~10% reduction in opponent goals
    ((avg_phys - 75.0) / 150.0).max(0.0)
}

/// Get intimidation bonus for player types
/// Valid types: Power Forward, Playmaker, Offensive, Two-Way, Sniper, Power Defense, Gamer, Defensive
fn get_player_type_intimidation_bonus(player_type: &str) -> f64 {
    match player_type.to_lowercase().as_str() {
        "power forward" => 1.20,   // Physical presence
        "power defense" => 1.18,
        "defensive" => 1.10,
        "gamer" => 1.05,           // Compete level
        "two-way" | "two way" => 1.0,
        "offensive" => 0.85,       // Less physical
        "playmaker" => 0.80,
        "sniper" => 0.75,          // Not intimidating
        _ => 1.0,
    }
}

/// Calculate leadership bonus for a team (affects clutch and chemistry)
fn calculate_team_leadership(team: &Team, is_playoff: bool, is_clutch: bool) -> f64 {
    // Find highest leadership on team
    let max_lead = team.lines.iter()
        .filter(|la| la.line_type != "goalie")
        .map(|la| la.player.lead)
        .max()
        .unwrap_or(75);
    
    // Calculate average leadership (weighted by ice time)
    let mut total_lead = 0.0;
    let mut total_weight = 0.0;
    
    for la in &team.lines {
        if la.line_type == "goalie" {
            continue;
        }
        
        let ice_time = match la.line_type.as_str() {
            "forward" => FORWARD_LINE_TIME[(la.line_number - 1).min(3) as usize],
            "defense" => DEFENSE_LINE_TIME[(la.line_number - 1).min(2) as usize],
            _ => 0.1,
        };
        
        total_lead += la.player.lead as f64 * ice_time;
        total_weight += ice_time;
    }
    
    let avg_lead = if total_weight > 0.0 {
        total_lead / total_weight
    } else {
        75.0
    };
    
    let mut bonus = 1.0;
    
    // Chemistry bonus - LINEAR based on max leadership (scales from 70-100)
    // 70 LEAD = no bonus, 85 LEAD = +2.5%, 100 LEAD = +5%
    let chemistry = (max_lead as f64 - 70.0) / 600.0;  // Linear 0 to 5%
    bonus *= 1.0 + chemistry.max(0.0);
    
    // Playoff intensity bonus - LINEAR based on average leadership
    // 75 avg LEAD = no bonus, 85 avg LEAD = +2%, 95 avg LEAD = +4%
    if is_playoff {
        let playoff_bonus = (avg_lead - 75.0) / 500.0;  // Linear
        bonus *= 1.0 + playoff_bonus.max(0.0);
    }
    
    // Clutch factor (3rd period, OT, close games) - LINEAR
    // 70 LEAD = no clutch bonus, 90 LEAD = +4%, 100 LEAD = +6%
    if is_clutch {
        let clutch_bonus = (max_lead as f64 - 70.0) / 500.0;
        bonus *= 1.0 + clutch_bonus.max(0.0);
    }
    
    // Low leadership can hurt slightly (below 70 avg = penalty)
    let leadership_penalty = (70.0 - avg_lead).max(0.0) / 200.0;  // Max -5% penalty
    bonus *= 1.0 - leadership_penalty;
    
    bonus.max(0.90)  // Floor at 90%
}

/// Calculate net-front presence bonus for rebound goals
fn calculate_netfront_presence(team: &Team) -> f64 {
    let mut presence = 1.0;
    
    for la in &team.lines {
        if la.line_type == "goalie" {
            continue;
        }
        
        let ice_time = match la.line_type.as_str() {
            "forward" => FORWARD_LINE_TIME[(la.line_number - 1).min(3) as usize],
            "defense" => DEFENSE_LINE_TIME[(la.line_number - 1).min(2) as usize] * 0.3,
            _ => 0.0,
        };
        
        // Power forwards and physical players improve rebound chances
        let type_bonus = match la.player.player_type.to_lowercase().as_str() {
            "power forward" => 0.20,  // +20% when on ice (net-front presence)
            "power defense" => 0.12,  // Physical D contribute
            "gamer" => 0.08,          // Will to compete
            _ => 0.0,
        };
        
        presence += type_bonus * ice_time * 2.0;  // Scale by ice time
    }
    
    presence.min(1.35)  // Cap at +35%
}

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
    
    // Get play style modifiers
    let home_style = get_style_modifiers(&input.home_team.play_style);
    let away_style = get_style_modifiers(&input.away_team.play_style);
    
    // Calculate team ratings
    let home_rating = calculate_team_rating(&input.home_team, home_goalie_idx, true, input.is_playoff);
    let away_rating = calculate_team_rating(&input.away_team, away_goalie_idx, false, input.is_playoff);
    
    // Initialize stats with TOI (only for players who play this game)
    let mut home_stats = init_team_stats(&input.home_team, home_goalie_idx);
    let mut away_stats = init_team_stats(&input.away_team, away_goalie_idx);
    
    let mut home_score = 0;
    let mut away_score = 0;
    
    // Simulate 3 periods
    for _period in 1..=3 {
        let (h_goals, a_goals) = simulate_period(
            &input.home_team,
            &input.away_team,
            home_goalie_idx,
            away_goalie_idx,
            home_rating,
            away_rating,
            &home_style,
            &away_style,
            input.is_playoff,
            &mut home_stats,
            &mut away_stats,
            &mut rng,
        );
        
        home_score += h_goals;
        away_score += a_goals;
    }
    
    let mut went_to_overtime = false;
    let mut went_to_shootout = false;
    
    // Handle ties
    if home_score == away_score && !input.is_playoff {
        went_to_overtime = true;
        
        let (h_ot, a_ot) = simulate_overtime(
            &input.home_team,
            &input.away_team,
            home_goalie_idx,
            away_goalie_idx,
            home_rating,
            away_rating,
            &home_style,
            &away_style,
            false,  // is_playoff = false for regular season
            &mut home_stats,
            &mut away_stats,
            &mut rng,
        );
        
        home_score += h_ot;
        away_score += a_ot;
        
        if home_score == away_score {
            went_to_shootout = true;
            let (h_so, a_so) = simulate_shootout(
                &input.home_team,
                &input.away_team,
                home_rating,
                away_rating,
                &mut rng,
            );
            home_score += h_so;
            away_score += a_so;
        }
    } else if home_score == away_score && input.is_playoff {
        went_to_overtime = true;
        
        // Playoff OT - sudden death until someone scores
        loop {
            let (h_ot, a_ot) = simulate_overtime(
                &input.home_team,
                &input.away_team,
                home_goalie_idx,
                away_goalie_idx,
                home_rating,
                away_rating,
                &home_style,
                &away_style,
                true,  // is_playoff = true
                &mut home_stats,
                &mut away_stats,
                &mut rng,
            );
            
            home_score += h_ot;
            away_score += a_ot;
            
            if home_score != away_score {
                break;
            }
        }
    }
    
    // Calculate plus/minus based on goals for/against while on ice
    finalize_plus_minus(&mut home_stats, home_score, away_score);
    finalize_plus_minus(&mut away_stats, away_score, home_score);
    
    GameResult {
        home_score,
        away_score,
        home_stats,
        away_stats,
        went_to_overtime,
        went_to_shootout,
    }
}

fn select_goalie(team: &Team, rng: &mut ThreadRng) -> usize {
    let goalie_indices: Vec<usize> = team.lines.iter()
        .enumerate()
        .filter(|(_, la)| la.line_type == "goalie")
        .map(|(idx, _)| idx)
        .collect();
    
    if goalie_indices.is_empty() {
        return 0;
    }
    
    let rand_val: f64 = rng.gen();
    if rand_val < GOALIE_GAME_PROBABILITY[0] && !goalie_indices.is_empty() {
        goalie_indices[0]
    } else if goalie_indices.len() > 1 {
        goalie_indices[1]
    } else {
        goalie_indices[0]
    }
}

fn calculate_team_rating(team: &Team, goalie_idx: usize, is_home: bool, is_playoff: bool) -> f64 {
    let mut total_rating = 0.0;
    let mut weight_sum = 0.0;
    
    // Forward lines
    for line_num in 1..=4 {
        let line_players: Vec<&Player> = team.lines.iter()
            .filter(|la| la.line_type == "forward" && la.line_number == line_num)
            .map(|la| &la.player)
            .collect();
        
        let ice_time = FORWARD_LINE_TIME[(line_num - 1) as usize];
        if !line_players.is_empty() {
            let line_rating = calculate_line_rating(&line_players, line_num, is_playoff);
            total_rating += line_rating * ice_time;
        } else {
            total_rating += 50.0 * ice_time;
        }
        weight_sum += ice_time;
    }
    
    // Defense pairs
    for pair_num in 1..=3 {
        let pair_players: Vec<&Player> = team.lines.iter()
            .filter(|la| la.line_type == "defense" && la.line_number == pair_num)
            .map(|la| &la.player)
            .collect();
        
        let ice_time = DEFENSE_LINE_TIME[(pair_num - 1) as usize];
        if !pair_players.is_empty() {
            let pair_rating = calculate_defense_rating(&pair_players, pair_num, is_playoff);
            total_rating += pair_rating * ice_time;
        } else {
            total_rating += 50.0 * ice_time;
        }
        weight_sum += ice_time;
    }
    
    // Goalie
    if goalie_idx < team.lines.len() && team.lines[goalie_idx].line_type == "goalie" {
        let goalie = &team.lines[goalie_idx].player;
        let goalie_rating = goalie.off as f64;  // For goalies, off = gen rating
        total_rating += goalie_rating * 0.3;
        weight_sum += 0.3;
    } else {
        total_rating += 50.0 * 0.3;
        weight_sum += 0.3;
    }
    
    // Coach modifier
    let coach_modifier = if let Some(coach) = &team.coach {
        1.0 + (coach.rating as f64 - 75.0) / 500.0
    } else {
        0.98
    };
    
    let mut final_rating = (total_rating / weight_sum.max(0.1)) * coach_modifier;
    
    if is_home {
        final_rating *= HOME_ICE_ADVANTAGE;
    }
    
    final_rating
}

fn calculate_line_rating(players: &[&Player], line_num: i32, is_playoff: bool) -> f64 {
    if players.is_empty() {
        return 50.0;
    }
    
    // Different weights per line
    let (off_w, def_w, phys_w) = match line_num {
        1 => (0.50, 0.30, 0.20),
        2 => (0.40, 0.40, 0.20),
        3 => (0.25, 0.50, 0.25),
        _ => (0.20, 0.40, 0.40),
    };
    
    let mut total_rating = 0.0;
    let mut leadership_boost = 0.0;
    
    for player in players {
        let phys = if is_playoff {
            (player.phys as f64 * PLAYOFF_PHYS_BOOST).min(100.0)
        } else {
            player.phys as f64
        };
        
        let rating = (player.off as f64 * off_w) +
                     (player.def as f64 * def_w) +
                     (phys * phys_w);
        
        total_rating += rating;
        leadership_boost += player.lead as f64;
    }
    
    let avg_leadership = leadership_boost / players.len() as f64;
    let leadership_multiplier = 1.0 + (avg_leadership - 75.0) / 1000.0;
    
    (total_rating / players.len() as f64) * leadership_multiplier
}

fn calculate_defense_rating(players: &[&Player], pair_num: i32, is_playoff: bool) -> f64 {
    if players.is_empty() {
        return 50.0;
    }
    
    let (off_w, def_w, phys_w) = match pair_num {
        1 => (0.40, 0.30, 0.30),
        2 => (0.30, 0.40, 0.30),
        _ => (0.10, 0.50, 0.40),
    };
    
    let mut total_rating = 0.0;
    
    for player in players {
        let phys = if is_playoff {
            (player.phys as f64 * PLAYOFF_PHYS_BOOST).min(100.0)
        } else {
            player.phys as f64
        };
        
        let rating = (player.off as f64 * off_w) +
                     (player.def as f64 * def_w) +
                     (phys * phys_w);
        
        total_rating += rating;
    }
    
    total_rating / players.len() as f64
}

fn find_goalie_stat_idx(stats: &[PlayerGameStat], team: &Team, goalie_line_idx: usize) -> Option<usize> {
    if goalie_line_idx >= team.lines.len() {
        return None;
    }
    let goalie_id = team.lines[goalie_line_idx].player.id;
    stats.iter().position(|s| s.player_id == goalie_id)
}

fn init_team_stats(team: &Team, active_goalie_idx: usize) -> Vec<PlayerGameStat> {
    team.lines.iter()
        .enumerate()
        .filter_map(|(idx, la)| {
            // Skip goalies who aren't playing this game
            if la.line_type == "goalie" && idx != active_goalie_idx {
                return None;  // Don't create stats for backup goalie
            }
            
            // Calculate base TOI based on line assignment
            let base_toi = match la.line_type.as_str() {
                "forward" => {
                    let line_idx = (la.line_number - 1).min(3) as usize;
                    (GAME_LENGTH_SECONDS as f64 * FORWARD_LINE_TIME[line_idx]) as i32
                },
                "defense" => {
                    let pair_idx = (la.line_number - 1).min(2) as usize;
                    (GAME_LENGTH_SECONDS as f64 * DEFENSE_LINE_TIME[pair_idx]) as i32
                },
                "goalie" => GAME_LENGTH_SECONDS,  // Active goalie plays full game
                _ => 0,
            };
            
            Some(PlayerGameStat {
                player_id: la.player.id,
                player_name: la.player.name.clone(),
                goals: 0,
                assists: 0,
                shots: 0,
                hits: 0,
                blocks: 0,
                plus_minus: 0,
                time_on_ice: base_toi,
                takeaways: 0,
                giveaways: 0,
                saves: 0,
                goals_against: 0,
                shots_against: 0,
            })
        })
        .collect()
}

fn simulate_period(
    home_team: &Team,
    away_team: &Team,
    home_goalie_line_idx: usize,
    away_goalie_line_idx: usize,
    home_rating: f64,
    away_rating: f64,
    home_style: &PlayStyleModifiers,
    away_style: &PlayStyleModifiers,
    is_playoff: bool,
    home_stats: &mut Vec<PlayerGameStat>,
    away_stats: &mut Vec<PlayerGameStat>,
    rng: &mut ThreadRng,
) -> (i32, i32) {
    let mut home_goals = 0;
    let mut away_goals = 0;
    
    // Find goalie indices in the stats arrays (not line arrays)
    let home_goalie_stat_idx = find_goalie_stat_idx(home_stats, home_team, home_goalie_line_idx);
    let away_goalie_stat_idx = find_goalie_stat_idx(away_stats, away_team, away_goalie_line_idx);
    
    // Calculate team-level modifiers
    let home_def_rating = calculate_team_defense_rating(home_team);
    let away_def_rating = calculate_team_defense_rating(away_team);
    let home_intimidation = calculate_team_intimidation(home_team, is_playoff);
    let away_intimidation = calculate_team_intimidation(away_team, is_playoff);
    let home_leadership = calculate_team_leadership(home_team, is_playoff, false);
    let away_leadership = calculate_team_leadership(away_team, is_playoff, false);
    let home_netfront = calculate_netfront_presence(home_team);
    let away_netfront = calculate_netfront_presence(away_team);
    
    // Number of plays affected by styles
    let home_plays = (BASE_PLAYS_PER_PERIOD as f64 * home_style.shot_volume) as i32;
    let away_plays = (BASE_PLAYS_PER_PERIOD as f64 * away_style.shot_volume) as i32;
    
    // Home team plays
    for _ in 0..home_plays {
        if let Some((goal, shooter_idx, primary_assist_idx, secondary_assist_idx)) = simulate_play(
            home_team,
            away_team,
            away_goalie_line_idx,
            home_rating,
            away_rating,
            home_style,
            is_playoff,
            away_def_rating,      // Defending team's DEF
            away_intimidation,    // Defending team's intimidation
            home_leadership,      // Attacking team's leadership
            home_netfront,        // Attacking team's net-front presence
            rng,
        ) {
            // Record shot - find shooter in stats by player_id
            if let Some(shooter_stat_idx) = find_player_stat_idx(home_stats, home_team, shooter_idx) {
                home_stats[shooter_stat_idx].shots += 1;
                
                if goal {
                    home_goals += 1;
                    home_stats[shooter_stat_idx].goals += 1;
                    
                    // Primary assist
                    if let Some(assist_line_idx) = primary_assist_idx {
                        if let Some(assist_stat_idx) = find_player_stat_idx(home_stats, home_team, assist_line_idx) {
                            home_stats[assist_stat_idx].assists += 1;
                        }
                    }
                    
                    // Secondary assist
                    if let Some(assist_line_idx) = secondary_assist_idx {
                        if let Some(assist_stat_idx) = find_player_stat_idx(home_stats, home_team, assist_line_idx) {
                            home_stats[assist_stat_idx].assists += 1;
                        }
                    }
                }
            }
            
            // Update goalie stats
            if let Some(goalie_idx) = away_goalie_stat_idx {
                away_stats[goalie_idx].shots_against += 1;
                if goal {
                    away_stats[goalie_idx].goals_against += 1;
                } else {
                    away_stats[goalie_idx].saves += 1;
                }
            }
        }
    }
    
    // Away team plays
    for _ in 0..away_plays {
        if let Some((goal, shooter_idx, primary_assist_idx, secondary_assist_idx)) = simulate_play(
            away_team,
            home_team,
            home_goalie_line_idx,
            away_rating,
            home_rating,
            away_style,
            is_playoff,
            home_def_rating,      // Defending team's DEF
            home_intimidation,    // Defending team's intimidation
            away_leadership,      // Attacking team's leadership
            away_netfront,        // Attacking team's net-front presence
            rng,
        ) {
            // Record shot - find shooter in stats by player_id
            if let Some(shooter_stat_idx) = find_player_stat_idx(away_stats, away_team, shooter_idx) {
                away_stats[shooter_stat_idx].shots += 1;
                
                if goal {
                    away_goals += 1;
                    away_stats[shooter_stat_idx].goals += 1;
                    
                    // Primary assist
                    if let Some(assist_line_idx) = primary_assist_idx {
                        if let Some(assist_stat_idx) = find_player_stat_idx(away_stats, away_team, assist_line_idx) {
                            away_stats[assist_stat_idx].assists += 1;
                        }
                    }
                    
                    // Secondary assist
                    if let Some(assist_line_idx) = secondary_assist_idx {
                        if let Some(assist_stat_idx) = find_player_stat_idx(away_stats, away_team, assist_line_idx) {
                            away_stats[assist_stat_idx].assists += 1;
                        }
                    }
                }
            }
            
            // Update goalie stats
            if let Some(goalie_idx) = home_goalie_stat_idx {
                home_stats[goalie_idx].shots_against += 1;
                if goal {
                    home_stats[goalie_idx].goals_against += 1;
                } else {
                    home_stats[goalie_idx].saves += 1;
                }
            }
        }
    }
    
    // Physical stats
    simulate_physical_stats(home_stats, home_team, home_style, is_playoff, rng);
    simulate_physical_stats(away_stats, away_team, away_style, is_playoff, rng);
    
    // Turnover stats (takeaways and giveaways)
    simulate_turnovers(home_stats, home_team, rng);
    simulate_turnovers(away_stats, away_team, rng);
    
    (home_goals, away_goals)
}

fn find_player_stat_idx(stats: &[PlayerGameStat], team: &Team, line_idx: usize) -> Option<usize> {
    if line_idx >= team.lines.len() {
        return None;
    }
    let player_id = team.lines[line_idx].player.id;
    stats.iter().position(|s| s.player_id == player_id)
}

fn simulate_play(
    attacking_team: &Team,
    defending_team: &Team,
    goalie_idx: usize,
    attack_rating: f64,
    _defend_rating: f64,
    style: &PlayStyleModifiers,
    is_playoff: bool,
    defender_def_rating: f64,
    defender_intimidation: f64,
    attacker_leadership: f64,
    attacker_netfront: f64,
    rng: &mut ThreadRng,
) -> Option<(bool, usize, Option<usize>, Option<usize>)> {
    // 25% of plays result in a shot attempt (calibrated for ~28-30 shots/team/game)
    if rng.gen::<f64>() > SHOT_ATTEMPT_RATE {
        return None;
    }
    
    // Select shooter with exponential weighting
    let (shooter_idx, line_num) = select_shooter_weighted(attacking_team, rng);
    let shooter = &attacking_team.lines[shooter_idx].player;
    
    // Apply consistency variance
    let consistency_factor = shooter.consistency as f64 / 100.0;
    let variance = rng.gen_range(-0.20..0.20) * (1.0 - consistency_factor);
    let adjusted_off = (shooter.off as f64 * (1.0 + variance)).max(1.0);
    
    // Determine shot quality (affected by defender DEF rating and player type)
    let shot_quality = get_shot_quality_with_defense(line_num, adjusted_off as i32, &shooter.player_type, style, defender_def_rating, rng);
    
    // Calculate goal probability using xG
    let base_xg = shot_quality.base_xg();
    
    // Shooter modifier (95 OFF = 1.19x, 70 OFF = 0.875x)
    let shooter_modifier = adjusted_off / 80.0;
    
    // Player type modifier
    let type_modifier = get_player_type_goal_modifier(&shooter.player_type);
    
    // Goalie modifier
    let goalie_modifier = if goalie_idx < defending_team.lines.len() {
        let goalie = &defending_team.lines[goalie_idx].player;
        let goalie_rating = goalie.off as f64;  // For goalies, off = gen rating
        85.0 / goalie_rating.max(50.0)
    } else {
        1.2  // No goalie = easier to score
    };
    
    // Team rating differential (simplified - attack vs baseline)
    let rating_modifier = attack_rating / 80.0;
    
    // Playoff physicality boost for rebounds
    let playoff_modifier = if is_playoff && matches!(shot_quality, ShotQuality::HighDanger) {
        1.05
    } else {
        1.0
    };
    
    // Style rebound bonus + net-front presence
    let rebound_modifier = if matches!(shot_quality, ShotQuality::HighDanger) {
        style.rebound_goals * attacker_netfront
    } else {
        1.0
    };
    
    // Intimidation reduces shooter confidence
    let intimidation_modifier = 1.0 - defender_intimidation;
    
    // Leadership boosts scoring
    let leadership_modifier = attacker_leadership;
    
    // Final goal probability
    let goal_prob = base_xg 
        * shooter_modifier 
        * type_modifier 
        * goalie_modifier 
        * rating_modifier 
        * playoff_modifier
        * rebound_modifier
        * intimidation_modifier
        * leadership_modifier;
    
    let is_goal = rng.gen::<f64>() < goal_prob.min(0.50);  // Cap at 50% per shot
    
    // Determine assists (realistic: ~5% unassisted, ~25% one assist, ~70% two assists)
    let (primary_assist, secondary_assist) = if is_goal {
        let primary = if rng.gen::<f64>() < 0.95 {
            select_assist_player(attacking_team, shooter_idx, line_num, rng)
        } else {
            None  // ~5% unassisted goals
        };
        
        let secondary = if primary.is_some() && rng.gen::<f64>() < 0.75 {
            select_secondary_assist(attacking_team, shooter_idx, primary, line_num, rng)
        } else {
            None
        };
        
        (primary, secondary)
    } else {
        (None, None)
    };
    
    Some((is_goal, shooter_idx, primary_assist, secondary_assist))
}

fn select_shooter_weighted(team: &Team, rng: &mut ThreadRng) -> (usize, i32) {
    // Exponential weighting: ice_time^1.5 * (off/80)^1.3
    let weights: Vec<f64> = team.lines.iter()
        .map(|la| {
            if la.line_type == "goalie" {
                return 0.0;
            }
            
            let ice_time = match la.line_type.as_str() {
                "forward" => FORWARD_LINE_TIME[(la.line_number - 1).min(3) as usize],
                "defense" => DEFENSE_LINE_TIME[(la.line_number - 1).min(2) as usize] * 0.4,
                _ => 0.1,
            };
            
            // Exponential weighting for more realistic distribution
            let time_weight = ice_time.powf(1.5);
            let skill_weight = (la.player.off as f64 / 80.0).powf(1.3);
            
            time_weight * skill_weight
        })
        .collect();
    
    // Handle case where all weights might be zero
    let total_weight: f64 = weights.iter().sum();
    if total_weight <= 0.0 {
        return (0, 1);
    }
    
    let dist = WeightedIndex::new(&weights).unwrap_or_else(|_| {
        WeightedIndex::new(&vec![1.0; weights.len()]).unwrap()
    });
    
    let idx = dist.sample(rng);
    let line_num = team.lines[idx].line_number;
    (idx, line_num)
}

fn get_shot_quality(line_num: i32, player_off: i32, style: &PlayStyleModifiers, rng: &mut ThreadRng) -> ShotQuality {
    // Base high-danger chance by line
    let base_hd_chance = match line_num {
        1 => 0.40,
        2 => 0.30,
        3 => 0.20,
        _ => 0.15,
    };
    
    // Skill bonus (up to +8% for 95 OFF)
    let skill_bonus = (player_off as f64 - 80.0) / 200.0;
    
    // Style modifier
    let high_danger_chance = (base_hd_chance + skill_bonus) * style.high_danger_chance;
    let medium_danger_chance = 0.35;  // Fixed medium danger rate
    
    let roll: f64 = rng.gen();
    
    if roll < high_danger_chance {
        ShotQuality::HighDanger
    } else if roll < high_danger_chance + medium_danger_chance {
        ShotQuality::MediumDanger
    } else {
        ShotQuality::LowDanger
    }
}

/// Shot quality with defender DEF rating suppression and player type bonus
fn get_shot_quality_with_defense(line_num: i32, player_off: i32, player_type: &str, style: &PlayStyleModifiers, defender_def: f64, rng: &mut ThreadRng) -> ShotQuality {
    // Base high-danger chance by line
    let base_hd_chance = match line_num {
        1 => 0.40,
        2 => 0.30,
        3 => 0.20,
        _ => 0.15,
    };
    
    // Skill bonus (up to +8% for 95 OFF)
    let skill_bonus = (player_off as f64 - 80.0) / 200.0;
    
    // Defense suppression: 85 DEF = -10% high danger chance
    let def_suppression = (defender_def - 75.0) / 100.0;
    
    // Player type modifier for shot quality
    let type_modifier = get_player_type_shot_quality_modifier(player_type);
    
    // Style modifier with defense suppression and player type
    let high_danger_chance = ((base_hd_chance + skill_bonus) * style.high_danger_chance * type_modifier * (1.0 - def_suppression)).max(0.05);
    let medium_danger_chance = 0.35;  // Fixed medium danger rate
    
    let roll: f64 = rng.gen();
    
    if roll < high_danger_chance {
        ShotQuality::HighDanger
    } else if roll < high_danger_chance + medium_danger_chance {
        ShotQuality::MediumDanger
    } else {
        ShotQuality::LowDanger
    }
}

fn get_player_type_goal_modifier(player_type: &str) -> f64 {
    // Valid types: Power Forward, Playmaker, Offensive, Two-Way, Sniper, Power Defense, Gamer, Defensive
    match player_type.to_lowercase().as_str() {
        // Offensive types - higher goal rates
        "sniper" => 1.25,           // +25% goal rate (elite finisher)
        "offensive" => 1.20,        // +20% (offensive D-man)
        "power forward" => 1.15,    // +15% (net-front presence)
        "gamer" => 1.08,            // +8% (clutch scorer)
        // Balanced types
        "two-way" | "two way" => 1.0,
        "power defense" => 0.95,
        // Defensive types - lower goal rates
        "playmaker" => 0.85,        // -15% (passes more than shoots)
        "defensive" => 0.70,        // -30% (stay-at-home)
        _ => 1.0,
    }
}

fn get_player_type_assist_modifier(player_type: &str) -> f64 {
    // Valid types: Power Forward, Playmaker, Offensive, Two-Way, Sniper, Power Defense, Gamer, Defensive
    match player_type.to_lowercase().as_str() {
        // Offensive/playmaking types - higher assist rates
        "playmaker" => 1.50,        // +50% assist rate (elite passers)
        "offensive" => 1.40,        // +40% (offensive D-men)
        "two-way" | "two way" => 1.15,
        "gamer" => 1.10,            // +10% (smart plays)
        "power forward" => 1.05,
        "power defense" => 1.0,
        // Finishers - lower assist rates
        "sniper" => 0.75,           // -25% (finishes, doesn't pass)
        "defensive" => 0.60,        // -40% (stay-at-home D)
        _ => 0.95,
    }
}

/// Shot quality modifier - affects chance of getting high-danger shots
/// Valid types: Power Forward, Playmaker, Offensive, Two-Way, Sniper, Power Defense, Gamer, Defensive
fn get_player_type_shot_quality_modifier(player_type: &str) -> f64 {
    match player_type.to_lowercase().as_str() {
        // High skill players get better scoring chances
        "sniper" => 1.15,           // +15% high-danger chance
        "power forward" => 1.12,    // +12% (drives to net)
        "offensive" => 1.10,        // +10% (offensive D rushing)
        "playmaker" => 1.05,        // +5% (creates space)
        "gamer" => 1.05,            // +5% (finds way to score)
        // Defensive types get lower quality chances
        "two-way" | "two way" => 1.0,
        "power defense" => 0.95,
        "defensive" => 0.88,
        _ => 1.0,
    }
}

fn select_assist_player(team: &Team, shooter_idx: usize, line_num: i32, rng: &mut ThreadRng) -> Option<usize> {
    let shooter_type = &team.lines[shooter_idx].line_type;
    
    // Primary assist: prefer same position type (forwards assist forwards, D assists D)
    // But 25% chance to cross over (D assisting forwards or vice versa)
    let prefer_same_type = rng.gen::<f64>() < 0.75;
    
    // First try to find players on same line AND same position type
    let mut candidates: Vec<usize> = team.lines.iter()
        .enumerate()
        .filter(|(idx, la)| {
            *idx != shooter_idx && 
            la.line_type != "goalie" &&
            if prefer_same_type {
                la.line_type == *shooter_type && la.line_number == line_num
            } else {
                // Cross-position: get D for forward goals, forwards for D goals
                la.line_type != *shooter_type
            }
        })
        .map(|(idx, _)| idx)
        .collect();
    
    // Fallback: any non-goalie on ice
    if candidates.is_empty() {
        candidates = team.lines.iter()
            .enumerate()
            .filter(|(idx, la)| *idx != shooter_idx && la.line_type != "goalie")
            .map(|(idx, _)| idx)
            .collect();
    }
    
    if candidates.is_empty() {
        return None;
    }
    
    // Weight by player type, skill, and ice time
    let weights: Vec<f64> = candidates.iter()
        .map(|&idx| {
            let la = &team.lines[idx];
            let player = &la.player;
            let type_mod = get_player_type_assist_modifier(&player.player_type);
            
            // Ice time weighting - top lines/pairs get more assists
            let ice_time_weight = match la.line_type.as_str() {
                "forward" => FORWARD_LINE_TIME[(la.line_number - 1).min(3) as usize],
                "defense" => DEFENSE_LINE_TIME[(la.line_number - 1).min(2) as usize],
                _ => 0.1,
            };
            
            // Exponential weighting for D-men assists (pair 1 >> pair 3)
            let position_weight = if la.line_type == "defense" {
                ice_time_weight.powf(2.0)  // Squared for steeper drop-off
            } else {
                ice_time_weight.powf(1.3)
            };
            
            type_mod * position_weight * (player.off as f64 / 80.0)
        })
        .collect();
    
    let total: f64 = weights.iter().sum();
    if total <= 0.0 {
        return Some(candidates[rng.gen_range(0..candidates.len())]);
    }
    
    let dist = WeightedIndex::new(&weights).ok()?;
    Some(candidates[dist.sample(rng)])
}

fn select_secondary_assist(team: &Team, shooter_idx: usize, primary_idx: Option<usize>, line_num: i32, rng: &mut ThreadRng) -> Option<usize> {
    let shooter_type = &team.lines[shooter_idx].line_type;
    
    // Secondary assist: 50% chance to cross position (often D-man feeding play)
    let prefer_crossover = rng.gen::<f64>() < 0.50;
    
    let mut candidates: Vec<usize> = team.lines.iter()
        .enumerate()
        .filter(|(idx, la)| {
            *idx != shooter_idx && 
            Some(*idx) != primary_idx &&
            la.line_type != "goalie" &&
            if prefer_crossover {
                la.line_type != *shooter_type  // D-man for forward goals
            } else {
                la.line_type == *shooter_type && la.line_number == line_num
            }
        })
        .map(|(idx, _)| idx)
        .collect();
    
    // Fallback
    if candidates.is_empty() {
        candidates = team.lines.iter()
            .enumerate()
            .filter(|(idx, la)| {
                *idx != shooter_idx && 
                Some(*idx) != primary_idx && 
                la.line_type != "goalie"
            })
            .map(|(idx, _)| idx)
            .collect();
    }
    
    if candidates.is_empty() {
        return None;
    }
    
    // Weight heavily by ice time for secondary assists
    let weights: Vec<f64> = candidates.iter()
        .map(|&idx| {
            let la = &team.lines[idx];
            let player = &la.player;
            let type_mod = get_player_type_assist_modifier(&player.player_type);
            
            let ice_time_weight = match la.line_type.as_str() {
                "forward" => FORWARD_LINE_TIME[(la.line_number - 1).min(3) as usize],
                "defense" => DEFENSE_LINE_TIME[(la.line_number - 1).min(2) as usize],
                _ => 0.1,
            };
            
            // Very steep weighting for D secondary assists (top pair dominates)
            let position_weight = if la.line_type == "defense" {
                ice_time_weight.powf(2.5)  // Even steeper for secondary
            } else {
                ice_time_weight.powf(1.5)
            };
            
            type_mod * position_weight * (player.off as f64 / 85.0)
        })
        .collect();
    
    let total: f64 = weights.iter().sum();
    if total <= 0.0 {
        return Some(candidates[rng.gen_range(0..candidates.len())]);
    }
    
    let dist = WeightedIndex::new(&weights).ok()?;
    Some(candidates[dist.sample(rng)])
}

fn simulate_physical_stats(
    stats: &mut Vec<PlayerGameStat>,
    team: &Team,
    style: &PlayStyleModifiers,
    is_playoff: bool,
    rng: &mut ThreadRng,
) {
    for (line_idx, la) in team.lines.iter().enumerate() {
        if la.line_type == "goalie" {
            continue;
        }
        
        // Find this player in stats array by player_id
        let stat_idx = match find_player_stat_idx(stats, team, line_idx) {
            Some(idx) => idx,
            None => continue,
        };
        
        // Ice time scaling - opportunities proportional to time on ice
        let ice_time_factor = match la.line_type.as_str() {
            "forward" => FORWARD_LINE_TIME[(la.line_number - 1).min(3) as usize],
            "defense" => DEFENSE_LINE_TIME[(la.line_number - 1).min(2) as usize],
            _ => 0.10,
        };
        
        let phys = if is_playoff {
            (la.player.phys as f64 * PLAYOFF_PHYS_BOOST).min(100.0)
        } else {
            la.player.phys as f64
        };
        
        // Player type HITS modifiers - physical players hit more, skill players hit less
        // Valid types: Power Forward, Playmaker, Offensive, Two-Way, Sniper, Power Defense, Gamer, Defensive
        let hit_type_mod = match la.player.player_type.to_lowercase().as_str() {
            "power forward" => 1.40,   // Physical presence
            "power defense" => 1.35,
            "defensive" => 1.15,
            "gamer" => 1.10,           // Compete level
            "two-way" | "two way" => 1.0,
            "offensive" => 0.75,       // Finesse player
            "playmaker" => 0.60,       // Playmakers avoid contact
            "sniper" => 0.55,          // Snipers avoid contact
            _ => 0.90,
        };
        
        // Hits: scale by ice time, physicality, type, and style
        // Base opportunities scaled by ice time (top line ~20, 4th line ~8)
        let hit_opportunities = (50.0 * ice_time_factor) as i32;
        let hit_chance = (phys / 100.0) * 0.04 * style.physical_bonus * hit_type_mod;
        stats[stat_idx].hits += (0..hit_opportunities).filter(|_| rng.gen::<f64>() < hit_chance).count() as i32;
        
        // Player type BLOCKS modifiers - defensive players block, offensive avoid it
        // Valid types: Power Forward, Playmaker, Offensive, Two-Way, Sniper, Power Defense, Gamer, Defensive
        let block_type_mod = match la.player.player_type.to_lowercase().as_str() {
            "defensive" => 1.40,       // Shot-blocking specialists
            "power defense" => 1.30,
            "two-way" | "two way" => 1.15,
            "gamer" => 1.10,           // Will sacrifice body
            "power forward" => 0.90,
            "offensive" => 0.55,       // Offensive D less willing to block
            "playmaker" => 0.50,       // Playmakers don't block
            "sniper" => 0.45,          // Snipers don't block
            _ => 0.85,
        };
        
        // Position modifier - D block more than forwards
        let position_block_mod = if la.line_type == "defense" { 1.5 } else { 1.0 };
        
        // Blocks: scale by ice time, defensive skill, type, and position
        let block_opportunities = (40.0 * ice_time_factor) as i32;
        let block_chance = (la.player.def as f64 / 100.0) * 0.025 * block_type_mod * position_block_mod;
        stats[stat_idx].blocks += (0..block_opportunities).filter(|_| rng.gen::<f64>() < block_chance).count() as i32;
    }
}

/// Simulate turnovers - takeaways (caused by DEF) and giveaways (caused by low CONST)
fn simulate_turnovers(
    stats: &mut Vec<PlayerGameStat>,
    team: &Team,
    rng: &mut ThreadRng,
) {
    for (line_idx, la) in team.lines.iter().enumerate() {
        if la.line_type == "goalie" {
            continue;
        }
        
        let stat_idx = match find_player_stat_idx(stats, team, line_idx) {
            Some(idx) => idx,
            None => continue,
        };
        
        // Ice time scaling
        let ice_time_factor = match la.line_type.as_str() {
            "forward" => FORWARD_LINE_TIME[(la.line_number - 1).min(3) as usize],
            "defense" => DEFENSE_LINE_TIME[(la.line_number - 1).min(2) as usize],
            _ => 0.10,
        };
        
        // === TAKEAWAYS (caused by high DEF) ===
        // Valid types: Power Forward, Playmaker, Offensive, Two-Way, Sniper, Power Defense, Gamer, Defensive
        let takeaway_type_mod = match la.player.player_type.to_lowercase().as_str() {
            "defensive" => 1.40,       // Elite at forcing turnovers
            "two-way" | "two way" => 1.25,
            "power defense" => 1.15,
            "gamer" => 1.12,           // Smart plays
            "playmaker" => 1.10,       // Good stick handling awareness
            "power forward" => 1.0,
            "sniper" => 0.75,          // Not focused on defense
            "offensive" => 0.80,       // Offensive D less defensive
            _ => 1.0,
        };
        
        // Position modifier - D get more takeaways
        let position_takeaway_mod = if la.line_type == "defense" { 1.3 } else { 1.0 };
        
        let takeaway_opportunities = (30.0 * ice_time_factor) as i32;
        let takeaway_chance = (la.player.def as f64 / 100.0) * 0.02 * takeaway_type_mod * position_takeaway_mod;
        stats[stat_idx].takeaways += (0..takeaway_opportunities).filter(|_| rng.gen::<f64>() < takeaway_chance).count() as i32;
        
        // === GIVEAWAYS (caused by low CONST) ===
        // Valid types: Power Forward, Playmaker, Offensive, Two-Way, Sniper, Power Defense, Gamer, Defensive
        let giveaway_type_mod = match la.player.player_type.to_lowercase().as_str() {
            "offensive" => 1.15,       // Risk-taking, high-reward plays
            "playmaker" => 1.10,       // Handle puck more, slightly more turnovers
            "sniper" => 1.05,
            "power forward" => 0.95,
            "gamer" => 0.90,           // Smart, reliable
            "two-way" | "two way" => 0.85,
            "power defense" => 0.80,   // Simple plays
            "defensive" => 0.70,       // Safe plays
            _ => 1.0,
        };
        
        // Giveaways based on inverse of consistency
        let consistency_factor = la.player.consistency as f64 / 100.0;
        let giveaway_opportunities = (25.0 * ice_time_factor) as i32;
        let giveaway_chance = ((1.0 - consistency_factor) * 0.03 + 0.005) * giveaway_type_mod;
        stats[stat_idx].giveaways += (0..giveaway_opportunities).filter(|_| rng.gen::<f64>() < giveaway_chance).count() as i32;
    }
}

fn simulate_overtime(
    home_team: &Team,
    away_team: &Team,
    home_goalie_line_idx: usize,
    away_goalie_line_idx: usize,
    home_rating: f64,
    away_rating: f64,
    home_style: &PlayStyleModifiers,
    away_style: &PlayStyleModifiers,
    is_playoff: bool,
    home_stats: &mut Vec<PlayerGameStat>,
    away_stats: &mut Vec<PlayerGameStat>,
    rng: &mut ThreadRng,
) -> (i32, i32) {
    let mut home_goals = 0;
    let mut away_goals = 0;
    
    // Find goalie indices in the stats arrays
    let home_goalie_stat_idx = find_goalie_stat_idx(home_stats, home_team, home_goalie_line_idx);
    let away_goalie_stat_idx = find_goalie_stat_idx(away_stats, away_team, away_goalie_line_idx);
    
    // Calculate team modifiers (OT is clutch time!)
    let home_def_rating = calculate_team_defense_rating(home_team);
    let away_def_rating = calculate_team_defense_rating(away_team);
    let home_intimidation = calculate_team_intimidation(home_team, is_playoff);
    let away_intimidation = calculate_team_intimidation(away_team, is_playoff);
    let home_leadership = calculate_team_leadership(home_team, is_playoff, true);  // Clutch = true
    let away_leadership = calculate_team_leadership(away_team, is_playoff, true);
    let home_netfront = calculate_netfront_presence(home_team);
    let away_netfront = calculate_netfront_presence(away_team);
    
    // OT is 3-on-3 with higher scoring - use top lines only
    for _ in 0..OT_PLAYS {
        // Home attack
        if let Some((goal, shooter_line_idx, primary_assist_idx, secondary_assist_idx)) = simulate_ot_play(
            home_team,
            away_team,
            away_goalie_line_idx,
            home_rating,
            away_rating,
            home_style,
            away_def_rating,
            away_intimidation,
            home_leadership,
            home_netfront,
            rng,
        ) {
            if let Some(shooter_stat_idx) = find_player_stat_idx(home_stats, home_team, shooter_line_idx) {
                home_stats[shooter_stat_idx].shots += 1;
                
                if goal {
                    home_goals += 1;
                    home_stats[shooter_stat_idx].goals += 1;
                    if let Some(assist_line_idx) = primary_assist_idx {
                        if let Some(assist_stat_idx) = find_player_stat_idx(home_stats, home_team, assist_line_idx) {
                            home_stats[assist_stat_idx].assists += 1;
                        }
                    }
                    if let Some(assist_line_idx) = secondary_assist_idx {
                        if let Some(assist_stat_idx) = find_player_stat_idx(home_stats, home_team, assist_line_idx) {
                            home_stats[assist_stat_idx].assists += 1;
                        }
                    }
                }
            }
            
            if let Some(goalie_idx) = away_goalie_stat_idx {
                away_stats[goalie_idx].shots_against += 1;
                if goal {
                    away_stats[goalie_idx].goals_against += 1;
                    return (home_goals, away_goals);  // Sudden death
                } else {
                    away_stats[goalie_idx].saves += 1;
                }
            } else if goal {
                return (home_goals, away_goals);  // Sudden death even without goalie tracking
            }
        }
        
        // Away attack
        if let Some((goal, shooter_line_idx, primary_assist_idx, secondary_assist_idx)) = simulate_ot_play(
            away_team,
            home_team,
            home_goalie_line_idx,
            away_rating,
            home_rating,
            away_style,
            home_def_rating,
            home_intimidation,
            away_leadership,
            away_netfront,
            rng,
        ) {
            if let Some(shooter_stat_idx) = find_player_stat_idx(away_stats, away_team, shooter_line_idx) {
                away_stats[shooter_stat_idx].shots += 1;
                
                if goal {
                    away_goals += 1;
                    away_stats[shooter_stat_idx].goals += 1;
                    if let Some(assist_line_idx) = primary_assist_idx {
                        if let Some(assist_stat_idx) = find_player_stat_idx(away_stats, away_team, assist_line_idx) {
                            away_stats[assist_stat_idx].assists += 1;
                        }
                    }
                    if let Some(assist_line_idx) = secondary_assist_idx {
                        if let Some(assist_stat_idx) = find_player_stat_idx(away_stats, away_team, assist_line_idx) {
                            away_stats[assist_stat_idx].assists += 1;
                        }
                    }
                }
            }
            
            if let Some(goalie_idx) = home_goalie_stat_idx {
                home_stats[goalie_idx].shots_against += 1;
                if goal {
                    home_stats[goalie_idx].goals_against += 1;
                    return (home_goals, away_goals);  // Sudden death
                } else {
                    home_stats[goalie_idx].saves += 1;
                }
            } else if goal {
                return (home_goals, away_goals);  // Sudden death even without goalie tracking
            }
        }
    }
    
    (home_goals, away_goals)
}

fn simulate_ot_play(
    attacking_team: &Team,
    defending_team: &Team,
    goalie_idx: usize,
    attack_rating: f64,
    _defend_rating: f64,
    style: &PlayStyleModifiers,
    defender_def_rating: f64,
    defender_intimidation: f64,
    attacker_leadership: f64,
    attacker_netfront: f64,
    rng: &mut ThreadRng,
) -> Option<(bool, usize, Option<usize>, Option<usize>)> {
    // Higher shot rate in 3-on-3 OT (35% vs 25% regular)
    if rng.gen::<f64>() > 0.35 {
        return None;
    }
    
    // OT uses top lines primarily (line 1-2)
    let top_line_players: Vec<usize> = attacking_team.lines.iter()
        .enumerate()
        .filter(|(_, la)| {
            la.line_type != "goalie" && la.line_number <= 2
        })
        .map(|(idx, _)| idx)
        .collect();
    
    if top_line_players.is_empty() {
        return None;
    }
    
    let shooter_idx = top_line_players[rng.gen_range(0..top_line_players.len())];
    let shooter = &attacking_team.lines[shooter_idx].player;
    let line_num = attacking_team.lines[shooter_idx].line_number;
    
    // Higher xG in 3-on-3, with defense suppression and player type
    let shot_quality = get_shot_quality_with_defense(line_num, shooter.off, &shooter.player_type, style, defender_def_rating, rng);
    let base_xg = shot_quality.base_xg() * 1.5;  // 50% higher in OT
    
    let shooter_modifier = shooter.off as f64 / 80.0;
    let type_modifier = get_player_type_goal_modifier(&shooter.player_type);
    
    let goalie_modifier = if goalie_idx < defending_team.lines.len() {
        let goalie = &defending_team.lines[goalie_idx].player;
        85.0 / (goalie.off as f64).max(50.0)
    } else {
        1.2
    };
    
    // Rating modifier
    let rating_modifier = attack_rating / 80.0;
    
    // Intimidation and leadership
    let intimidation_modifier = 1.0 - defender_intimidation;
    let leadership_modifier = attacker_leadership;
    
    // Net-front presence for rebounds
    let netfront_modifier = if matches!(shot_quality, ShotQuality::HighDanger) {
        attacker_netfront
    } else {
        1.0
    };
    
    let goal_prob = base_xg * shooter_modifier * type_modifier * goalie_modifier 
        * rating_modifier * intimidation_modifier * leadership_modifier * netfront_modifier;
    let is_goal = rng.gen::<f64>() < goal_prob.min(0.50);
    
    // Assists for OT goals (same logic as regular)
    let (primary_assist, secondary_assist) = if is_goal {
        let primary = if rng.gen::<f64>() < 0.95 {
            select_assist_player(attacking_team, shooter_idx, line_num, rng)
        } else {
            None
        };
        let secondary = if primary.is_some() && rng.gen::<f64>() < 0.75 {
            select_secondary_assist(attacking_team, shooter_idx, primary, line_num, rng)
        } else {
            None
        };
        (primary, secondary)
    } else {
        (None, None)
    };
    
    Some((is_goal, shooter_idx, primary_assist, secondary_assist))
}

fn simulate_shootout(
    home_team: &Team,
    away_team: &Team,
    home_rating: f64,
    away_rating: f64,
    rng: &mut ThreadRng,
) -> (i32, i32) {
    let mut home_goals = 0;
    let mut away_goals = 0;
    
    // 3 rounds minimum
    for _round in 0..3 {
        // Home shooter
        let home_shooter = select_best_shooter(home_team, rng);
        let home_prob = 0.30 * (home_team.lines[home_shooter].player.off as f64 / 80.0)
            * get_player_type_goal_modifier(&home_team.lines[home_shooter].player.player_type);
        if rng.gen::<f64>() < home_prob {
            home_goals += 1;
        }
        
        // Away shooter
        let away_shooter = select_best_shooter(away_team, rng);
        let away_prob = 0.30 * (away_team.lines[away_shooter].player.off as f64 / 80.0)
            * get_player_type_goal_modifier(&away_team.lines[away_shooter].player.player_type);
        if rng.gen::<f64>() < away_prob {
            away_goals += 1;
        }
    }
    
    // Sudden death if tied
    while home_goals == away_goals {
        let home_scores = rng.gen::<f64>() < 0.30 * (home_rating / 80.0);
        let away_scores = rng.gen::<f64>() < 0.30 * (away_rating / 80.0);
        
        if home_scores && !away_scores {
            home_goals += 1;
        } else if away_scores && !home_scores {
            away_goals += 1;
        }
    }
    
    (home_goals, away_goals)
}

fn select_best_shooter(team: &Team, rng: &mut ThreadRng) -> usize {
    let forward_indices: Vec<usize> = team.lines.iter()
        .enumerate()
        .filter(|(_, la)| la.line_type == "forward")
        .map(|(idx, _)| idx)
        .collect();
    
    if forward_indices.is_empty() {
        return 0;
    }
    
    let weights: Vec<f64> = forward_indices.iter()
        .map(|&idx| {
            let la = &team.lines[idx];
            let line_weight = match la.line_number {
                1 => 1.0,
                2 => 0.8,
                3 => 0.5,
                _ => 0.3,
            };
            let type_mod = get_player_type_goal_modifier(&la.player.player_type);
            (la.player.off as f64 / 100.0) * line_weight * type_mod
        })
        .collect();
    
    let dist = WeightedIndex::new(&weights).unwrap_or_else(|_| {
        WeightedIndex::new(&vec![1.0; weights.len()]).unwrap()
    });
    
    forward_indices[dist.sample(rng)]
}

fn finalize_plus_minus(stats: &mut [PlayerGameStat], team_goals: i32, opponent_goals: i32) {
    // Simplified: distribute based on TOI proportion
    let total_skater_toi: i32 = stats.iter()
        .filter(|s| s.shots_against == 0)  // Not a goalie
        .map(|s| s.time_on_ice)
        .sum();
    
    if total_skater_toi == 0 {
        return;
    }
    
    let goal_diff = team_goals - opponent_goals;
    
    for stat in stats.iter_mut() {
        if stat.shots_against > 0 {
            continue;  // Skip goalies
        }
        
        // Weight plus/minus by TOI
        let toi_fraction = stat.time_on_ice as f64 / total_skater_toi as f64;
        stat.plus_minus = (goal_diff as f64 * toi_fraction * 3.0).round() as i32;
    }
}
