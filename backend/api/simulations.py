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
    name = data.get('name', '').strip()  # Optional name, default to empty string
    user_team_index = data.get('user_team_index', 0)  # Team index (0-based) for user to control
    
    if year_length not in [20, 21, 22, 23, 24, 25]:
        return jsonify({'error': 'Year length must be between 20 and 25'}), 400
    
    if num_teams not in [4, 6, 8, 10, 12]:
        return jsonify({'error': 'Number of teams must be 4, 6, 8, 10, or 12'}), 400
    
    # Create simulation
    simulation = Simulation(
        user_id=user_id,
        name=name if name else None,  # Store None if empty string
        year_length=year_length,
        num_teams=num_teams,
        current_season=1,
        current_date=date(1980, 10, 1),  # Start in October 1980
        status='draft',
        draft_pick=1
    )
    
    db.session.add(simulation)
    db.session.flush()
    
    # Initialize teams (all AI-controlled initially)
    teams = initialize_league(simulation.id, num_teams)
    for team in teams:
        db.session.add(team)
    
    db.session.flush()
    
    # Set user-controlled team based on index
    if 0 <= user_team_index < len(teams):
        teams[user_team_index].user_controlled = True
    else:
        # Default to first team if invalid
        teams[0].user_controlled = True
    
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
    all_simulations = Simulation.query.filter_by(user_id=user_id).order_by(Simulation.created_at.desc()).all()
    
    # Filter by is_active (default to True if not set for backwards compatibility)
    active = [s.to_dict() for s in all_simulations if getattr(s, 'is_active', True)]
    quit_sims = [s.to_dict() for s in all_simulations if hasattr(s, 'is_active') and not s.is_active]
    
    return jsonify({
        'simulations': active,
        'quit_simulations': quit_sims
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
    if isinstance(result, tuple):
        payload, status = result
        return jsonify(payload), status
    
    return jsonify(result), 200

@bp.route('/<int:simulation_id>/draft/current', methods=['GET'])
@jwt_required()
def get_current_draft_pick(simulation_id):
    """Get current draft pick info"""
    from models.simulation import Simulation
    from services.draft_service import DraftManager
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404
    
    if simulation.status != 'draft':
        return jsonify({'error': 'Draft not in progress', 'draft_complete': True}), 200
    
    manager = DraftManager(simulation_id)
    pick_info = manager.get_current_pick_info()
    
    if not pick_info:
        return jsonify({'draft_complete': True}), 200
    
    return jsonify(pick_info), 200

@bp.route('/<int:simulation_id>/draft/lottery-order', methods=['GET'])
@jwt_required()
def get_lottery_order(simulation_id):
    """Get first round draft lottery order"""
    from models.simulation import Simulation
    from services.draft_service import DraftManager
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404
    
    manager = DraftManager(simulation_id)
    lottery_order = manager.get_first_round_order()
    
    return jsonify({'lottery_order': lottery_order}), 200

@bp.route('/<int:simulation_id>/draft/history', methods=['GET'])
@jwt_required()
def get_draft_history(simulation_id):
    """Get draft history - all picks made so far"""
    from models.simulation import Simulation
    from services.draft_service import get_draft_history
    from extensions import db
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404
    
    # Ensure we see the latest committed data
    db.session.commit()  # Commit any pending changes
    db.session.expire_all()  # Expire all cached objects to force fresh query
    
    history = get_draft_history(simulation_id)
    
    return jsonify({'history': history}), 200

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

@bp.route('/<int:simulation_id>/enter-playoffs', methods=['POST'])
@jwt_required()
def enter_playoffs(simulation_id):
    """Enter playoffs and create bracket"""
    from models.simulation import Simulation

    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)

    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404

    from services.game_service import enter_playoffs
    result = enter_playoffs(simulation_id)
    status_code = 400 if 'error' in result else 200
    return jsonify(result), status_code

@bp.route('/<int:simulation_id>/playoffs', methods=['GET'])
@jwt_required()
def get_playoffs(simulation_id):
    """Get playoff bracket"""
    from models.simulation import Simulation

    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)

    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404

    from services.game_service import get_playoff_bracket
    result = get_playoff_bracket(simulation_id)
    return jsonify(result), 200

@bp.route('/<int:simulation_id>/playoffs/simulate-game', methods=['POST'])
@jwt_required()
def simulate_playoff_game(simulation_id):
    """Simulate one game in all active playoff series"""
    from models.simulation import Simulation
    from models.game import PlayoffSeries
    from services.game_service import simulate_playoff_game as sim_game

    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)

    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404

    # Get all active series in current round
    active_series = PlayoffSeries.query.filter_by(
        simulation_id=simulation_id,
        season=simulation.current_season,
        status='in_progress'
    ).all()

    if not active_series:
        return jsonify({'error': 'No active playoff series'}), 400

    results = []
    for series in active_series:
        result = sim_game(simulation_id, series.id)
        results.append(result)

    # Check for any errors
    errors = [r for r in results if 'error' in r]
    if errors:
        return jsonify({'errors': errors}), 400

    # Refresh simulation state
    from extensions import db
    db.session.refresh(simulation)
    
    # Check if playoffs are complete - find Stanley Cup winner
    # NOTE: sim_game may have called _check_and_advance_to_next_season internally
    cup_winner = None
    playoffs_complete = False
    
    # Determine which season to check - if we just advanced, check the previous season
    check_season = simulation.current_season
    if simulation.status == 'season':
        check_season = simulation.current_season - 1
    
    # Find completed Stanley Cup Final
    from models.team import Team
    all_complete_series = PlayoffSeries.query.filter_by(
        simulation_id=simulation_id,
        season=check_season,
        status='complete'
    ).order_by(PlayoffSeries.round.desc()).all()
    
    for series_item in all_complete_series:
        higher_team = Team.query.get(series_item.higher_seed_team_id)
        lower_team = Team.query.get(series_item.lower_seed_team_id)
        if higher_team and lower_team and higher_team.conference != lower_team.conference:
            if series_item.winner_team_id:
                winner_team = Team.query.get(series_item.winner_team_id)
                if winner_team:
                    playoffs_complete = True
                    cup_winner = {
                        'id': winner_team.id,
                        'city': winner_team.city,
                        'name': winner_team.name
                    }
            break

    return jsonify({
        'message': f'Simulated {len(results)} games',
        'games_simulated': len(results),
        'playoffs_complete': playoffs_complete,
        'cup_winner': cup_winner
    }), 200

@bp.route('/<int:simulation_id>/playoffs/simulate-round', methods=['POST'])
@jwt_required()
def simulate_playoff_round(simulation_id):
    """Simulate all remaining games in the current active playoff round"""
    from extensions import db
    from models.simulation import Simulation
    from models.game import PlayoffSeries
    from services.game_service import simulate_playoff_game as sim_game

    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)

    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404

    # Get all active series
    active_series = PlayoffSeries.query.filter_by(
        simulation_id=simulation_id,
        season=simulation.current_season,
        status='in_progress'
    ).all()

    if not active_series:
        return jsonify({'error': 'No active playoff series'}), 400

    # Find the current active round (minimum round with active series)
    current_round = min(series.round for series in active_series)
    
    # Get all active series in the current round
    round_series = [s for s in active_series if s.round == current_round]
    
    if not round_series:
        return jsonify({'error': 'No active series in current round'}), 400

    # Simulate games until the round is complete
    total_games = 0
    max_iterations = 100  # Safety limit to prevent infinite loops
    iterations = 0

    while iterations < max_iterations:
        iterations += 1
        games_this_iteration = 0
        
        # Get all active series in the current round (refresh from DB)
        active_round_series = PlayoffSeries.query.filter_by(
            simulation_id=simulation_id,
            season=simulation.current_season,
            round=current_round,
            status='in_progress'
        ).all()
        
        if not active_round_series:
            # Round is complete
            break
        
        # Simulate one game for each active series in the round
        for series in active_round_series:
            result = sim_game(simulation_id, series.id)
            if 'error' not in result:
                games_this_iteration += 1
                total_games += 1
            # If there's an error, we'll still continue with other series
        
        # If no games were simulated this iteration, break
        if games_this_iteration == 0:
            break

    # Refresh simulation from DB to get latest status
    db.session.refresh(simulation)
    
    # Check if playoffs are complete - find Stanley Cup winner
    # NOTE: By this point, _check_and_advance_to_next_season may have already been called
    # inside sim_game when a series completed. So we need to check the PREVIOUS season
    # (current_season - 1 if status is now 'season', otherwise current_season)
    cup_winner = None
    playoffs_complete = False
    
    # Determine which season to check - if we just advanced, check the previous season
    check_season = simulation.current_season
    if simulation.status == 'season':
        # We may have just advanced, check previous season
        check_season = simulation.current_season - 1
    
    # Find completed Stanley Cup Final (series with teams from different conferences)
    from models.team import Team
    all_complete_series = PlayoffSeries.query.filter_by(
        simulation_id=simulation_id,
        season=check_season,
        status='complete'
    ).order_by(PlayoffSeries.round.desc()).all()
    
    for series in all_complete_series:
        higher_team = Team.query.get(series.higher_seed_team_id)
        lower_team = Team.query.get(series.lower_seed_team_id)
        if higher_team and lower_team and higher_team.conference != lower_team.conference:
            # This is the Stanley Cup Final
            if series.winner_team_id:
                winner_team = Team.query.get(series.winner_team_id)
                if winner_team:
                    playoffs_complete = True
                    cup_winner = {
                        'id': winner_team.id,
                        'city': winner_team.city,
                        'name': winner_team.name
                    }
            break
    
    # _check_and_advance_to_next_season is already called inside sim_game when series complete
    # No need to call it again here

    return jsonify({
        'message': f'Simulated round {current_round}',
        'round': current_round,
        'games_simulated': total_games,
        'simulation_status': simulation.status,
        'playoffs_complete': playoffs_complete,
        'cup_winner': cup_winner
    }), 200

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

@bp.route('/<int:simulation_id>/simulation-progress', methods=['GET'])
@jwt_required()
def get_simulation_progress(simulation_id):
    """Get simulation progress for user's controlled team"""
    from models.simulation import Simulation
    from models.team import Team
    from models.game import Game
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404
    
    # Find user's controlled team
    user_team = Team.query.filter_by(
        simulation_id=simulation_id,
        user_controlled=True
    ).first()
    
    if not user_team:
        return jsonify({
            'games_simulated': 0,
            'total_games': 0,
            'percentage': 0
        }), 200
    
    season = simulation.current_season
    
    # Refresh session to see latest commits
    from extensions import db
    db.session.expire_all()
    
    # Get total games for the user's team (regular season only)
    total_games = Game.query.filter_by(
        simulation_id=simulation_id,
        season=season,
        is_playoff=False
    ).filter(
        (Game.home_team_id == user_team.id) | (Game.away_team_id == user_team.id)
    ).count()
    
    # Get simulated games for the user's team
    games_simulated = Game.query.filter_by(
        simulation_id=simulation_id,
        season=season,
        is_playoff=False,
        simulated=True
    ).filter(
        (Game.home_team_id == user_team.id) | (Game.away_team_id == user_team.id)
    ).count()
    
    percentage = (games_simulated / total_games * 100) if total_games > 0 else 0
    
    return jsonify({
        'games_simulated': games_simulated,
        'total_games': total_games,
        'percentage': round(percentage, 1)
    }), 200

@bp.route('/<int:simulation_id>', methods=['DELETE'])
@jwt_required()
def delete_simulation(simulation_id):
    """Delete a simulation"""
    from extensions import db
    from models.simulation import Simulation
    from models.game import PlayoffSeries, Game
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation:
        return jsonify({'error': 'Simulation not found'}), 404
    
    if simulation.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Delete in correct order to avoid foreign key violations:
    # 1. Delete games that reference playoff series (set series_id to NULL or delete them)
    Game.query.filter_by(simulation_id=simulation_id).filter(Game.series_id.isnot(None)).update({Game.series_id: None}, synchronize_session=False)
    
    # 2. Delete playoff series (they reference teams via foreign keys)
    PlayoffSeries.query.filter_by(simulation_id=simulation_id).delete()
    
    # 3. Now delete the simulation (which will cascade to teams, remaining games, etc.)
    db.session.delete(simulation)
    db.session.commit()
    
    return jsonify({'message': 'Simulation deleted successfully'}), 200

@bp.route('/<int:simulation_id>/quit', methods=['POST'])
@jwt_required()
def quit_simulation(simulation_id):
    """Quit/leave a simulation (marks as inactive but doesn't delete)"""
    from extensions import db
    from models.simulation import Simulation
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation:
        return jsonify({'error': 'Simulation not found'}), 404
    
    if simulation.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    simulation.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Simulation quit successfully'}), 200

@bp.route('/<int:simulation_id>/rejoin', methods=['POST'])
@jwt_required()
def rejoin_simulation(simulation_id):
    """Rejoin a previously quit simulation"""
    from extensions import db
    from models.simulation import Simulation
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation:
        return jsonify({'error': 'Simulation not found'}), 404
    
    if simulation.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    simulation.is_active = True
    db.session.commit()
    
    return jsonify({
        'message': 'Simulation rejoined successfully',
        'simulation': simulation.to_dict()
    }), 200

@bp.route('/<int:simulation_id>/draft/sim-to-next', methods=['POST'])
@jwt_required()
def sim_to_next_user_pick(simulation_id):
    """Simulate picks until user's next pick"""
    from models.simulation import Simulation
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404
    
    if simulation.status != 'draft':
        return jsonify({'error': 'Draft not in progress'}), 400
    
    from services.draft_service import sim_to_next_user_pick
    result = sim_to_next_user_pick(simulation_id)
    if result.get('error'):
        return jsonify(result), 400
    
    return jsonify(result), 200

@bp.route('/<int:simulation_id>/draft/sim-next-ai', methods=['POST'])
@jwt_required()
def sim_next_ai_pick(simulation_id):
    """Simulate the next AI pick"""
    from models.simulation import Simulation
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404
    
    if simulation.status != 'draft':
        return jsonify({'error': 'Draft not in progress'}), 400
    
    from services.draft_service import sim_next_ai_pick as sim_next_ai_pick_service
    from extensions import db
    from models.team import Roster
    
    try:
        # Get roster count before the pick for debugging
        roster_count_before = Roster.query.filter_by(simulation_id=simulation_id).count()
        
        result = sim_next_ai_pick_service(simulation_id)
        
        # Get roster count after the pick for debugging
        db.session.commit()  # Ensure we see latest data
        roster_count_after = Roster.query.filter_by(simulation_id=simulation_id).count()
        
        # Add debug info to response
        if result.get('success') or not result.get('error'):
            result['debug'] = {
                'roster_count_before': roster_count_before,
                'roster_count_after': roster_count_after,
                'roster_added': roster_count_after > roster_count_before
            }
            if not (roster_count_after > roster_count_before):
                result['warning'] = f'Roster count did not increase (before: {roster_count_before}, after: {roster_count_after}) - pick may have failed silently'
                print(f"WARNING: AI pick for simulation {simulation_id} did not increase roster count")
        
        return jsonify(result), 200
    except Exception as e:
        print(f"ERROR in sim_next_ai_pick API endpoint: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@bp.route('/<int:simulation_id>/draft/sim-all', methods=['POST'])
@jwt_required()
def sim_all_draft(simulation_id):
    """Simulate the entire draft"""
    from models.simulation import Simulation
    
    user_id = int(get_jwt_identity())
    simulation = Simulation.query.get(simulation_id)
    
    if not simulation or simulation.user_id != user_id:
        return jsonify({'error': 'Simulation not found or unauthorized'}), 404
    
    if simulation.status != 'draft':
        return jsonify({'error': 'Draft not in progress'}), 400
    
    from services.draft_service import sim_all_draft
    result = sim_all_draft(simulation_id)
    
    return jsonify(result), 200
