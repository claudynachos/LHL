"""Game simulation and scheduling service"""
from app import db
from models.simulation import Simulation
from models.team import Team
from models.game import Game, PlayerStat, Standing
from datetime import datetime, timedelta, date
import random
from services.simulation_service import simulate_game

def generate_season_schedule(simulation_id, season):
    """Generate schedule for a season"""
    teams = Team.query.filter_by(simulation_id=simulation_id).all()
    num_teams = len(teams)
    
    # Calculate games per team (roughly 82 games in NHL)
    # For smaller leagues, adjust proportionally
    games_per_team = {
        4: 24,  # Each team plays others 8 times
        6: 40,  # Each team plays others 8 times
        8: 56,  # Each team plays others 8 times
        10: 72,  # Each team plays others 8 times
        12: 82   # Standard NHL schedule
    }.get(num_teams, 82)
    
    games = []
    start_date = date(1980 + season - 1, 10, 1)  # Start in October
    current_date = start_date
    
    # Round-robin scheduling
    matchups = []
    for i, home in enumerate(teams):
        for j, away in enumerate(teams):
            if i != j:
                # Calculate how many times they should play
                times_to_play = games_per_team // (num_teams - 1)
                for _ in range(times_to_play):
                    matchups.append((home.id, away.id))
    
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
    for game in games:
        if not game.simulated:
            result = simulate_game(game.home_team_id, game.away_team_id, False)
            save_game_result(game, result)
            update_standings(game, result)
            simulated_count += 1
    
    # Update simulation status
    simulation.status = 'playoffs'
    simulation.current_date = games[-1].date if games else simulation.current_date
    db.session.commit()
    
    return {
        'message': f'Simulated {simulated_count} regular season games',
        'season': season,
        'status': 'playoffs'
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
    
    # Simulate all playoff rounds
    simulation = Simulation.query.get(simulation_id)
    from services.league_service import get_playoff_teams
    num_playoff_teams = get_playoff_teams(simulation.num_teams)
    
    # Determine number of playoff rounds
    rounds = {
        4: 2,   # Semi-final + Final
        8: 3    # Quarter + Semi + Final
    }.get(num_playoff_teams, 3)
    
    for round_num in range(1, rounds + 1):
        simulate_playoff_round(simulation_id, round_num)
    
    # Advance to next season
    simulation.current_season += 1
    simulation.status = 'season'
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
    
    if home_standing:
        home_standing.goals_for += result['home_score']
        home_standing.goals_against += result['away_score']
        
        if result['home_score'] > result['away_score']:
            home_standing.wins += 1
            home_standing.points += 2
        else:
            home_standing.losses += 1
    
    if away_standing:
        away_standing.goals_for += result['away_score']
        away_standing.goals_against += result['home_score']
        
        if result['away_score'] > result['home_score']:
            away_standing.wins += 1
            away_standing.points += 2
        else:
            away_standing.losses += 1

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
