"""Game simulation and scheduling service"""
from extensions import db
from models.simulation import Simulation
from models.team import Team
from models.game import Game, PlayerStat, Standing, PlayoffSeries
from datetime import datetime, timedelta, date
import random
from services.simulation_service import simulate_game

def generate_season_schedule(simulation_id, season):
    """Generate schedule for a season with intra-conference preference"""
    # Check if schedule already exists for this season
    existing_games = Game.query.filter_by(
        simulation_id=simulation_id,
        season=season,
        is_playoff=False
    ).first()
    
    if existing_games:
        # Schedule already exists, return existing games
        return Game.query.filter_by(
            simulation_id=simulation_id,
            season=season,
            is_playoff=False
        ).all()
    
    teams = Team.query.filter_by(simulation_id=simulation_id).all()
    num_teams = len(teams)
    
    # Always 82 games per team (NHL standard)
    games_per_team = 82
    
    games = []
    start_date = date(1980 + season - 1, 10, 1)  # Start in October
    current_date = start_date
    
    # Organize teams by conference
    eastern_teams = [t for t in teams if t.conference == 'Eastern']
    western_teams = [t for t in teams if t.conference == 'Western']
    team_conference_map = {t.id: t.conference for t in teams}
    
    # Separate pairs into intra-conference and inter-conference
    intra_conference_pairs = []
    inter_conference_pairs = []
    
    for i, team1 in enumerate(teams):
        for j, team2 in enumerate(teams):
            if i < j:  # Avoid duplicates and self-pairs
                if team1.conference == team2.conference:
                    intra_conference_pairs.append((team1.id, team2.id))
                else:
                    inter_conference_pairs.append((team1.id, team2.id))
    
    # Calculate exact distribution to reach games_per_team
    # For 12 teams: 6 per conference
    # Each team has: 5 intra-conference opponents + 6 inter-conference opponents = 11 total
    # We want 82 games total per team
    # Strategy: favor intra-conference (more games vs same conference)
    
    num_intra_opponents = max(len(eastern_teams), len(western_teams)) - 1  # Teams in same conference - 1
    num_inter_opponents = min(len(eastern_teams), len(western_teams))  # Teams in other conference
    
    # Calculate exact games per opponent type
    # Formula: (intra_games * num_intra) + (inter_games * num_inter) = games_per_team
    # We want to favor intra, so let's set intra_games = inter_games + 1 (or more)
    
    # Start with equal distribution
    base_games = games_per_team // (num_intra_opponents + num_inter_opponents)
    remaining = games_per_team % (num_intra_opponents + num_inter_opponents)
    
    # Assign base games
    intra_games = base_games
    inter_games = base_games
    
    # Distribute remaining games to favor intra-conference
    # Give as many as possible to intra, then to inter if needed
    if remaining >= num_intra_opponents:
        # Give 1 extra to all intra opponents
        intra_games += 1
        remaining -= num_intra_opponents
        # Give remaining to inter
        if remaining > 0 and num_inter_opponents > 0:
            extra_per_inter = remaining // num_inter_opponents
            inter_games += extra_per_inter
            remaining -= (extra_per_inter * num_inter_opponents)
    else:
        # Give remaining games to intra (not enough for all)
        # We'll handle these in the remaining games distribution
        pass
    
    # Verify calculation matches target exactly
    total_from_base = (intra_games * num_intra_opponents) + (inter_games * num_inter_opponents)
    
    # If calculation doesn't match exactly, adjust
    if total_from_base != games_per_team:
        # Adjust inter_games to reach exact target
        diff = games_per_team - total_from_base
        if diff != 0 and num_inter_opponents > 0:
            adjustment = diff // num_inter_opponents
            inter_games += adjustment
            # Recalculate to verify
            total_from_base = (intra_games * num_intra_opponents) + (inter_games * num_inter_opponents)
    
    # At this point, total_from_base should equal games_per_team exactly
    # No remaining games should be needed if calculation is correct
    
    matchups = []
    
    # Add intra-conference games (more games vs same conference)
    for home_id, away_id in intra_conference_pairs:
        for k in range(intra_games):
            if k % 2 == 0:
                matchups.append((home_id, away_id))
            else:
                matchups.append((away_id, home_id))
    
    # Add inter-conference games (fewer games vs other conference)
    for home_id, away_id in inter_conference_pairs:
        for k in range(inter_games):
            if k % 2 == 0:
                matchups.append((home_id, away_id))
            else:
                matchups.append((away_id, home_id))
    
    # Count games per team to verify and add any remaining games
    team_ids = [t.id for t in teams]
    games_per_team_count = {}
    for team_id in team_ids:
        games_per_team_count[team_id] = 0
    
    for home_id, away_id in matchups:
        games_per_team_count[home_id] += 1
        games_per_team_count[away_id] += 1
    
    # Check if we need to add more games (use actual count)
    # Verify all teams have the same number of games (should be exact if calculation is correct)
    remaining_games = {}
    all_teams_same = True
    expected_count = None
    
    for team_id in team_ids:
        current_count = games_per_team_count[team_id]
        if expected_count is None:
            expected_count = current_count
        elif current_count != expected_count:
            all_teams_same = False
        
        needed = games_per_team - current_count
        if needed > 0:
            remaining_games[team_id] = needed
        elif needed < 0:
            # Team has too many games - this shouldn't happen but log it
            print(f"WARNING: Team {team_id} has {current_count} games, expected {games_per_team}")
    
    # Only run remaining distribution if teams don't already have exactly games_per_team
    if remaining_games and sum(remaining_games.values()) > 0:
        # Prefer intra-conference pairs for remaining games
        random.shuffle(intra_conference_pairs)
        random.shuffle(inter_conference_pairs)
        prioritized_pairs = intra_conference_pairs + inter_conference_pairs
        
        # Keep adding games until all teams have their remaining games
        # Only add exactly what's needed based on actual counts
        max_iterations = games_per_team * num_teams  # Safety limit (should be much less)
        iterations = 0
        
        while sum(remaining_games.values()) > 0 and iterations < max_iterations:
            iterations += 1
            made_progress = False
            
            # Try intra-conference pairs first, then inter-conference
            for home_id, away_id in prioritized_pairs:
                if remaining_games[home_id] > 0 and remaining_games[away_id] > 0:
                    if random.random() < 0.5:
                        matchups.append((home_id, away_id))
                    else:
                        matchups.append((away_id, home_id))
                    remaining_games[home_id] -= 1
                    remaining_games[away_id] -= 1
                    made_progress = True
                    if sum(remaining_games.values()) == 0:
                        break
            
            if sum(remaining_games.values()) == 0:
                break
                
            if not made_progress:
                # If we can't find pairs where both need games, 
                # add games for any team that still needs them
                for team_id in team_ids:
                    if remaining_games[team_id] > 0:
                        # Prefer same conference opponents
                        team_conf = team_conference_map[team_id]
                        same_conf_opponents = [t.id for t in teams if t.conference == team_conf and t.id != team_id]
                        other_conf_opponents = [t.id for t in teams if t.conference != team_conf]
                        
                        # Try same conference first
                        opponents = same_conf_opponents + other_conf_opponents
                        for opponent_id in opponents:
                            if random.random() < 0.5:
                                matchups.append((team_id, opponent_id))
                            else:
                                matchups.append((opponent_id, team_id))
                            remaining_games[team_id] -= 1
                            made_progress = True
                            break
                        if made_progress:
                            break
    
    # Shuffle and distribute across season
    random.shuffle(matchups)
    
    for home_id, away_id in matchups:
        game = Game(
            simulation_id=simulation_id,
            season=season,
            date=current_date,
            home_team_id=home_id,
            away_team_id=away_id,
            is_playoff=False,
            simulated=False
        )
        games.append(game)
        
        # Advance date (games every 2-3 days on average)
        current_date += timedelta(days=random.choice([2, 2, 3, 3, 4]))
    
    # Save all games
    for game in games:
        db.session.add(game)
    
    db.session.commit()
    return games

def simulate_season_to_playoffs(simulation_id):
    """Simulate all regular season games"""
    simulation = Simulation.query.get(simulation_id)
    season = simulation.current_season
    
    # Get or create schedule
    games = Game.query.filter_by(
        simulation_id=simulation_id,
        season=season,
        is_playoff=False
    ).all()
    
    if not games:
        games = generate_season_schedule(simulation_id, season)
    
    # Initialize standings
    initialize_standings(simulation_id, season)
    
    # Simulate all regular season games
    simulated_count = 0
    commit_interval = 3  # Commit every 3 games to allow progress tracking
    unsimulated_games = [g for g in games if not g.simulated]
    total_to_simulate = len(unsimulated_games)
    
    for idx, game in enumerate(unsimulated_games):
        result = simulate_game(game.home_team_id, game.away_team_id, False)
        save_game_result(game, result)
        update_standings(game, result)
        simulated_count += 1
        
        # Commit periodically to allow progress tracking
        if simulated_count % commit_interval == 0 or simulated_count == total_to_simulate:
            db.session.commit()
    
    # Update simulation status
    simulation.status = 'season_end'
    simulation.current_date = games[-1].date if games else simulation.current_date
    db.session.commit()
    
    return {
        'message': f'Simulated {simulated_count} regular season games',
        'season': season,
        'status': 'season_end'
    }

def simulate_playoff_round(simulation_id, round_num):
    """Simulate a playoff round"""
    simulation = Simulation.query.get(simulation_id)
    season = simulation.current_season
    
    # Get playoff matchups
    from services.league_service import get_playoff_teams
    num_playoff_teams = get_playoff_teams(simulation.num_teams)
    
    # Get standings to determine playoff teams
    standings = Standing.query.filter_by(
        simulation_id=simulation_id,
        season=season
    ).order_by(Standing.points.desc()).limit(num_playoff_teams).all()
    
    playoff_teams = [s.team_id for s in standings]
    
    # Generate or get playoff games
    playoff_games = Game.query.filter_by(
        simulation_id=simulation_id,
        season=season,
        is_playoff=True,
        playoff_round=round_num,
        simulated=False
    ).all()
    
    if not playoff_games:
        # Generate playoff matchups (best-of-7 series)
        playoff_games = generate_playoff_matchups(simulation_id, season, round_num, playoff_teams)
    
    # Simulate games
    for game in playoff_games:
        result = simulate_game(game.home_team_id, game.away_team_id, True)
        save_game_result(game, result)
    
    db.session.commit()
    
    return {
        'message': f'Simulated playoff round {round_num}',
        'games_simulated': len(playoff_games)
    }

def simulate_full_season(simulation_id):
    """Simulate entire season including playoffs"""
    # Simulate regular season
    result = simulate_season_to_playoffs(simulation_id)

    # Enter playoffs and simulate through completion
    enter_playoffs(simulation_id)
    while True:
        incomplete = PlayoffSeries.query.filter_by(
            simulation_id=simulation_id,
            season=Simulation.query.get(simulation_id).current_season,
            status='in_progress'
        ).count()
        if incomplete == 0:
            break

        series = PlayoffSeries.query.filter_by(
            simulation_id=simulation_id,
            season=Simulation.query.get(simulation_id).current_season,
            status='in_progress'
        ).order_by(PlayoffSeries.round.asc(), PlayoffSeries.id.asc()).first()
        if not series:
            break
        simulate_playoff_game(simulation_id, series.id)

    simulation = Simulation.query.get(simulation_id)
    completed_season = simulation.current_season
    
    # Award trophies for the completed season
    from services.trophy_service import award_trophies
    try:
        award_trophies(simulation_id, completed_season)
    except Exception as e:
        print(f"Error awarding trophies for season {completed_season}: {e}")
        # Continue even if trophy awarding fails
    
    simulation.current_season += 1
    simulation.status = 'season'
    
    # Generate schedule for the new season
    generate_season_schedule(simulation_id, simulation.current_season)
    
    db.session.commit()

    return {
        'message': 'Season completed',
        'next_season': simulation.current_season
    }

def initialize_standings(simulation_id, season):
    """Initialize standings for all teams"""
    teams = Team.query.filter_by(simulation_id=simulation_id).all()
    
    for team in teams:
        existing = Standing.query.filter_by(
            team_id=team.id,
            simulation_id=simulation_id,
            season=season
        ).first()
        
        if not existing:
            standing = Standing(
                team_id=team.id,
                simulation_id=simulation_id,
                season=season,
                wins=0,
                losses=0,
                ot_losses=0,
                points=0,
                goals_for=0,
                goals_against=0
            )
            db.session.add(standing)
    
    db.session.commit()

def save_game_result(game, result):
    """Save game result and player stats"""
    game.home_score = result['home_score']
    game.away_score = result['away_score']
    game.simulated = True
    
    # Save player stats
    for stat in result['home_stats']:
        player_stat = PlayerStat(
            game_id=game.id,
            player_id=stat['player_id'],
            team_id=game.home_team_id,
            goals=stat['goals'],
            assists=stat['assists'],
            shots=stat['shots'],
            hits=stat['hits'],
            blocks=stat['blocks'],
            plus_minus=stat['plus_minus'],
            time_on_ice=stat.get('time_on_ice', 0),
            takeaways=stat.get('takeaways', 0),
            giveaways=stat.get('giveaways', 0),
            saves=stat.get('saves', 0),
            goals_against=stat.get('goals_against', 0),
            shots_against=stat.get('shots_against', 0)
        )
        db.session.add(player_stat)
    
    for stat in result['away_stats']:
        player_stat = PlayerStat(
            game_id=game.id,
            player_id=stat['player_id'],
            team_id=game.away_team_id,
            goals=stat['goals'],
            assists=stat['assists'],
            shots=stat['shots'],
            hits=stat['hits'],
            blocks=stat['blocks'],
            plus_minus=stat['plus_minus'],
            time_on_ice=stat.get('time_on_ice', 0),
            takeaways=stat.get('takeaways', 0),
            giveaways=stat.get('giveaways', 0),
            saves=stat.get('saves', 0),
            goals_against=stat.get('goals_against', 0),
            shots_against=stat.get('shots_against', 0)
        )
        db.session.add(player_stat)

def update_standings(game, result):
    """Update standings after a game"""
    home_standing = Standing.query.filter_by(
        team_id=game.home_team_id,
        simulation_id=game.simulation_id,
        season=game.season
    ).first()
    
    away_standing = Standing.query.filter_by(
        team_id=game.away_team_id,
        simulation_id=game.simulation_id,
        season=game.season
    ).first()
    
    went_to_overtime = result.get('went_to_overtime', False)
    went_to_shootout = result.get('went_to_shootout', False)
    
    if home_standing:
        home_standing.goals_for += result['home_score']
        home_standing.goals_against += result['away_score']
        
        if result['home_score'] > result['away_score']:
            home_standing.wins += 1
            home_standing.points += 2
        elif result['home_score'] < result['away_score']:
            # Loss in regulation or OT
            if went_to_overtime and not game.is_playoff:
                # Overtime loss (OTL) - 1 point
                home_standing.ot_losses += 1
                home_standing.points += 1
            else:
                # Regulation loss
                home_standing.losses += 1
        # If tied, it's a playoff game that went to multiple OTs (handled above)
    
    if away_standing:
        away_standing.goals_for += result['away_score']
        away_standing.goals_against += result['home_score']
        
        if result['away_score'] > result['home_score']:
            away_standing.wins += 1
            away_standing.points += 2
        elif result['away_score'] < result['home_score']:
            # Loss in regulation or OT
            if went_to_overtime and not game.is_playoff:
                # Overtime loss (OTL) - 1 point
                away_standing.ot_losses += 1
                away_standing.points += 1
            else:
                # Regulation loss
                away_standing.losses += 1
        # If tied, it's a playoff game that went to multiple OTs (handled above)

def enter_playoffs(simulation_id):
    """Create playoff bracket and enter playoffs state - conference-based"""
    simulation = Simulation.query.get(simulation_id)
    season = simulation.current_season

    if simulation.status not in ['season_end', 'playoffs']:
        return {'error': 'Season not complete yet'}

    existing_series = PlayoffSeries.query.filter_by(
        simulation_id=simulation_id,
        season=season
    ).first()
    if existing_series:
        simulation.status = 'playoffs'
        db.session.commit()
        return {'message': 'Playoffs already created', 'status': 'playoffs'}

    remaining = Game.query.filter_by(
        simulation_id=simulation_id,
        season=season,
        is_playoff=False,
        simulated=False
    ).count()
    if remaining > 0:
        return {'error': 'Regular season not fully simulated'}

    from services.league_service import get_playoff_teams
    num_playoff_teams = get_playoff_teams(simulation.num_teams)

    # Separate standings by conference
    from models.team import Team
    eastern_standings = db.session.query(Standing, Team)\
        .join(Team, Standing.team_id == Team.id)\
        .filter(
            Standing.simulation_id == simulation_id,
            Standing.season == season,
            Team.conference == 'Eastern'
        )\
        .order_by(
            Standing.points.desc(),
            Standing.wins.desc(),
            Standing.goals_for.desc()
        ).all()
    
    western_standings = db.session.query(Standing, Team)\
        .join(Team, Standing.team_id == Team.id)\
        .filter(
            Standing.simulation_id == simulation_id,
            Standing.season == season,
            Team.conference == 'Western'
        )\
        .order_by(
            Standing.points.desc(),
            Standing.wins.desc(),
            Standing.goals_for.desc()
        ).all()

    # Determine how many teams per conference make playoffs based on total playoff teams
    eastern_count = len(eastern_standings)
    western_count = len(western_standings)
    
    # Calculate teams per conference based on requirements:
    # 4 teams: all 4 make playoffs → 2 per conference
    # 6 teams: top 4 make playoffs → 2 per conference  
    # 8 teams: all 8 make playoffs → 4 per conference
    # 10 teams: top 8 make playoffs → 4 per conference
    # 12 teams: top 8 make playoffs → 4 per conference
    if num_playoff_teams == 4:
        # 4 or 6 team league: 2 per conference
        per_conference = 2
    elif num_playoff_teams == 8:
        # 8, 10, or 12 team league: 4 per conference
        per_conference = 4
    else:
        # Fallback: split evenly
        per_conference = num_playoff_teams // 2

    # Ensure we don't take more teams than available in each conference
    per_conference = min(per_conference, eastern_count, western_count)

    # Get top teams from each conference (already sorted by points, wins, goals_for descending)
    # This gives us the seeded order: [1st, 2nd, 3rd, ...]
    eastern_seeds = [s.team_id for s, _ in eastern_standings[:per_conference]]
    western_seeds = [s.team_id for s, _ in western_standings[:per_conference]]

    # Create round 1 series within each conference
    # Seed format: 1st vs last, 2nd vs 2nd-to-last, etc.
    round_num = 1
    
    # Eastern Conference bracket
    # Pair teams: seeds[i] (higher seed) vs seeds[-(i+1)] (lower seed)
    # Example: 4 teams → [1st, 2nd, 3rd, 4th]
    #          Series 1: 1st vs 4th (seeds[0] vs seeds[-1])
    #          Series 2: 2nd vs 3rd (seeds[1] vs seeds[-2])
    num_eastern_series = len(eastern_seeds) // 2
    for i in range(num_eastern_series):
        higher_seed = eastern_seeds[i]  # 1st, 2nd, 3rd, etc.
        lower_seed = eastern_seeds[-(i + 1)]  # last, 2nd-to-last, etc.
        series = PlayoffSeries(
            simulation_id=simulation_id,
            season=season,
            round=round_num,
            higher_seed_team_id=higher_seed,
            lower_seed_team_id=lower_seed
        )
        db.session.add(series)
    
    # Western Conference bracket
    # Same seeding logic: 1st vs last, 2nd vs 2nd-to-last, etc.
    num_western_series = len(western_seeds) // 2
    for i in range(num_western_series):
        higher_seed = western_seeds[i]  # 1st, 2nd, 3rd, etc.
        lower_seed = western_seeds[-(i + 1)]  # last, 2nd-to-last, etc.
        series = PlayoffSeries(
            simulation_id=simulation_id,
            season=season,
            round=round_num,
            higher_seed_team_id=higher_seed,
            lower_seed_team_id=lower_seed
        )
        db.session.add(series)

    simulation.status = 'playoffs'
    db.session.commit()
    return {'message': 'Playoffs created', 'status': 'playoffs'}

def _series_home_team(series, game_number):
    if game_number in [1, 2, 5, 7]:
        return series.higher_seed_team_id, series.lower_seed_team_id
    return series.lower_seed_team_id, series.higher_seed_team_id

def _ensure_playoff_winner(result):
    if result['home_score'] != result['away_score']:
        return result
    if random.random() < 0.5:
        result['home_score'] += 1
    else:
        result['away_score'] += 1
    return result

def simulate_playoff_game(simulation_id, series_id):
    """Simulate the next game in a playoff series"""
    simulation = Simulation.query.get(simulation_id)
    series = PlayoffSeries.query.filter_by(
        id=series_id,
        simulation_id=simulation_id,
        season=simulation.current_season
    ).first()
    if not series:
        return {'error': 'Series not found'}

    if series.status != 'in_progress':
        return {'error': 'Series already completed'}

    if series.next_game_number > 7:
        return {'error': 'Series already completed'}

    home_id, away_id = _series_home_team(series, series.next_game_number)
    game_date = simulation.current_date or date.today()
    game = Game(
        simulation_id=simulation_id,
        season=simulation.current_season,
        date=game_date,
        home_team_id=home_id,
        away_team_id=away_id,
        is_playoff=True,
        playoff_round=series.round,
        series_id=series.id,
        simulated=False
    )
    db.session.add(game)
    db.session.flush()

    result = simulate_game(home_id, away_id, True)
    result = _ensure_playoff_winner(result)
    save_game_result(game, result)

    if result['home_score'] > result['away_score']:
        if home_id == series.higher_seed_team_id:
            series.higher_seed_wins += 1
        else:
            series.lower_seed_wins += 1
        winning_team_id = home_id
    else:
        if away_id == series.higher_seed_team_id:
            series.higher_seed_wins += 1
        else:
            series.lower_seed_wins += 1
        winning_team_id = away_id

    series.next_game_number += 1
    series_completed = False
    if series.higher_seed_wins >= 4 or series.lower_seed_wins >= 4:
        series.status = 'complete'
        series.winner_team_id = winning_team_id
        series_completed = True

    simulation.current_date = game_date + timedelta(days=1)
    db.session.commit()

    _create_next_round_if_ready(simulation_id, simulation.current_season, series.round)
    
    # Check if playoffs are complete when a series finishes
    # This handles both individual game simulation and round simulation
    if series_completed:
        # Refresh simulation object to get latest status
        db.session.refresh(simulation)
        _check_and_advance_to_next_season(simulation_id)

    return {'message': 'Game simulated', 'series_id': series.id}

def _check_and_advance_to_next_season(simulation_id):
    """Check if playoffs are complete and advance to next season if so"""
    # Re-query to ensure we have the latest simulation state
    simulation = Simulation.query.get(simulation_id)
    if not simulation:
        return
    
    # Check if we're in playoffs
    if simulation.status != 'playoffs':
        return
    
    # Check if all playoff series are complete for current season
    # Use a fresh query to ensure we get the latest data
    incomplete = PlayoffSeries.query.filter_by(
        simulation_id=simulation_id,
        season=simulation.current_season,
        status='in_progress'
    ).count()
    
    if incomplete == 0:
        # All playoffs complete - award trophies and advance to next season
        completed_season = simulation.current_season
        print(f"All playoff series complete for season {completed_season}. Advancing to next season...")
        
        from services.trophy_service import award_trophies
        try:
            award_trophies(simulation_id, completed_season)
            print(f"Trophies awarded for season {completed_season}")
        except Exception as e:
            print(f"Error awarding trophies for season {completed_season}: {e}")
            import traceback
            traceback.print_exc()
            # Continue even if trophy awarding fails
        
        # Re-query simulation to ensure we have the latest state
        simulation = Simulation.query.get(simulation_id)
        simulation.current_season += 1
        simulation.status = 'season'
        
        # Generate schedule for the new season
        generate_season_schedule(simulation_id, simulation.current_season)
        
        db.session.commit()
        print(f"Playoffs complete for season {completed_season}. Advanced to season {simulation.current_season}. Status: {simulation.status}")

def _create_next_round_if_ready(simulation_id, season, round_num):
    """Create next playoff round, keeping conferences separate until final"""
    current_series = PlayoffSeries.query.filter_by(
        simulation_id=simulation_id,
        season=season,
        round=round_num
    ).all()
    if not current_series:
        return

    if any(s.status != 'complete' for s in current_series):
        return

    next_round = round_num + 1
    existing_next = PlayoffSeries.query.filter_by(
        simulation_id=simulation_id,
        season=season,
        round=next_round
    ).first()
    if existing_next:
        return

    from models.team import Team
    teams = Team.query.filter_by(simulation_id=simulation_id).all()
    team_lookup = {t.id: t for t in teams}

    # Separate winners by conference
    eastern_winners = []
    western_winners = []
    
    for series in sorted(current_series, key=lambda s: s.id):
        winner_id = series.winner_team_id
        winner_team = team_lookup.get(winner_id)
        if winner_team:
            if winner_team.conference == 'Eastern':
                eastern_winners.append(winner_id)
            else:
                western_winners.append(winner_id)

    # If we have both conferences with winners, keep them separate until final
    # Final round (when only 2 teams remain total) merges conferences
    total_winners = len(eastern_winners) + len(western_winners)
    
    # Check if current round is already the final (has teams from different conferences)
    is_current_final = False
    if len(current_series) == 1:
        series = current_series[0]
        higher_team = team_lookup.get(series.higher_seed_team_id)
        lower_team = team_lookup.get(series.lower_seed_team_id)
        if higher_team and lower_team and higher_team.conference != lower_team.conference:
            is_current_final = True
    
    # Don't create another round if current round is the final
    if is_current_final:
        return
    
    if total_winners == 2:
        # Final round - merge conferences
        higher_seed = eastern_winners[0] if eastern_winners else western_winners[0]
        lower_seed = western_winners[0] if western_winners else eastern_winners[0]
        series = PlayoffSeries(
            simulation_id=simulation_id,
            season=season,
            round=next_round,
            higher_seed_team_id=higher_seed,
            lower_seed_team_id=lower_seed
        )
        db.session.add(series)
    else:
        # Create series within each conference
        if len(eastern_winners) >= 2:
            num_eastern = len(eastern_winners) // 2
            for i in range(num_eastern):
                higher_seed = eastern_winners[i]
                lower_seed = eastern_winners[-(i + 1)]
                series = PlayoffSeries(
                    simulation_id=simulation_id,
                    season=season,
                    round=next_round,
                    higher_seed_team_id=higher_seed,
                    lower_seed_team_id=lower_seed
                )
                db.session.add(series)
        
        if len(western_winners) >= 2:
            num_western = len(western_winners) // 2
            for i in range(num_western):
                higher_seed = western_winners[i]
                lower_seed = western_winners[-(i + 1)]
                series = PlayoffSeries(
                    simulation_id=simulation_id,
                    season=season,
                    round=next_round,
                    higher_seed_team_id=higher_seed,
                    lower_seed_team_id=lower_seed
                )
                db.session.add(series)
    
    db.session.commit()

def get_playoff_bracket(simulation_id):
    """Get playoff series grouped by round"""
    simulation = Simulation.query.get(simulation_id)
    season = simulation.current_season
    series_list = PlayoffSeries.query.filter_by(
        simulation_id=simulation_id,
        season=season
    ).order_by(PlayoffSeries.round.asc(), PlayoffSeries.id.asc()).all()

    from models.team import Team
    teams = Team.query.filter_by(simulation_id=simulation_id).all()
    team_lookup = {t.id: t for t in teams}

    rounds = {}
    for series in series_list:
        last_game = Game.query.filter_by(series_id=series.id).order_by(Game.id.desc()).first()
        higher_team = team_lookup.get(series.higher_seed_team_id)
        lower_team = team_lookup.get(series.lower_seed_team_id)
        winner_team = team_lookup.get(series.winner_team_id) if series.winner_team_id else None
        
        # Determine conference - use higher seed team's conference, or winner's if available
        conference = None
        if winner_team:
            conference = winner_team.conference
        elif higher_team:
            conference = higher_team.conference
        elif lower_team:
            conference = lower_team.conference
        
        rounds.setdefault(series.round, []).append({
            **series.to_dict(),
            'higher_seed_team': higher_team.to_dict() if higher_team else None,
            'lower_seed_team': lower_team.to_dict() if lower_team else None,
            'winner_team': winner_team.to_dict() if winner_team else None,
            'conference': conference,
            'last_game': last_game.to_dict() if last_game else None
        })

    return {
        'rounds': rounds,
        'season': season,
        'status': simulation.status
    }

def generate_playoff_matchups(simulation_id, season, round_num, playoff_teams):
    """Generate playoff matchups for a round"""
    games = []
    
    # For simplicity, pair teams sequentially (1v8, 2v7, etc.)
    matchups = []
    num_matchups = len(playoff_teams) // (2 ** round_num)
    
    for i in range(num_matchups):
        higher_seed = playoff_teams[i]
        lower_seed = playoff_teams[-(i + 1)]
        matchups.append((higher_seed, lower_seed))
    
    # Generate best-of-7 series (4 home for higher seed, 3 for lower)
    base_date = date(1980 + season - 1, 4, 1)  # Playoffs start in April
    
    for home_id, away_id in matchups:
        # Games 1, 2, 5, 7 at higher seed, games 3, 4, 6 at lower seed
        game_locations = [
            (home_id, away_id),  # Game 1
            (home_id, away_id),  # Game 2
            (away_id, home_id),  # Game 3
            (away_id, home_id),  # Game 4
            (home_id, away_id),  # Game 5
            (away_id, home_id),  # Game 6
            (home_id, away_id),  # Game 7
        ]
        
        current_date = base_date + timedelta(days=(round_num - 1) * 14)
        
        for i, (h, a) in enumerate(game_locations):
            game = Game(
                simulation_id=simulation_id,
                season=season,
                date=current_date + timedelta(days=i * 2),
                home_team_id=h,
                away_team_id=a,
                is_playoff=True,
                playoff_round=round_num,
                simulated=False
            )
            games.append(game)
            db.session.add(game)
    
    db.session.commit()
    return games
