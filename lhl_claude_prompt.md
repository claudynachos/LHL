# Legend Hockey League (LHL) - Prompt pour Claude Code

## Context & Objective
Build a web-based hockey simulation game featuring historical NHL legends. Users draft teams and simulate 20-25 year seasons with detailed statistics tracking.

## Tech Stack (Non-negotiable)
- **Frontend**: React or nextjs
- **Backend**: Python Flask
- **Simulation Engine**: Rust (performance-critical calculations)
- **Database**: SQLite (simplicity priority) or PostgreSQL if multi-user requires it
- **Auth**: Simple JWT-based authentication
- **Deployment**: Vercel
- **Important**: Set up the entire project structure with all necessary configs so I can run it immediately without additional tool setup

## Data Files Provided
- Excel file: Player stats (name, position, OFF, DEF, PHYS, LEAD, CONST skills)
- Excel file: Goalie stats (separate sheet)
- CSV file: Coach data

## Core Features - MVP

### 1. Home Page
- Clean, minimal design
- Two primary actions: "Continue Simulation" or "Start New Simulation"
- User profile settings (billing integration placeholder, account management)
- Brief explanation of app functionality

### 2. New Simulation Setup (Single Page Onboarding)
- Simulation length: 20-25 years (dropdown)
- Number of teams: 4, 6, 8, 10, or 12 (dropdown)
- Game mode: Solo (vs AI) or Multiplayer (for V2, just add UI placeholder)

### 3. Draft System
**Critical Rules:**
- One-time initial draft only (no yearly drafts)
- Snake draft pattern:
  - Round 1: Team 1 → Team N
  - Round 2: Team N → Team 1
  - Round 3: Team 1 → Team N
  - Continue until 20 players + 1 coach per team
- Undrafted players become free agents

### 4. Main Simulation Interface

**Left Sidebar Menu:**
- Calendar (current date, game schedule)
- Stats submenu:
  - Season Stats
  - All-Time Stats
  - Trophies
  - Lines Configuration
  - League Standings

**Center Action Panel:**
- "Simulate to Playoffs" button
- "Simulate Round 1", "Round 2", etc.
- "Simulate to End of Playoffs" (if team eliminated)
- "Simulate to Next Season" button
- Current game/playoff status display

**Roster Management:**
- Lines editor (drag-and-drop or select players)
- Free agent signing (end of season only for MVP)
- Trade module: V2 feature (add placeholder UI)

### 5. Lines Configuration Page
Display format:
```
Forward Lines:
LW - C - RW   (Line 1)
LW - C - RW   (Line 2)
LW - C - RW   (Line 3)
LW - C - RW   (Line 4)

Defense Pairs:
LD - RD   (Pair 1)
LD - RD   (Pair 2)
LD - RD   (Pair 3)

Goalies:
G1 (Starter)
G2 (Backup)

Coach: [Name]
```

**Important:** Allow viewing other teams' lines in the league

### 6. League Structure

**Conference Alignment** (teams added based on league size):

**Eastern Conference:**
1. MTL (4+ teams)
2. BOS (4+ teams)
3. TOR (6+ teams)
4. PHI (8+ teams)
5. PIT (10+ teams)
6. QC (12 teams)

**Western Conference:**
1. DET (4+ teams)
2. CHI (4+ teams)
3. NYR (6+ teams)
4. LA (8+ teams)
5. EDM (10+ teams)
6. NYI (12 teams)

**Playoff Format:**
- 4 teams: All 4 make playoffs
- 6 teams: Top 4 make playoffs
- 8 teams: All 8 make playoffs
- 10 teams: Top 8 make playoffs
- 12 teams: Top 8 make playoffs
- All series: Best of 7 games
- Home team advantage: Slight statistical boost

## Simulation Engine Requirements

### Ice Time Distribution (% of game)
```
Line 1: 35%
Line 2: 30%
Line 3: 20%
Line 4: 15%

Defense Pair 1: 45%
Defense Pair 2: 35%
Defense Pair 3: 20%

Goalie 1: 60%
Goalie 2: 40%
```

### Skill Weightings [OFF, DEF, PHYS]
```
Line 1: [50, 30, 20]
Line 2: [40, 40, 20]
Line 3: [25, 50, 25]
Line 4: [20, 40, 40]

Defense Pair 1: [40, 30, 30]
Defense Pair 2: [30, 40, 30]
Defense Pair 3: [10, 50, 40]

Goalies: Use separate goalie-specific stats
```

### Player Skills (0-100 scale)
- **OFF** (Offense): Scoring ability
- **DEF** (Defense): Defensive play quality
- **PHYS** (Physicality): Physical play, more impactful in playoffs (temporarily reduces opponent skills when delivering hits)
- **LEAD** (Leadership): Boosts teammates' performance
- **CONST** (Consistency): Reduces season-to-season variation (higher = more reliable performance)

### Simulation Rules
- **No injuries** (MVP version)
- Game simulation should produce realistic NHL-style statistics (goals, assists, +/-, shots, hits, blocked shots, etc.)
- Playoff games: Increase PHYS skill impact by 20%
- Coach impact: Apply small modifiers to team performance based on coach ratings

### Critical Requirement
**Provide detailed documentation** explaining:
1. How the Rust simulation engine calculates game outcomes
2. Algorithm for determining goals/assists based on player skills
3. How line weightings and skill distributions affect results
4. Mathematical formulas used for game simulation

## Admin Panel (Simple)
- User management (view, suspend, delete)
- Analytics dashboard:
  - Total users
  - Active simulations
  - Most popular teams/players
- Database health metrics

## UI/UX Inspiration
- Reference: EA Sports NHL 2026 aesthetic (but simpler and cleaner)
- Design screenshots attached (reference for visual style)
- Modern, intuitive interface
- Fast navigation between sections
- Responsive design (mobile-first for web version)

## Project Structure Requirements
1. Set up complete development environment with one command
2. Include README with:
   - Installation steps
   - How to run locally
   - How to deploy to Vercel
   - API documentation
3. Seed database with provided Excel/CSV data automatically
4. Include sample test data for quick testing

## Out of Scope for MVP (V2 Features)
- Multiplayer synchronization (add UI placeholders)
- In-season trades
- Mobile app (iOS/Android)
- Advanced analytics/visualizations
- Player progression system beyond basic CONST skill

## Success Criteria
- Can draft a team and simulate 1 full season in under 5 clicks
- Simulation produces statistically realistic results
- All stats pages load in <1 second
- Clean, bug-free user experience
- Deployable to Vercel without additional configuration

---

## Action Items for Claude Code
1. Create complete project structure with all necessary files
2. Implement Rust simulation engine with clear documentation
3. Build Flask API with all endpoints
4. Create React frontend with routing and state management
5. Set up database schema and seed scripts
6. Configure Vercel deployment
7. Write comprehensive README
8. Include unit tests for simulation engine logic

**Start with the simulation engine first** - this is the core of the application and should be thoroughly tested before building the UI around it.