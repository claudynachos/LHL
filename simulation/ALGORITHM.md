# Hockey Simulation Algorithm Documentation

## Overview

This document explains the mathematical formulas and logic used in the Rust-based hockey simulation engine. The simulation uses an **xG-based play-by-play** approach, combining expected goals (xG) concepts with event-driven simulation for realistic stat distributions.

## Core Concepts

### 1. Ice Time Distribution

Players receive different amounts of ice time based on their line assignment:

**Forward Lines:**
- Line 1: 35% of game time (~21 min)
- Line 2: 30% of game time (~18 min)
- Line 3: 20% of game time (~12 min)
- Line 4: 15% of game time (~9 min)

**Defense Pairs:**
- Pair 1: 45% of game time (~27 min)
- Pair 2: 35% of game time (~21 min)
- Pair 3: 20% of game time (~12 min)

**Goalies:**
- Starter (G1): 60% of games (plays full game when active)
- Backup (G2): 40% of games (plays full game when active)
- Note: Goalies stay in for the entire game, so % represents games played, not ice time within games

### 2. Player Attributes

Each player has 5 core attributes (0-100 scale) - ALL actively used in simulation:

- **OFF** (Offense): Scoring ability, shot accuracy, shooter selection weighting
- **DEF** (Defense): 
  - Shot quality suppression (high DEF reduces opponent high-danger chances)
  - Takeaway generation
  - Blocks
- **PHYS** (Physicality): 
  - Hit generation
  - Team intimidation (reduces opponent scoring confidence)
  - Playoff intensity boost
- **LEAD** (Leadership): 
  - Line chemistry bonus (85+ LEAD boosts linemates)
  - Clutch performance in close games/3rd period
  - Playoff intensity multiplier
- **CONST** (Consistency): 
  - Game-to-game performance variance
  - Giveaway prevention (low CONST = more turnovers)

### 3. Player Types

The simulation supports 8 player types (matching actual player data):

| Type | Goals | Assists | Shot Quality | Hits | Blocks | Takeaways | Giveaways | Intimidation | Defense |
|------|-------|---------|--------------|------|--------|-----------|-----------|--------------|---------|
| **Sniper** | +25% | -25% | +15% | -45% | -55% | -25% | +5% | -25% | -12% |
| **Playmaker** | -15% | +50% | +5% | -40% | -50% | +10% | +10% | -20% | -8% |
| **Power Forward** | +15% | +5% | +12% | +40% | -10% | - | -5% | +20% | - |
| **Two-Way** | - | +15% | - | - | +15% | +25% | -15% | - | +8% |
| **Gamer** | +8% | +10% | +5% | +10% | +10% | +12% | -10% | +5% | +5% |
| **Defensive** | -30% | -40% | -12% | +15% | +40% | +40% | -30% | +10% | +15% |
| **Offensive (D)** | +20% | +40% | +10% | -25% | -45% | -20% | +15% | -15% | -10% |
| **Power Defense** | -5% | - | -5% | +35% | +30% | +15% | -20% | +18% | +12% |

### 4. Play Styles

Teams can adopt different play styles that affect simulation:

| Style | Shot Volume | High-Danger | Turnovers | Odd-Man Rush | Physical | Rebounds |
|-------|-------------|-------------|-----------|--------------|----------|----------|
| Trap | 85% | 90% | +20% forced | 80% | 100% | 90% |
| Possession | 95% | 125% | -20% | 90% | 90% | 100% |
| Dump & Chase | 110% | 90% | 100% | 85% | 140% | 125% |
| Rush | 105% | 115% | +10% risky | 135% | 85% | 95% |
| Shoot & Crash | 125% | 100% | +5% | 90% | 120% | 120% |

**Coach Type to Default Style:**
- Defensive/Trap coach → Trap
- Offensive/Possession coach → Possession
- Physical/Grinder coach → Dump & Chase
- Speed/Transition coach → Rush
- Aggressive/Crash coach → Shoot & Crash

## Simulation Flow

### Play-by-Play Structure

Each period simulates ~50 "plays" (adjusted by play style), with 25% resulting in shots:

```
1. For each play (~50 per period):
   a. 25% chance of shot attempt (adjusted by style)
   b. Select shooter using exponential weighting
   c. Apply consistency variance to shooter
   d. Determine shot quality zone
   e. Calculate xG-based goal probability
   f. Apply shooter, goalie, and team modifiers
   g. Roll for goal
   h. If goal: assign assists to linemates
   i. Track TOI, hits, blocks
```

### Shooter Selection (Exponential Weighting)

```
weight = ice_time^1.5 × (player_off / 80)^1.3
```

**Example distributions:**
- Line 1 (35% TOI, 95 OFF): weight = 0.207 × 1.25 = 0.259
- Line 4 (15% TOI, 70 OFF): weight = 0.058 × 0.84 = 0.049
- **Ratio: 5.3x more shots for 1st line**

### Shot Quality Zones (xG Model)

Three shot quality zones with base expected goals:

| Zone | Base xG | Description |
|------|---------|-------------|
| High-Danger | 0.20 | Slot, odd-man rush, rebound |
| Medium-Danger | 0.08 | Between circles, point shot with screen |
| Low-Danger | 0.03 | Perimeter, point shot no screen |

**High-danger chance by line:**
```
Line 1: 40% + (OFF - 80) / 200  → 40-48% for elite players
Line 2: 30% + (OFF - 80) / 250  → 30-36%
Line 3: 20%
Line 4: 15%
```

### Defense Suppression

High-DEF teams force opponents into lower-quality shots (**LINEAR** scaling):

```
defender_suppression = (avg_team_DEF - 75) / 100
high_danger_chance *= (1 - defender_suppression)
```

**Examples**:
- 75 avg DEF = no suppression (baseline)
- 80 avg DEF = -5% opponent high-danger chances
- 85 avg DEF = -10% opponent high-danger chances
- 90 avg DEF = -15% opponent high-danger chances

Defensive player types provide extra suppression:
- Defensive: +15%, Power Defense: +12%, Two-Way: +8%, Gamer: +5%
- Offensive D: -10%, Playmaker: -8%, Sniper: -12%

### Intimidation Factor

Physical teams reduce opponent shooting confidence (**LINEAR** scaling):

```
intimidation = (avg_team_PHYS - 75) / 150
goal_prob *= (1 - intimidation)
```

**Examples**:
- 75 avg PHYS = no intimidation (baseline)
- 82 avg PHYS = -5% opponent goals
- 90 avg PHYS = -10% opponent goals

Intimidating player types contribute more:
- Power Forward: +20%, Power Defense: +18%, Defensive: +10%, Gamer: +5%
- Sniper: -25%, Playmaker: -20%, Offensive D: -15%

### Leadership System

All leadership bonuses are **LINEAR** (no cutoffs):

**Line Chemistry** (based on max team leadership):
```
chemistry_bonus = (max_LEAD - 70) / 600
```
- 70 LEAD = no bonus
- 85 LEAD = +2.5%
- 100 LEAD = +5%

**Clutch Factor** (3rd period, OT, close games):
```
clutch_modifier = (max_LEAD - 70) / 500
```
- 70 LEAD = no bonus
- 90 LEAD = +4%
- 100 LEAD = +6%

**Playoff Intensity**:
```
playoff_lead_bonus = (avg_team_LEAD - 75) / 500
```
- 75 avg LEAD = no bonus
- 85 avg LEAD = +2%
- 95 avg LEAD = +4%

**Low Leadership Penalty** (team avg below 70):
```
penalty = (70 - avg_LEAD) / 200
```
- 60 avg LEAD = -5% penalty

### Net-Front Presence

Physical players improve rebound goal chances (scaled by ice time):
- Power Forward: +20% when on ice
- Power Defense: +12%
- Gamer: +8% (compete level)
- Total capped at +35%

### Goal Probability Calculation

```
goal_prob = base_xG 
          × shooter_modifier      (OFF / 80)
          × player_type_modifier  (sniper: 1.25, etc.)
          × shot_quality_modifier (sniper: 1.15 for HD)
          × goalie_modifier       (85 / goalie_rating)
          × team_rating_modifier  (attack / 80)
          × intimidation_modifier (1 - opponent_intimidation)
          × leadership_modifier   (chemistry + clutch + playoff)
          × netfront_modifier     (for rebounds)
          × style_modifiers       (rebound_goals, etc.)
          × playoff_modifier      (1.05 for high-danger)
```

**Example calculations:**

| Scenario | Calculation | Result |
|----------|-------------|--------|
| 1st liner (95 OFF, sniper) vs 80 goalie, high-danger | 0.20 × 1.19 × 1.20 × 1.0 | 28.6% |
| 4th liner (70 OFF) vs 95 goalie, low-danger | 0.03 × 0.875 × 0.89 | 2.3% |

### Consistency (CONST) Implementation

Each game, player performance varies based on consistency:

```
variance = random(-0.20, 0.20) × (1 - consistency/100)
adjusted_off = OFF × (1 + variance)
```

**Examples:**
- 95 CONST player: max ±1% variance per game
- 60 CONST player: max ±8% variance per game

### Goalie Save Probability

Individual goalie rating directly affects saves:

```
goalie_modifier = 85 / goalie_rating
```

| Rating | Modifier | Effect |
|--------|----------|--------|
| 95 | 0.89 | 11% fewer goals allowed |
| 85 | 1.00 | Baseline |
| 75 | 1.13 | 13% more goals allowed |

### Assist Attribution

- 65% chance of assist on each goal
- Assists go to linemates (same line)
- Weighted by player type assist modifier (playmakers favored)

### Physical Stats

**Hits:**
```
hit_chance = (PHYS / 100) × 0.05 × style_physical_bonus × type_modifier
hits = sum(50 opportunities × hit_chance)
```

**Blocks:**
```
block_chance = (DEF / 100) × 0.03 × type_modifier
blocks = sum(40 opportunities × block_chance)
```

## Expected Season Statistics (82 games)

### Forwards

| Line | OFF | Type | Goals | Assists | Points |
|------|-----|------|-------|---------|--------|
| 1st C | 95 | Playmaker | 35-45 | 65-80 | 100-120 |
| 1st W | 92 | Sniper | 45-55 | 40-50 | 90-105 |
| 2nd C | 85 | Two-Way | 25-35 | 40-55 | 70-85 |
| 3rd C | 78 | Grinder | 12-18 | 20-30 | 35-45 |
| 4th C | 70 | Grinder | 4-8 | 8-12 | 12-20 |

### Defensemen

| Pair | OFF | Type | Goals | Assists | Points |
|------|-----|------|-------|---------|--------|
| 1st | 85 | Offensive | 12-18 | 50-65 | 65-80 |
| 2nd | 78 | Two-Way | 6-10 | 30-40 | 38-50 |
| 3rd | 70 | Defensive | 1-4 | 8-14 | 10-18 |

### Goalies

| Type | Rating | SV% | GAA |
|------|--------|-----|-----|
| Elite | 95 | .915-.925 | 2.3-2.6 |
| Starter | 85 | .905-.915 | 2.7-3.0 |
| Backup | 80 | .890-.905 | 3.0-3.4 |

### Point Distribution Ratios

- 1st line vs 4th line: ~6-7x
- Top pair D vs 3rd pair D: ~5x
- Snipers lead in goals
- Playmakers lead in assists

## Overtime & Shootout

### 3-on-3 Overtime
- Uses top 2 lines only
- 50% higher xG (more open ice)
- 15 plays per OT period
- Sudden death

### Shootout
- 30% base scoring chance
- Modified by shooter OFF and player type
- 3 rounds then sudden death

## Time on Ice Tracking

TOI is calculated and stored for each player:
- Based on line assignment percentages
- Stored in seconds (3600 = full game)
- OT adds proportional TOI for active players

## Constants

```rust
HOME_ICE_ADVANTAGE: 1.05       // +5% boost
PLAYOFF_PHYS_BOOST: 1.20       // +20% physicality
BASE_PLAYS_PER_PERIOD: 50      // ~50 plays per period
SHOT_ATTEMPT_RATE: 0.25        // 25% of plays result in shots
OT_PLAYS: 10                   // 5-min OT plays
OT_SHOT_RATE: 0.35             // 35% shot rate in 3-on-3 OT
```

### xG Base Values (reduced 20% from original)
```rust
HighDanger:   0.16  // Slot, odd-man rush, rebounds
MediumDanger: 0.065 // Between circles, screened shots
LowDanger:    0.024 // Perimeter shots
```

### Expected Per-Game Stats
- Shots per team: ~37 (50 plays × 3 periods × 0.25)
- Goals per team: ~2.6 (with xG averaging ~6.5%)
- Goalie games: 60/40 split between starter and backup

### Assist Distribution
- ~5% unassisted goals
- ~25% one assist (primary only)
- ~70% two assists (primary + secondary)
- Expected: League-wide assists > goals (realistic)

### Position-Based Assist Logic
- **Primary Assist**: 75% same position type (F→F, D→D), 25% crossover
- **Secondary Assist**: 50% crossover (D-man often starts the play)
- **D-man weighting**: ice_time^2.0 for primary, ice_time^2.5 for secondary
  - Creates realistic gap: Top pair ~60+ assists, 3rd pair ~15-20 assists
- **Forward weighting**: ice_time^1.3 for primary, ice_time^1.5 for secondary

### Player Type Assist Modifiers
```rust
Playmaker:      1.50  // Elite passers
Offensive:      1.40  // Offensive D-men  
Two-Way:        1.15
Gamer:          1.10  // Smart plays
Power Forward:  1.05
Power Defense:  1.00
Sniper:         0.75  // Finishers, not passers
Defensive:      0.60  // Stay-at-home D
```

### Physical Stats (Hits & Blocks)
- **Ice time scaling**: Opportunities proportional to TOI (top line ~20, 4th ~8)
- **Hits modifiers by type**:
  - Power Forward: 1.40, Power Defense: 1.35, Defensive: 1.15, Gamer: 1.10
  - Offensive D: 0.75, Playmaker: 0.60, Sniper: 0.55 (avoid contact)
- **Blocks modifiers by type**:
  - Defensive: 1.40, Power Defense: 1.30, Two-Way: 1.15, Gamer: 1.10
  - Offensive D: 0.55, Playmaker: 0.50, Sniper: 0.45 (don't sacrifice body)
- **Position modifier**: D-men block 1.5x more than forwards

### Turnover Stats (Takeaways & Giveaways)

**Takeaways** (caused by high DEF):
```
takeaway_chance = (DEF / 100) × 0.02 × ice_time × type_modifier × position_modifier
```
- Defensive: 1.40x, Two-Way: 1.25x, Power Defense: 1.15x, Gamer: 1.12x
- Playmaker: 1.10x (stick awareness)
- Sniper: 0.75x, Offensive D: 0.80x
- D-men: 1.30x position bonus

**Giveaways** (caused by low CONST):
```
giveaway_chance = ((1 - CONST/100) × 0.03 + 0.005) × ice_time × type_modifier
```
- Offensive D: 1.15x (risk-taking), Playmaker: 1.10x (handles puck more)
- Gamer: 0.90x, Two-Way: 0.85x, Power Defense: 0.80x
- Defensive: 0.70x (safe plays)

**Expected Season Stats**:
- Elite defensive player: 80-120 takeaways
- Sniper/Playmaker: 20-40 takeaways
- High-CONST player (95): 15-25 giveaways
- Low-CONST player (70): 40-60 giveaways

## Performance

- Single game simulation: < 50ms
- Full season (82 games × 12 teams): < 30 seconds
- Statistical variance: Controlled by CONST rating
