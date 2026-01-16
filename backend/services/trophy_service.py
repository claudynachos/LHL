"""Trophy awarding service"""
from extensions import db
from models.trophy import Trophy
from models.game import PlayoffSeries, Standing
from models.team import Team
from models.player import Player
from sqlalchemy import func, desc

def award_trophies(simulation_id, season):
    """Award all trophies for a completed season"""
    # Check if trophies already awarded for this season
    existing = Trophy.query.filter_by(
        simulation_id=simulation_id,
        season=season
    ).first()
    
    if existing:
        return {'message': 'Trophies already awarded for this season'}
    
    trophies_awarded = []
    
    # Team Awards
    # 1. Stanley Cup - Winner of final playoff round
    stanley_cup_winner = _get_stanley_cup_winner(simulation_id, season)
    if stanley_cup_winner:
        trophy = Trophy(
            simulation_id=simulation_id,
            season=season,
            trophy_name='Stanley Cup',
            trophy_type='team',
            team_id=stanley_cup_winner
        )
        db.session.add(trophy)
        trophies_awarded.append('Stanley Cup')
    
    # 2. Presidents' Trophy - Best regular season record
    presidents_winner = _get_presidents_trophy_winner(simulation_id, season)
    if presidents_winner:
        trophy = Trophy(
            simulation_id=simulation_id,
            season=season,
            trophy_name='Presidents\' Trophy',
            trophy_type='team',
            team_id=presidents_winner
        )
        db.session.add(trophy)
        trophies_awarded.append('Presidents\' Trophy')
    
    # Individual Awards (based on regular season stats)
    # Get season stats for calculations
    from api.stats import get_season_stats
    from flask import Flask
    app = Flask(__name__)
    with app.app_context():
        # We'll calculate these directly from the database
        pass
    
    # 3. Art Ross Trophy - Most points
    art_ross_winner = _get_art_ross_winner(simulation_id, season)
    if art_ross_winner:
        trophy = Trophy(
            simulation_id=simulation_id,
            season=season,
            trophy_name='Art Ross Trophy',
            trophy_type='individual',
            player_id=art_ross_winner
        )
        db.session.add(trophy)
        trophies_awarded.append('Art Ross Trophy')
    
    # 4. Rocket Richard Trophy - Most goals
    rocket_richard_winner = _get_rocket_richard_winner(simulation_id, season)
    if rocket_richard_winner:
        trophy = Trophy(
            simulation_id=simulation_id,
            season=season,
            trophy_name='Rocket Richard Trophy',
            trophy_type='individual',
            player_id=rocket_richard_winner
        )
        db.session.add(trophy)
        trophies_awarded.append('Rocket Richard Trophy')
    
    # 5. Hart Trophy - MVP (most points for skaters, best save% for goalies)
    hart_winner = _get_hart_winner(simulation_id, season)
    if hart_winner:
        trophy = Trophy(
            simulation_id=simulation_id,
            season=season,
            trophy_name='Hart Trophy',
            trophy_type='individual',
            player_id=hart_winner
        )
        db.session.add(trophy)
        trophies_awarded.append('Hart Trophy')
    
    # 6. Norris Trophy - Best defenseman (most points among defensemen)
    norris_winner = _get_norris_winner(simulation_id, season)
    if norris_winner:
        trophy = Trophy(
            simulation_id=simulation_id,
            season=season,
            trophy_name='Norris Trophy',
            trophy_type='individual',
            player_id=norris_winner
        )
        db.session.add(trophy)
        trophies_awarded.append('Norris Trophy')
    
    # 7. Vezina Trophy - Best goaltender (best save percentage)
    vezina_winner = _get_vezina_winner(simulation_id, season)
    if vezina_winner:
        trophy = Trophy(
            simulation_id=simulation_id,
            season=season,
            trophy_name='Vezina Trophy',
            trophy_type='individual',
            player_id=vezina_winner
        )
        db.session.add(trophy)
        trophies_awarded.append('Vezina Trophy')
    
    # 8. Conn Smythe Trophy - Playoff MVP
    conn_smythe_winner = _get_conn_smythe_winner(simulation_id, season)
    if conn_smythe_winner:
        trophy = Trophy(
            simulation_id=simulation_id,
            season=season,
            trophy_name='Conn Smythe Trophy',
            trophy_type='individual',
            player_id=conn_smythe_winner
        )
        db.session.add(trophy)
        trophies_awarded.append('Conn Smythe Trophy')
    
    db.session.commit()
    
    return {
        'message': f'Awarded {len(trophies_awarded)} trophies',
        'trophies': trophies_awarded
    }

def _get_stanley_cup_winner(simulation_id, season):
    """Get Stanley Cup winner (final round winner)"""
    # Find the final round (highest round number)
    final_series = PlayoffSeries.query.filter_by(
        simulation_id=simulation_id,
        season=season,
        status='complete'
    ).order_by(desc(PlayoffSeries.round)).first()
    
    if final_series and final_series.winner_team_id:
        return final_series.winner_team_id
    return None

def _get_presidents_trophy_winner(simulation_id, season):
    """Get Presidents' Trophy winner (most points in regular season)"""
    standing = Standing.query.filter_by(
        simulation_id=simulation_id,
        season=season
    ).order_by(desc(Standing.points), desc(Standing.wins), desc(Standing.goals_for)).first()
    
    if standing:
        return standing.team_id
    return None

def _get_art_ross_winner(simulation_id, season):
    """Get Art Ross Trophy winner (most points) - NHL: No minimum games, but typically requires significant play"""
    from models.game import PlayerStat, Game
    from models.player import Player
    
    # Get regular season stats only
    # Count unique games played
    stats = db.session.query(
        Player.id,
        Player.name,
        func.sum(PlayerStat.goals + PlayerStat.assists).label('points'),
        func.count(func.distinct(Game.id)).label('games_played')
    ).join(PlayerStat, Player.id == PlayerStat.player_id)\
     .join(Game, PlayerStat.game_id == Game.id)\
     .filter(
         Game.simulation_id == simulation_id,
         Game.season == season,
         Game.is_playoff == False,
         Player.position != 'G'
     ).group_by(Player.id, Player.name)\
     .having(func.count(func.distinct(Game.id)) >= 25)\
     .order_by(desc('points')).first()
    
    if stats:
        return stats.id
    return None

def _get_rocket_richard_winner(simulation_id, season):
    """Get Rocket Richard Trophy winner (most goals) - NHL: No minimum games, but typically requires significant play"""
    from models.game import PlayerStat, Game
    from models.player import Player
    
    stats = db.session.query(
        Player.id,
        func.sum(PlayerStat.goals).label('goals'),
        func.count(func.distinct(Game.id)).label('games_played')
    ).join(PlayerStat, Player.id == PlayerStat.player_id)\
     .join(Game, PlayerStat.game_id == Game.id)\
     .filter(
         Game.simulation_id == simulation_id,
         Game.season == season,
         Game.is_playoff == False,
         Player.position != 'G'
     ).group_by(Player.id)\
     .having(func.count(func.distinct(Game.id)) >= 25)\
     .order_by(desc('goals')).first()
    
    if stats:
        return stats.id
    return None

def _get_hart_winner(simulation_id, season):
    """Get Hart Trophy winner (MVP - best skater by points, best goalie by save%) - NHL: Typically 25+ games"""
    from models.game import PlayerStat, Game
    from models.player import Player
    
    # Get best skater (by points) with minimum games
    best_skater = db.session.query(
        Player.id,
        func.sum(PlayerStat.goals + PlayerStat.assists).label('points'),
        func.count(func.distinct(Game.id)).label('games_played')
    ).join(PlayerStat, Player.id == PlayerStat.player_id)\
     .join(Game, PlayerStat.game_id == Game.id)\
     .filter(
         Game.simulation_id == simulation_id,
         Game.season == season,
         Game.is_playoff == False,
         Player.position != 'G'
     ).group_by(Player.id)\
     .having(func.count(func.distinct(Game.id)) >= 25)\
     .order_by(desc('points')).first()
    
    # Get best goalie (by save percentage) with minimum games
    best_goalie = db.session.query(
        Player.id,
        func.sum(PlayerStat.saves).label('saves'),
        func.sum(PlayerStat.shots_against).label('shots_against'),
        func.count(func.distinct(Game.id)).label('games_played')
    ).join(PlayerStat, Player.id == PlayerStat.player_id)\
     .join(Game, PlayerStat.game_id == Game.id)\
     .filter(
         Game.simulation_id == simulation_id,
         Game.season == season,
         Game.is_playoff == False,
         Player.position == 'G'
     ).group_by(Player.id)\
     .having(
         func.sum(PlayerStat.shots_against) > 0,
         func.count(func.distinct(Game.id)) >= 25  # Minimum 25 games for goalies
     ).all()
    
    best_goalie_sv_pct = None
    best_goalie_id = None
    for goalie in best_goalie:
        if goalie.shots_against > 0:
            sv_pct = goalie.saves / goalie.shots_against
            if best_goalie_sv_pct is None or sv_pct > best_goalie_sv_pct:
                best_goalie_sv_pct = sv_pct
                best_goalie_id = goalie.id
    
    # Return the one with better relative performance
    # For simplicity, return best skater (can be improved with more sophisticated MVP calculation)
    if best_skater:
        return best_skater.id
    return best_goalie_id

def _get_norris_winner(simulation_id, season):
    """Get Norris Trophy winner (best defenseman by points) - NHL: Typically 25+ games"""
    from models.game import PlayerStat, Game
    from models.player import Player
    
    stats = db.session.query(
        Player.id,
        func.sum(PlayerStat.goals + PlayerStat.assists).label('points'),
        func.count(func.distinct(Game.id)).label('games_played')
    ).join(PlayerStat, Player.id == PlayerStat.player_id)\
     .join(Game, PlayerStat.game_id == Game.id)\
     .filter(
         Game.simulation_id == simulation_id,
         Game.season == season,
         Game.is_playoff == False,
         Player.position == 'D'
     ).group_by(Player.id)\
     .having(func.count(func.distinct(Game.id)) >= 25)\
     .order_by(desc('points')).first()
    
    if stats:
        return stats.id
    return None

def _get_vezina_winner(simulation_id, season):
    """Get Vezina Trophy winner (best save percentage) - NHL: Typically 25+ games"""
    from models.game import PlayerStat, Game
    from models.player import Player
    
    goalies = db.session.query(
        Player.id,
        func.sum(PlayerStat.saves).label('saves'),
        func.sum(PlayerStat.shots_against).label('shots_against'),
        func.count(func.distinct(Game.id)).label('games_played')
    ).join(PlayerStat, Player.id == PlayerStat.player_id)\
     .join(Game, PlayerStat.game_id == Game.id)\
     .filter(
         Game.simulation_id == simulation_id,
         Game.season == season,
         Game.is_playoff == False,
         Player.position == 'G'
     ).group_by(Player.id)\
     .having(
         func.sum(PlayerStat.shots_against) > 0,
         func.count(func.distinct(Game.id)) >= 25  # Minimum 25 games for Vezina
     ).all()
    
    best_sv_pct = None
    best_goalie_id = None
    for goalie in goalies:
        if goalie.shots_against > 0:
            sv_pct = goalie.saves / goalie.shots_against
            if best_sv_pct is None or sv_pct > best_sv_pct:
                best_sv_pct = sv_pct
                best_goalie_id = goalie.id
    
    return best_goalie_id

def _get_conn_smythe_winner(simulation_id, season):
    """Get Conn Smythe Trophy winner (playoff MVP - most points in playoffs) - No minimum games for playoffs"""
    from models.game import PlayerStat, Game
    from models.player import Player
    
    # Get playoff stats - typically goes to a player from the winning team
    # For simplicity, we'll use most points, but ideally should favor players from Stanley Cup winner
    stats = db.session.query(
        Player.id,
        func.sum(PlayerStat.goals + PlayerStat.assists).label('points'),
        func.count(func.distinct(Game.id)).label('games_played')
    ).join(PlayerStat, Player.id == PlayerStat.player_id)\
     .join(Game, PlayerStat.game_id == Game.id)\
     .filter(
         Game.simulation_id == simulation_id,
         Game.season == season,
         Game.is_playoff == True
     ).group_by(Player.id)\
     .order_by(desc('points')).first()
    
    if stats:
        return stats.id
    return None
