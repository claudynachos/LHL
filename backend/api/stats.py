from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func, desc

bp = Blueprint('stats', __name__)

@bp.route('/season/<int:simulation_id>', methods=['GET'])
@jwt_required()
def get_season_stats(simulation_id):
    """Get current season stats"""
    from extensions import db
    from models.game import PlayerStat
    from models.player import Player
    from models.team import Team
    
    season = request.args.get('season', type=int)
    
    # Get player stats aggregated for the season
    query = db.session.query(
        Player.id,
        Player.name,
        Team.name.label('team_name'),
        func.count(PlayerStat.game_id).label('games_played'),
        func.sum(PlayerStat.goals).label('goals'),
        func.sum(PlayerStat.assists).label('assists'),
        (func.sum(PlayerStat.goals) + func.sum(PlayerStat.assists)).label('points'),
        func.sum(PlayerStat.plus_minus).label('plus_minus'),
        func.sum(PlayerStat.hits).label('hits'),
        func.sum(PlayerStat.blocks).label('blocks'),
        func.sum(PlayerStat.shots).label('shots')
    ).join(PlayerStat, Player.id == PlayerStat.player_id)\
     .join(Team, PlayerStat.team_id == Team.id)\
     .filter(Team.simulation_id == simulation_id)
    
    if season:
        # Filter by specific season
        from models.game import Game
        query = query.join(Game, PlayerStat.game_id == Game.id)\
                    .filter(Game.season == season)
    
    stats = query.group_by(Player.id, Player.name, Team.name)\
                 .order_by(desc('points'))\
                 .limit(100)\
                 .all()
    
    return jsonify({
        'stats': [{
            'player_id': s.id,
            'player_name': s.name,
            'team_name': s.team_name,
            'games_played': s.games_played or 0,
            'goals': s.goals or 0,
            'assists': s.assists or 0,
            'points': s.points or 0,
            'plus_minus': s.plus_minus or 0,
            'hits': s.hits or 0,
            'blocks': s.blocks or 0,
            'shots': s.shots or 0
        } for s in stats]
    }), 200

@bp.route('/all-time/<int:simulation_id>', methods=['GET'])
@jwt_required()
def get_alltime_stats(simulation_id):
    """Get all-time stats across all seasons"""
    from extensions import db
    from models.game import PlayerStat
    from models.player import Player
    from models.team import Team
    
    # Similar to season stats but without season filter
    query = db.session.query(
        Player.id,
        Player.name,
        func.count(PlayerStat.game_id).label('games_played'),
        func.sum(PlayerStat.goals).label('goals'),
        func.sum(PlayerStat.assists).label('assists'),
        (func.sum(PlayerStat.goals) + func.sum(PlayerStat.assists)).label('points'),
        func.sum(PlayerStat.plus_minus).label('plus_minus'),
        func.sum(PlayerStat.hits).label('hits'),
        func.sum(PlayerStat.blocks).label('blocks')
    ).join(PlayerStat, Player.id == PlayerStat.player_id)\
     .join(Team, PlayerStat.team_id == Team.id)\
     .filter(Team.simulation_id == simulation_id)\
     .group_by(Player.id, Player.name)\
     .order_by(desc('points'))\
     .limit(100)\
     .all()
    
    return jsonify({
        'stats': [{
            'player_id': s.id,
            'player_name': s.name,
            'games_played': s.games_played or 0,
            'goals': s.goals or 0,
            'assists': s.assists or 0,
            'points': s.points or 0,
            'plus_minus': s.plus_minus or 0,
            'hits': s.hits or 0,
            'blocks': s.blocks or 0
        } for s in query]
    }), 200

@bp.route('/standings/<int:simulation_id>', methods=['GET'])
@jwt_required()
def get_standings(simulation_id):
    """Get league standings"""
    from extensions import db
    from models.game import Standing
    from models.team import Team
    
    season = request.args.get('season', type=int)
    
    query = db.session.query(Standing, Team)\
        .join(Team, Standing.team_id == Team.id)\
        .filter(Standing.simulation_id == simulation_id)
    
    if season:
        query = query.filter(Standing.season == season)
    
    standings = query.all()
    
    # Group by conference
    eastern = []
    western = []
    
    for standing, team in standings:
        standing_dict = standing.to_dict()
        standing_dict['team_name'] = team.name
        standing_dict['conference'] = team.conference
        
        if team.conference == 'Eastern':
            eastern.append(standing_dict)
        else:
            western.append(standing_dict)
    
    # Sort by points
    eastern.sort(key=lambda x: x['points'], reverse=True)
    western.sort(key=lambda x: x['points'], reverse=True)
    
    return jsonify({
        'eastern': eastern,
        'western': western
    }), 200

@bp.route('/trophies/<int:simulation_id>', methods=['GET'])
@jwt_required()
def get_trophies(simulation_id):
    """Get trophy winners by season"""
    # This would require a separate trophies table, for now return placeholder
    return jsonify({
        'message': 'Trophy tracking coming soon',
        'trophies': []
    }), 200
