from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('admin', __name__)

def admin_required():
    """Decorator to check if user is admin"""
    from models.user import User
    
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    return None

@bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """List all users (admin only)"""
    from models.user import User
    
    error = admin_required()
    if error:
        return error
    
    users = User.query.all()
    
    return jsonify({
        'users': [u.to_dict() for u in users]
    }), 200

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete a user (admin only)"""
    from app import db
    from models.user import User
    
    error = admin_required()
    if error:
        return error
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200

@bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    """Get analytics dashboard data (admin only)"""
    from models.user import User
    from models.simulation import Simulation
    
    error = admin_required()
    if error:
        return error
    
    # Total users
    total_users = User.query.count()
    
    # Active simulations
    active_sims = Simulation.query.filter(Simulation.status.in_(['draft', 'season', 'playoffs'])).count()
    
    # Most popular teams (placeholder)
    # Would need more complex query to track actual popularity
    
    return jsonify({
        'total_users': total_users,
        'active_simulations': active_sims,
        'completed_simulations': Simulation.query.filter_by(status='completed').count(),
        'popular_teams': []
    }), 200

@bp.route('/database-health', methods=['GET'])
@jwt_required()
def database_health():
    """Get database health metrics (admin only)"""
    from models.user import User
    from models.player import Player, Coach
    from models.game import Game, PlayerStat
    from models.simulation import Simulation
    
    error = admin_required()
    if error:
        return error
    
    metrics = {
        'users': User.query.count(),
        'simulations': Simulation.query.count(),
        'players': Player.query.count(),
        'coaches': Coach.query.count(),
        'games_simulated': Game.query.filter_by(simulated=True).count(),
        'total_player_stats': PlayerStat.query.count()
    }
    
    return jsonify(metrics), 200
