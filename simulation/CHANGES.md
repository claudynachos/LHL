# Simulation Algorithm Updates - January 14, 2026

## Summary
Updated both the algorithm documentation and Rust implementation to reflect:
1. **Overall Player Rating Calculation** - Added formula based on spreadsheet
2. **Goalie Game Assignment** - Changed from % ice time to % of games played

---

## 1. Overall Rating Calculation

### Formula
```
OVERALL = (OFF × 1.1 + DEF × 0.95 + PHYS × 0.9 × (LEAD/100) × (CONST/100)) / 2.5
```

### Explanation
- **OFF** is weighted at 1.1 (offense slightly more important)
- **DEF** is weighted at 0.95
- **PHYS** is weighted at 0.9 and modified by Leadership and Consistency as percentage multipliers
- LEAD and CONST act as modifiers (0.0-1.0 scale) that scale the physicality contribution
- Result normalized by dividing by 2.5

### Example
Player: OFF=115, DEF=82, PHYS=88, LEAD=85, CONST=92
- OFF component: 115 × 1.1 = 126.5
- DEF component: 82 × 0.95 = 77.9
- PHYS component: 88 × 0.9 × 0.85 × 0.92 = 61.9
- **OVERALL = (126.5 + 77.9 + 61.9) / 2.5 = 106.5**

### Implementation (Rust)
```rust
impl Player {
    fn calculate_overall(&self) -> f64 {
        let off_component = self.off as f64 * 1.1;
        let def_component = self.def as f64 * 0.95;
        let phys_component = self.phys as f64 * 0.9 
            * (self.lead as f64 / 100.0) 
            * (self.consistency as f64 / 100.0);
        
        (off_component + def_component + phys_component) / 2.5
    }
}
```

---

## 2. Goalie Game Assignment Changes

### Previous Behavior
- **G1 (Starter)**: Played 60% of game time
- **G2 (Backup)**: Played 40% of game time
- Both goalies could "share" a single game
- Team rating weighted both goalies proportionally

### New Behavior
- **G1 (Starter)**: Plays in 60% of games (full game when selected)
- **G2 (Backup)**: Plays in 40% of games (full game when selected)
- **One goalie per game** - selected at start of simulation
- Selected goalie plays the **entire game** (no splitting)

### Implementation Changes

#### Constants Updated
```rust
// Old:
const GOALIE_TIME: [f64; 2] = [0.60, 0.40];

// New:
const GOALIE_GAME_PROBABILITY: [f64; 2] = [0.60, 0.40];
```

#### New Function: `select_goalie()`
```rust
fn select_goalie(team: &Team, rng: &mut ThreadRng) -> usize {
    // Find goalie positions in team lines
    let goalie_indices: Vec<usize> = team.lines.iter()
        .enumerate()
        .filter(|(_, la)| la.line_type == "goalie")
        .map(|(idx, _)| idx)
        .collect();
    
    // Select based on probability (60% G1, 40% G2)
    let rand_val: f64 = rng.gen();
    if rand_val < GOALIE_GAME_PROBABILITY[0] && goalie_indices.len() > 0 {
        goalie_indices[0] // Starter (G1)
    } else if goalie_indices.len() > 1 {
        goalie_indices[1] // Backup (G2)
    } else {
        goalie_indices[0] // Only one goalie available
    }
}
```

#### Updated `simulate_game()`
- Now selects goalies at the start of the game
- Passes goalie indices to all period simulations

```rust
// Select goalies for this game (60% G1, 40% G2)
let home_goalie_idx = select_goalie(&input.home_team, &mut rng);
let away_goalie_idx = select_goalie(&input.away_team, &mut rng);

// Calculate ratings with selected goalie
let home_rating = calculate_team_rating(&input.home_team, home_goalie_idx, true, input.is_playoff);
let away_rating = calculate_team_rating(&input.away_team, away_goalie_idx, false, input.is_playoff);
```

#### Updated `calculate_team_rating()`
- Now accepts `goalie_idx` parameter instead of calculating weighted average
- Uses only the selected goalie's rating

```rust
// Use the selected goalie's rating (plays full game)
if goalie_idx < team.lines.len() && team.lines[goalie_idx].line_type == "goalie" {
    let goalie = &team.lines[goalie_idx].player;
    let goalie_rating = (goalie.off + goalie.def + goalie.phys) as f64 / 3.0;
    total_rating += goalie_rating * 0.3;  // Goalies have 30% weight
    weight_sum += 0.3;
}
```

#### Updated `simulate_period()`
- Accepts `home_goalie_idx` and `away_goalie_idx` parameters
- Tracks stats only for the selected goalie
- Properly attributes saves and goals against to active goalie

```rust
// Track goalie stats using the selected goalie index
if away_goalie_idx < away_stats.len() {
    away_stats[away_goalie_idx].shots_against += 1;
    if is_goal {
        away_stats[away_goalie_idx].goals_against += 1;
    } else {
        away_stats[away_goalie_idx].saves += 1;
    }
}
```

#### Removed Functions
- `find_goalie_index()` - No longer needed since goalie is pre-selected

---

## 3. Documentation Updates

### Files Modified
1. **`simulation/ALGORITHM.md`**
   - Updated Section 2: Added Overall Rating Calculation with formula and example
   - Updated lines 22-25: Changed goalie ice time to game percentage
   - Updated Section 4: Added note about active goalie per game
   - Updated Section 10: Added goalie game assignment details

2. **`simulation/src/main.rs`**
   - Added `Player::calculate_overall()` method (lines 65-74)
   - Updated goalie constants (line 93)
   - Added `select_goalie()` function (lines 204-220)
   - Modified `simulate_game()` to select goalies upfront (lines 157-161)
   - Modified `calculate_team_rating()` to use selected goalie (lines 222-276)
   - Modified `simulate_period()` signature and goalie tracking (lines 306-389)
   - Removed `find_goalie_index()` function

---

## Impact on Simulation Results

### Goalie Statistics
- **Before**: Both goalies could accumulate stats in same game (proportional to ice time)
- **After**: Only one goalie gets stats per game
- **Result**: More realistic goalie stats (Games Played, Save %, GAA)

### Team Rating Variance
- **Before**: Team rating was averaged across both goalies every game
- **After**: Team rating varies game-to-game based on which goalie starts
- **Result**: Teams with strong starter vs weak backup will show more variance in performance

### Season Simulation
- Over an 82-game season:
  - Starter (G1) plays ~49 games
  - Backup (G2) plays ~33 games
  - Matches realistic NHL goalie usage patterns

---

## Testing Recommendations

1. **Unit Tests**
   - Verify `calculate_overall()` produces expected values
   - Test `select_goalie()` probability distribution over 1000+ trials
   - Ensure selected goalie index is valid

2. **Integration Tests**
   - Simulate 82-game season, verify goalie games played ratio
   - Check that only one goalie per game has stats > 0
   - Verify team rating changes based on goalie selection

3. **Validation**
   - Compare overall ratings to spreadsheet calculations
   - Verify goalie save percentages are realistic (.900-.930)
   - Check games played distribution matches 60/40 split

---

## Files Changed
- ✅ `/simulation/ALGORITHM.md` - Documentation updated
- ✅ `/simulation/src/main.rs` - Rust implementation updated
- ✅ `/simulation/CHANGES.md` - This summary document (NEW)

## Status
**COMPLETE** - All changes implemented and documented.

To compile and test:
```bash
cd simulation
cargo build --release
cargo test
```
