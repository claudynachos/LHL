# Hockey Simulation Algorithm Documentation

## Overview
This document explains the mathematical formulas and logic used in the Rust-based hockey simulation engine.

## Core Concepts

### 1. Ice Time Distribution
Players receive different amounts of ice time based on their line assignment:

**Forward Lines:**
- Line 1: 35% of game time
- Line 2: 30% of game time
- Line 3: 20% of game time
- Line 4: 15% of game time

**Defense Pairs:**
- Pair 1: 45% of game time
- Pair 2: 35% of game time
- Pair 3: 20% of game time

**Goalies:**
- Starter (G1): 60% of games (plays full game when active)
- Backup (G2): 40% of games (plays full game when active)
- Note: Goalies stay in for the entire game, so % represents games played, not ice time within games

### 2. Player Attributes

Each player has 5 core attributes (0-100 scale) used in the simulation algorithm:
- **OFF** (Offense): Scoring ability, shot accuracy
- **DEF** (Defense): Defensive positioning, takeaways
- **PHYS** (Physicality): Hitting, board battles
- **LEAD** (Leadership): Team performance boost
- **CONST** (Consistency): Reduces variability (future feature)

**Note:** The algorithm uses individual attributes (OFF, DEF, PHYS, LEAD, CONST) directly. The overall rating is calculated separately for frontend display purposes only and is not used in simulation calculations.

**Overall Rating (Frontend Display Only):**
```
OVERALL = (OFF × 1.1 + DEF × 0.95 + PHYS × 0.9 × (LEAD/100) × (CONST/100)) / 2.5
```
This formula is used solely for displaying player ratings in the user interface and does not affect game simulation outcomes.

Different lines emphasize different skills:

**Forward Line Weights [OFF, DEF, PHYS]:**
- Line 1: [50%, 30%, 20%] - Offensive focus
- Line 2: [40%, 40%, 20%] - Balanced
- Line 3: [25%, 50%, 25%] - Defensive focus
- Line 4: [20%, 40%, 40%] - Physical/checking line

**Defense Pair Weights [OFF, DEF, PHYS]:**
- Pair 1: [40%, 30%, 30%] - Offensive defensemen
- Pair 2: [30%, 40%, 30%] - Balanced
- Pair 3: [10%, 50%, 40%] - Stay-at-home/physical

### 3. Line Rating Calculation

For each line/pair, the effective rating is calculated as:

```
line_rating = Σ (player_off × w_off + player_def × w_def + player_phys × w_phys) / num_players
```

**Leadership Modifier:**
```
avg_leadership = Σ player_lead / num_players
leadership_multiplier = 1 + (avg_leadership - 75) / 1000
final_line_rating = line_rating × leadership_multiplier
```

Leadership adds ±2.5% performance boost based on deviation from average (75).

### 4. Team Rating Calculation

```
team_rating = Σ (line_rating × ice_time_percentage) + (goalie_rating × 0.3)
```

**Note:** Goalie rating is from the active goalie for that specific game (G1 plays 60% of games, G2 plays 40% of games).

**Coach Modifier:**
```
coach_multiplier = 1 + (coach_rating - 75) / 500
team_rating = team_rating × coach_multiplier
```

Coaches with rating 50-100 provide -5% to +5% team performance.

**Home Ice Advantage:**
```
if is_home_team:
    team_rating × = 1.05  # +5% boost
```

**Playoff Physicality Boost:**
```
if is_playoff:
    player_phys × = 1.20  # +20% to physicality
```

### 5. Shot Generation

Shots per period are distributed based on team ratings, calibrated to match modern NHL averages (2024-2025 season: ~28.1 shots per team per game = ~9.4 shots per period):

```
total_rating = home_rating + away_rating
home_shot_ratio = home_rating / total_rating

home_shots_per_period = BASE_SHOTS (9.4) × (1 + home_shot_ratio)
away_shots_per_period = BASE_SHOTS (9.4) × (2 - home_shot_ratio)
```

**Target Statistics (Modern NHL 2024-2025):**
- Shots per team per game: ~28.1
- Shots per period per team: ~9.4
- Total shots per game: ~56

**Example:**
- If Home Rating = 85, Away Rating = 75
- Total = 160, Ratio = 0.53125
- Home shots = 9.4 × 1.53 ≈ 14 shots per period
- Away shots = 9.4 × 1.47 ≈ 14 shots per period
- Total per game: ~84 shots (slightly above average for competitive games)

### 6. Shooter Selection

Each shot is attributed to a player weighted by:
```
player_weight = ice_time_percentage × (player_off / 100)
```

Forwards get full weight, defensemen get 40% weight (they shoot less).

### 7. Goal Probability

For each shot, goal probability is calculated as:

```
goal_probability = BASE_PROB (0.10) × (shooter_team_rating / 80) × (80 / goalie_team_rating)
```

**Explanation:**
- Base 10% shooting percentage (matches NHL 2024-2025 average save percentage of .900)
- Scales up with offensive team strength
- Scales down with defensive/goalie team strength
- Target: ~3.01 goals per team per game (NHL 2024-2025 average)

**Example Calculation:**
- Home team rating: 90, Away team rating: 70
- Home goal prob = 0.10 × (90/80) × (80/70) = 0.10 × 1.125 × 1.143 ≈ 12.9%
- Away goal prob = 0.10 × (70/80) × (80/90) = 0.10 × 0.875 × 0.889 ≈ 7.8%

**Validation:**
- With ~28 shots per game and 10% shooting percentage = ~2.8 goals per game
- Algorithm adjusts based on team ratings to reach ~3.01 goals per team per game average

### 8. Assist Attribution

When a goal is scored:
- 60% chance of an assist being credited
- Assist goes to a teammate on the same line (random selection)
- Encourages realistic multi-point games from line combinations

### 9. Physical Stats Simulation

Calibrated to match modern NHL averages (2024-2025: ~15-25 hits and blocks per team per game):

**Hits:**
```
hit_probability_per_opportunity = (player_phys / 100) × 0.05
hits_per_game = Σ(50 opportunities × hit_probability)
```
Target: ~15-25 hits per team per game

In playoffs: `player_phys × 1.20` before calculation

**Blocks:**
```
block_probability = (player_def / 100) × 0.03
blocks_per_game = Σ(40 opportunities × block_probability)
```
Target: ~15-25 blocks per team per game

### 10. Goalie Stats

**Game Assignment:**
- Starting goalie (G1) plays in 60% of games
- Backup goalie (G2) plays in 40% of games
- Active goalie plays the full game (no splitting ice time within a game)

**For each shot against:**
- If goal scored: `goals_against++`
- If no goal: `saves++`
- Always: `shots_against++`

Save percentage = `saves / shots_against`

### 11. Plus/Minus Calculation

Simplified implementation:
```
player_plus_minus = team_goals - opponent_goals
```

*Note: In future versions, this will be weighted by ice time during even-strength goals.*

## Expected Outputs

### Realistic Modern NHL Statistics (2024-2025 Baseline)

**Game-Level Averages:**
- Goals per team per game: ~3.01
- Shots per team per game: ~28.1
- Save percentage: ~.900
- Hits per team per game: ~15-25
- Blocks per team per game: ~15-25

**Top Line Center (35% ice time, 95 OFF, 85 DEF):**
- Goals per game: 0.8-1.2
- Assists per game: 1.0-1.5
- Total points: ~140-180 per 82-game season

**Top Defenseman (45% ice time, 85 OFF, 95 DEF):**
- Goals per game: 0.3-0.6
- Assists per game: 0.8-1.2
- Blocks: 2-4 per game

**Elite Goalie (94 rating, 60% games):**
- Save percentage: .900-.920
- Goals against average: 2.5-3.0

**Physical Fourth Liner (15% ice time, 70 OFF, 80 DEF, 95 PHYS):**
- Goals per game: 0.1-0.3
- Hits per game: 3-6
- Blocks: 0.5-1.5

## Balancing Philosophy

1. **Realism over randomness**: Ratings directly influence outcomes
2. **Line chemistry matters**: Same-line players assist each other
3. **Playoffs are different**: Physicality becomes more valuable
4. **Stars shine**: Top players get more ice time and opportunities
5. **Role players matter**: Depth and defensive players impact goals against

## Performance Targets

- Single game simulation: < 100ms
- Full season (82 games): < 5 seconds
- Statistical variance: ±15% season-to-season based on consistency rating

## Future Enhancements

1. **Consistency Rating**: Implement season-to-season variance
2. **Fatigue System**: Reduce performance late in games/seasons
3. **Matchup Bonuses**: Line vs line advantages
4. **Special Teams**: Power play and penalty kill units
5. **Injuries**: Random events affecting availability
