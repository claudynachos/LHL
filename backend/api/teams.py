from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('teams', __name__)

@bp.route('/<int:team_id>', methods=['GET'])
@jwt_required()
def get_team(team_id):
    """Get team details"""
    from extensions import db
    from models.team import Team, Roster, LineAssignment
    from models.player import Player
    from services.team_rating_service import calculate_team_overall
    
    team = Team.query.get(team_id)
    
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    # Get roster - order by roster entry ID to maintain draft order
    # Filter by team_id and simulation_id to ensure correct roster
    roster = db.session.query(Player).join(Roster).filter(
        Roster.team_id == team_id,
        Roster.simulation_id == team.simulation_id
    ).order_by(Roster.id).all()
    
    # Get line assignments
    lines = LineAssignment.query.filter_by(team_id=team_id).all()
    
    # Calculate team overall rating
    team_overall = calculate_team_overall(team_id)
    
    team_dict = team.to_dict()
    if team_overall is not None:
        team_dict['overall'] = team_overall
    
    return jsonify({
        'team': team_dict,
        'roster': [p.to_dict() for p in roster],
        'lines': [l.to_dict() for l in lines]
    }), 200

@bp.route('/<int:team_id>/roster', methods=['GET'])
@jwt_required()
def get_roster(team_id):
    """Get team roster"""
    from extensions import db
    from models.team import Team, Roster
    from models.player import Player
    
    team = Team.query.get(team_id)
    
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    # Get roster for this team - order by roster entry ID to maintain draft order
    roster = db.session.query(Player).join(Roster).filter(
        Roster.team_id == team_id,
        Roster.simulation_id == team.simulation_id
    ).order_by(Roster.id).all()
    
    # Debug: Log roster contents
    defensemen = [p for p in roster if p.position == 'D']
    print(f"Team {team_id} roster: {len(roster)} players, {len(defensemen)} defensemen")
    for d in defensemen:
        print(f"  - {d.name} (position: {d.position})")
    
    return jsonify({
        'roster': [p.to_dict() for p in roster]
    }), 200

@bp.route('/<int:team_id>/lines', methods=['GET', 'PUT', 'POST'])
@jwt_required()
def manage_lines(team_id):
    """Get or update team lines"""
    from extensions import db
    from models.team import Team, LineAssignment
    from models.simulation import Simulation
    from services.lines_service import auto_populate_lines
    
    user_id = int(get_jwt_identity())
    team = Team.query.get(team_id)
    
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    # Check authorization
    simulation = Simulation.query.get(team.simulation_id)
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        lines = LineAssignment.query.filter_by(team_id=team_id).all()
        return jsonify({
            'lines': [l.to_dict() for l in lines]
        }), 200
    
    if request.method == 'POST':
        # Auto-populate lines
        success = auto_populate_lines(team_id)
        if success:
            lines = LineAssignment.query.filter_by(team_id=team_id).all()
            return jsonify({
                'message': 'Lines auto-populated successfully',
                'lines': [l.to_dict() for l in lines]
            }), 200
        else:
            return jsonify({'message': 'Lines already populated or team not found'}), 200
    
    # PUT - Update lines
    data = request.get_json()
    
    if not data or not data.get('lines'):
        return jsonify({'error': 'Missing lines data'}), 400
    
    # Validate: ensure no player appears twice
    player_ids = [line_data['player_id'] for line_data in data['lines'] if line_data.get('player_id')]
    if len(player_ids) != len(set(player_ids)):
        return jsonify({'error': 'A player cannot be assigned to multiple lines'}), 400
    
    # Delete existing line assignments
    LineAssignment.query.filter_by(team_id=team_id).delete()
    
    # Create new line assignments
    for line_data in data['lines']:
        if line_data.get('player_id'):  # Only create if player_id is provided
            line = LineAssignment(
                team_id=team_id,
                player_id=line_data['player_id'],
                line_type=line_data['line_type'],
                line_number=line_data['line_number'],
                position=line_data['position']
            )
            db.session.add(line)
    
    db.session.commit()
    
    return jsonify({'message': 'Lines updated successfully'}), 200

@bp.route('/<int:team_id>/sign-free-agent', methods=['POST'])
@jwt_required()
def sign_free_agent(team_id):
    """Sign a free agent player"""
    from extensions import db
    from models.team import Team, Roster
    from models.simulation import Simulation
    
    user_id = int(get_jwt_identity())
    team = Team.query.get(team_id)
    
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    simulation = Simulation.query.get(team.simulation_id)
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    player_id = data.get('player_id')
    
    if not player_id:
        return jsonify({'error': 'Missing player_id'}), 400
    
    # Check if player is already on a team
    existing = Roster.query.filter_by(
        simulation_id=simulation.id,
        player_id=player_id
    ).first()
    
    if existing:
        return jsonify({'error': 'Player already on a team'}), 400
    
    # Add player to roster
    roster_entry = Roster(
        team_id=team_id,
        player_id=player_id,
        simulation_id=simulation.id,
        season_acquired=simulation.current_season
    )
    
    db.session.add(roster_entry)
    db.session.commit()
    
    return jsonify({'message': 'Player signed successfully'}), 200
