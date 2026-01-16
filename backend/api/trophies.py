from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func, desc

bp = Blueprint('trophies', __name__)

# NHL Trophy definitions
NHL_TROPHIES = {
    # Team Awards
    'team': [
        {'name': 'Stanley Cup', 'description': 'Championship winner'},
        {'name': 'Presidents\' Trophy', 'description': 'Best regular season record'},
    ],
    # Individual Awards
    'individual': [
        {'name': 'Hart Trophy', 'description': 'Most valuable player'},
        {'name': 'Art Ross Trophy', 'description': 'Most points'},
        {'name': 'Rocket Richard Trophy', 'description': 'Most goals'},
        {'name': 'Norris Trophy', 'description': 'Best defenseman'},
        {'name': 'Vezina Trophy', 'description': 'Best goaltender'},
        {'name': 'Calder Trophy', 'description': 'Rookie of the year'},
        {'name': 'Selke Trophy', 'description': 'Best defensive forward'},
        {'name': 'Lady Byng Trophy', 'description': 'Most gentlemanly player'},
        {'name': 'Conn Smythe Trophy', 'description': 'Playoff MVP'},
    ]
}

@bp.route('/<int:simulation_id>', methods=['GET'])
@jwt_required()
def get_trophies(simulation_id):
    """Get trophy winners by season"""
    from extensions import db
    from models.trophy import Trophy
    from models.simulation import Simulation
    
    season = request.args.get('season', type=int)
    trophy_type = request.args.get('trophy_type')  # 'team', 'individual', or None for all
    team_id = request.args.get('team_id', type=int)
    
    query = Trophy.query.filter_by(simulation_id=simulation_id)
    
    if season:
        query = query.filter_by(season=season)
    
    if trophy_type:
        query = query.filter_by(trophy_type=trophy_type)
    
    if team_id:
        query = query.filter_by(team_id=team_id)
    
    trophies = query.order_by(desc(Trophy.season), Trophy.trophy_name).all()
    
    # Group by season
    trophies_by_season = {}
    for trophy in trophies:
        if trophy.season not in trophies_by_season:
            trophies_by_season[trophy.season] = []
        trophies_by_season[trophy.season].append(trophy.to_dict())
    
    return jsonify({
        'trophies_by_season': trophies_by_season,
        'trophy_definitions': NHL_TROPHIES
    }), 200

@bp.route('/definitions', methods=['GET'])
@jwt_required()
def get_trophy_definitions():
    """Get all NHL trophy definitions"""
    return jsonify({
        'trophies': NHL_TROPHIES
    }), 200

@bp.route('/simulation-ranking/<int:simulation_id>', methods=['GET'])
@jwt_required()
def get_simulation_ranking(simulation_id):
    """Get team rankings by Stanley Cup wins"""
    from extensions import db
    from models.trophy import Trophy
    from models.team import Team
    
    # Count Stanley Cup wins per team
    cup_wins = db.session.query(
        Trophy.team_id,
        Team.name,
        Team.city,
        func.count(Trophy.id).label('cups')
    ).join(Team, Trophy.team_id == Team.id)\
     .filter(
         Trophy.simulation_id == simulation_id,
         Trophy.trophy_name == 'Stanley Cup'
     ).group_by(Trophy.team_id, Team.name, Team.city)\
     .order_by(desc('cups'), Team.name).all()
    
    ranking = []
    for idx, (team_id, team_name, team_city, cups) in enumerate(cup_wins, 1):
        ranking.append({
            'rank': idx,
            'team_id': team_id,
            'team_name': team_name,
            'team_city': team_city,
            'stanley_cups': cups
        })
    
    return jsonify({
        'ranking': ranking
    }), 200

@bp.route('/award/<int:simulation_id>', methods=['POST'])
@jwt_required()
def award_trophies_endpoint(simulation_id):
    """Manually award trophies for a season"""
    from extensions import db
    from services.trophy_service import award_trophies
    
    data = request.get_json()
    season = data.get('season')
    
    if not season:
        return jsonify({'error': 'Season is required'}), 400
    
    try:
        result = award_trophies(simulation_id, season)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
