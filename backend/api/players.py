from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

bp = Blueprint('players', __name__)

@bp.route('/', methods=['GET'])
@jwt_required()
def get_all_players():
    """Get all available players for drafting"""
    from models.player import Player
    
    players = Player.query.all()
    
    return jsonify({
        'players': [p.to_dict() for p in players]
    }), 200

@bp.route('/<int:player_id>', methods=['GET'])
@jwt_required()
def get_player(player_id):
    """Get a specific player"""
    from models.player import Player
    
    player = Player.query.get(player_id)
    
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    return jsonify(player.to_dict()), 200
