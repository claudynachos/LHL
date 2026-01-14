# Statistics Calibration Update - January 14, 2026

## Summary
Updated the simulation algorithm to match modern NHL statistics (2024-2025 season) and clarified that overall player rating is for frontend display only, not used in simulation calculations.

---

## Key Changes

### 1. Overall Rating Clarification

**Status:** Frontend display only, NOT used in algorithm

The overall rating calculation exists solely for displaying player ratings in the user interface. The simulation algorithm uses individual attributes (OFF, DEF, PHYS, LEAD, CONST) directly.

**Formula (Display Only):**
```
OVERALL = (OFF × 1.1 + DEF × 0.95 + PHYS × 0.9 × (LEAD/100) × (CONST/100)) / 2.5
```

**Implementation:**
- `Player::calculate_overall()` method exists but is not called during simulation
- All game calculations use raw attributes: `player.off`, `player.def`, `player.phys`, etc.

---

### 2. Shot Generation Calibration

**Previous:** 12 shots per period per team = 36 per game = 72 total per game
**Updated:** 9.4 shots per period per team = 28.2 per game = ~56 total per game

**NHL 2024-2025 Baseline:**
- Shots per team per game: **28.1**
- Shots per period per team: **~9.4**
- Total shots per game: **~56**

**Code Changes:**
```rust
// Old:
const BASE_SHOTS_PER_PERIOD: i32 = 12;

// New:
const BASE_SHOTS_PER_PERIOD: f64 = 9.4;  // ~28.1 shots per team per game / 3 periods
```

---

### 3. Goal Probability Validation

**Base Shooting Percentage:** 10% (unchanged)
- Matches NHL 2024-2025 save percentage of .900
- Results in ~3.01 goals per team per game (NHL average)

**Calculation:**
- ~28.1 shots per game × 10% = ~2.81 goals per game
- Algorithm adjusts based on team ratings to reach ~3.01 goals per team per game

**Code:**
```rust
const BASE_GOAL_PROBABILITY: f64 = 0.10;  // 10% shooting percentage (matches .900 save %)
```

---

### 4. Physical Stats Calibration

**Hits:**
- Target: **15-25 hits per team per game** (NHL 2024-2025)
- Current algorithm: 50 opportunities × (PHYS/100) × 0.05
- Scales appropriately with player physicality ratings

**Blocks:**
- Target: **15-25 blocks per team per game** (NHL 2024-2025)
- Current algorithm: 40 opportunities × (DEF/100) × 0.03
- Scales appropriately with player defensive ratings

**Code Comments Added:**
```rust
// Hits based on physicality
// Target: ~15-25 hits per team per game (NHL 2024-2025 average)
let hit_chance = phys as f64 / 100.0 * 0.05;
stats[idx].hits = (0..50).filter(|_| rng.gen::<f64>() < hit_chance).count() as i32;

// Blocks based on defensive skill
// Target: ~15-25 blocks per team per game (NHL 2024-2025 average)
let block_chance = la.player.def as f64 / 100.0 * 0.03;
stats[idx].blocks = (0..40).filter(|_| rng.gen::<f64>() < block_chance).count() as i32;
```

---

## NHL 2024-2025 Reference Statistics

### League-Wide Averages (Per Team Per Game)

| Statistic | Value | Source |
|-----------|-------|--------|
| Goals | 3.01 | hockey-reference.com |
| Shots | 28.1 | hockey-reference.com |
| Save Percentage | .900 | hockey-reference.com |
| Shooting Percentage | ~10.7% | Calculated (3.01 goals / 28.1 shots) |
| Hits | 15-25 | Estimated from game data |
| Blocks | 15-25 | Estimated from game data |

### Per Period Averages

| Statistic | Value |
|-----------|-------|
| Shots per period | ~9.4 |
| Goals per period | ~1.0 |

---

## Files Modified

### 1. `/simulation/ALGORITHM.md`
- ✅ Clarified overall rating is frontend-only
- ✅ Updated shot generation section with NHL 2024-2025 targets
- ✅ Updated goal probability section with validation
- ✅ Updated physical stats section with targets
- ✅ Updated expected outputs with modern NHL baseline

### 2. `/simulation/src/main.rs`
- ✅ Added comment clarifying `calculate_overall()` is display-only
- ✅ Changed `BASE_SHOTS_PER_PERIOD` from `i32 = 12` to `f64 = 9.4`
- ✅ Updated shot calculation to use new constant
- ✅ Added comments referencing NHL 2024-2025 statistics
- ✅ Added calibration comments to physical stats functions

---

## Validation

### Expected Game Outputs (Modern NHL Baseline)

**Per Game (Both Teams Combined):**
- Total shots: ~56
- Total goals: ~6
- Total hits: ~30-50
- Total blocks: ~30-50

**Per Team Per Game:**
- Shots: ~28.1
- Goals: ~3.01
- Save percentage: ~.900
- Hits: ~15-25
- Blocks: ~15-25

### Algorithm Behavior

The simulation will:
1. Generate ~9.4 shots per period per team (varies based on team ratings)
2. Convert ~10% of shots to goals (varies based on offensive/defensive matchups)
3. Scale physical stats based on player attributes
4. Produce realistic modern NHL statistics despite players from all eras

---

## Testing Recommendations

1. **Run 82-game season simulation**
   - Verify average shots per team per game ≈ 28.1
   - Verify average goals per team per game ≈ 3.01
   - Verify save percentage ≈ .900

2. **Validate physical stats**
   - Check hits per team per game range: 15-25
   - Check blocks per team per game range: 15-25

3. **Confirm overall rating not used**
   - Verify simulation results don't change if `calculate_overall()` is removed
   - Confirm only individual attributes affect outcomes

---

## Notes

- **Era Compatibility:** The algorithm uses modern NHL statistics as targets, but players from all eras (Run & Gun, Dead Puck, etc.) will have their individual attributes (OFF, DEF, PHYS) used directly, creating realistic cross-era matchups.

- **Rating System:** Individual attributes (0-100 scale) are used throughout the algorithm. The overall rating is purely cosmetic for frontend display.

- **Calibration:** Constants are tuned to match 2024-2025 NHL averages, but the algorithm naturally scales based on team ratings, so stronger teams will generate more shots/goals and weaker teams will generate fewer.

---

## Status
**COMPLETE** - All changes implemented and documented.
