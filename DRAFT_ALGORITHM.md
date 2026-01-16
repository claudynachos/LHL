# Draft Algorithm Documentation

## Overview
This document explains the AI draft strategy used in the hockey simulation game. The algorithm uses a simple scoring system that evaluates all available players and coaches based on their overall rating, team needs, and roster balance.

## Draft Structure

- **Total Rounds**: 21 rounds (20 players + 1 coach per team)
- **Format**: Snake draft (round 1 uses lottery order, then alternates)
- **Roster Targets**: 
  - 4 Centers (C)
  - 4 Left Wings (LW)
  - 4 Right Wings (RW)
  - 6 Defensemen (D)
  - 2 Goalies (G)
  - 1 Coach

## Simple Scoring System

The algorithm evaluates all available options (players and coaches) using a unified scoring system. No hardcoded round restrictions or position multipliers.

### Player Scoring

Each player is scored using:

```
score = overall_rating + position_bonus + balance_bonus
```

**Components:**

1. **Overall Rating** (base score)
   - Uses `calculate_overall()` which already includes:
     - For skaters: `(OFF × 1.1 + DEF × 0.95 + PHYS × 0.9 × (LEAD/100) × (CONST/100)) / 2.5`
     - For goalies: Uses their gen rating directly
   - Consistency is already factored into the overall rating

2. **Position Bonus**
   - `position_bonus = deficit × 5`
   - Where `deficit = target - current_count` for that position
   - Small bonus to encourage filling needed positions
   - Example: If team has 2 defensemen and needs 6, deficit = 4, bonus = 20

3. **Balance Bonus**
   - Encourages team style balance (offensive, defensive, physical)
   - If team average in a category is below 75, and player excels (>75) in that category:
     - +2 bonus per matching category
   - Helps build well-rounded teams

### Coach Scoring

Coaches are scored simply:
```
score = coach_rating
```

Coaches are evaluated alongside players and can be selected at any time if they represent the best available option.

## Selection Logic

1. **Score all available players** using the formula above
2. **Score all available coaches** (if team doesn't have one) using their rating
3. **Select the option with the highest score**

This means:
- Goalies are evaluated like any other player (no early exclusion)
- Coaches can be selected at any round if they're the best option
- No artificial restrictions based on round number
- Best player available is prioritized, with small adjustments for team needs and balance

## Key Features

1. **No Hardcoded Rules**: No round-based restrictions or position multipliers
2. **Overall Rating Priority**: Best players are prioritized, with consistency already factored in
3. **Team Needs Consideration**: Small bonus for positions the team needs
4. **Style Balance**: Encourages balanced rosters (offensive, defensive, physical)
5. **Flexible Coach Selection**: Coaches evaluated alongside players, can be picked anytime

## Example Scoring

**Scenario**: Team has 3 forwards, 2 defensemen, 0 goalies

**Available Options:**
- Player A: Overall 85, Position: D, OFF: 80, DEF: 90, PHYS: 75
  - Base: 85
  - Position bonus: (6-2) × 5 = 20
  - Balance bonus: +2 (team weak in defense, player strong)
  - **Total: 107**

- Player B: Overall 90, Position: C, OFF: 95, DEF: 85, PHYS: 80
  - Base: 90
  - Position bonus: (4-3) × 5 = 5
  - Balance bonus: +2 (team weak in offense, player strong)
  - **Total: 97**

- Goalie C: Overall 88, Position: G
  - Base: 88
  - Position bonus: (2-0) × 5 = 10
  - Balance bonus: 0 (goalies don't get style bonus)
  - **Total: 98**

- Coach D: Rating 92
  - **Total: 92**

**Result**: Player A (defenseman) is selected with score 107, as the team needs defensemen and the player complements the team's defensive weakness.

## Fallback Logic

If no players or coaches are available:
1. Select any remaining available player
2. Ensures the draft always completes successfully
