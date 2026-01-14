from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date

bp = Blueprint('simulations', __name__)

@bp.route('/create', methods=['POST'])
@jwt_required()
def create_simulation():
    """Create a new simulation"""
    from extensions import db
    from models.simulation import Simulation
    from models.team import Team
    from services.league_service import initialize_league
    
    user_id = int(get_jwt_identity())  # Convert string identity back to int
    data = request.get_json()
    
    if not data or not data.get('year_length') or not data.get('num_teams'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    year_length = data['year_length']
    num_teams = data['num_teams']
    
    if year_length not in [20, 21, 22, 23, 24, 25]:
        return jsonify({'error': 'Year length must be between 20 and 25'}), 400
    
    if num_teams not in [4, 6, 8, 10, 12]:
        return jsonify({'error': 'Number of teams must be 4, 6, 8, 10, or 12'}), 400
    
    # Create simulation
    simulation = Simulation(
        user_id=user_id,
        year_length=year_length,
        num_teams=num_teams,
        current_season=1,
        current_date=date(1980, 10, 1),  # Start in October 1980
        status='draft'
    )
    
    db.session.add(simulation)
    db.session.flush()
    
    # Initialize teams
    teams = initialize_league(simulation.id, num_teams)
    for team in teams:
        db.session.add(team)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Simulation created successfully',
        'simulation': simulation.to_dict(),
        'teams': [t.to_dict() for t in teams]
    }), 201

@bp.route('/<int:simulation_id>', methods=['GET'])
@jwt_required()
def get_simulation(simulation_id):
    """Get simulation details"""
    from models.simulation import Simulation
    from models.team import Team
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation:
        return jsonify({'error': 'Simulation not found'}), 404
    
    if simulation.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    teams = Team.query.filter_by(simulation_id=simulation_id).all()
    
    return jsonify({
        'simulation': simulation.to_dict(),
        'teams': [t.to_dict() for t in teams]
    }), 200

@bp.route('/', methods=['GET'])
@jwt_required()
def list_simulations():
    """List user's simulations"""
    from models.simulation import Simulation
    
    user_id = int(get_jwt_identity())
    simulations = Simulation.query.filter_by(user_id=user_id).order_by(Simulation.created_at.desc()).all()
    
    return jsonify({
        'simulations': [s.to_dict() for s in simulations]
    }), 200

@bp.route('/<int:simulation_id>/draft', methods=['POST'])
@jwt_required()
def make_draft_pick(simulation_id):
    """Make a draft pick"""
    from models.simulation import Simulation
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404
    
    if simulation.status != 'draft':
        return jsonify({'error': 'Draft already completed'}), 400
    
    data = request.get_json()
    
    from services.draft_service import process_draft_pick
    result = process_draft_pick(simulation_id, data)
    
    return jsonify(result), 200

@bp.route('/<int:simulation_id>/draft/current', methods=['GET'])
@jwt_required()
def get_current_draft_pick(simulation_id):
    """Get current draft pick info"""
    from models.simulation import Simulation
    from models.team import Team
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404
    
    if simulation.status != 'draft':
        return jsonify({'error': 'Draft not in progress', 'draft_complete': True}), 200
    
    # Get draft state from simulation
    teams = Team.query.filter_by(simulation_id=simulation_id).order_by(Team.id).all()
    num_teams = len(teams)
    
    # Calculate current pick (simplified - assumes snake draft)
    current_pick = simulation.draft_pick or 1
    total_picks = num_teams * 20  # 20 players per team roster
    
    # Determine which team is picking
    round_num = ((current_pick - 1) // num_teams) + 1
    pick_in_round = ((current_pick - 1) % num_teams)
    
    # Snake draft: reverse order in even rounds
    if round_num % 2 == 0:
        pick_in_round = num_teams - 1 - pick_in_round
    
    picking_team = teams[pick_in_round] if pick_in_round < len(teams) else teams[0]
    
    return jsonify({
        'round': round_num,
        'pick': current_pick,
        'total_picks': total_picks,
        'team_id': picking_team.id,
        'team_name': f"{picking_team.city} {picking_team.name}",
        'is_user_team': picking_team.user_controlled
    }), 200

@bp.route('/<int:simulation_id>/simulate-to-playoffs', methods=['POST'])
@jwt_required()
def simulate_to_playoffs(simulation_id):
    """Simulate games until playoffs"""
    from models.simulation import Simulation
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404
    
    from services.game_service import simulate_season_to_playoffs
    result = simulate_season_to_playoffs(simulation_id)
    
    return jsonify(result), 200

@bp.route('/<int:simulation_id>/simulate-round', methods=['POST'])
@jwt_required()
def simulate_playoff_round(simulation_id):
    """Simulate a playoff round"""
    from models.simulation import Simulation
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404
    
    data = request.get_json()
    round_num = data.get('round', 1)
    
    from services.game_service import simulate_playoff_round
    result = simulate_playoff_round(simulation_id, round_num)
    
    return jsonify(result), 200

@bp.route('/<int:simulation_id>/simulate-season', methods=['POST'])
@jwt_required()
def simulate_full_season(simulation_id):
    """Simulate entire season including playoffs"""
    from models.simulation import Simulation
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404
    
    from services.game_service import simulate_full_season
    result = simulate_full_season(simulation_id)
    
    return jsonify(result), 200
