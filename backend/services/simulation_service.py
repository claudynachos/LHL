"""Service for calling Rust simulation engine"""
import subprocess
import json
import os
from config import Config
from models.team import Team, LineAssignment
from models.player import Player, Coach

def prepare_game_data(home_team_id, away_team_id, is_playoff=False):
    """Prepare game data for Rust simulator"""
    home_team = Team.query.get(home_team_id)
    away_team = Team.query.get(away_team_id)
    
    if not home_team or not away_team:
        raise ValueError("Team not found")
    
    home_data = get_team_data(home_team)
    away_data = get_team_data(away_team)
    
    return {
        'home_team': home_data,
        'away_team': away_data,
        'is_playoff': is_playoff
    }

def get_effective_play_style(team):
    """Get effective play style - resolve 'auto' to coach-based style"""
    if team.play_style and team.play_style != 'auto':
        return team.play_style
    
    # Auto mode - derive from coach type
    if team.coach_id:
        coach = Coach.query.get(team.coach_id)
        if coach and coach.coach_type:
            coach_type = coach.coach_type.lower()
            if 'defensive' in coach_type or 'trap' in coach_type:
                return 'trap'
            elif 'offensive' in coach_type or 'possession' in coach_type:
                return 'possession'
            elif 'physical' in coach_type or 'grind' in coach_type:
                return 'dump_chase'
            elif 'speed' in coach_type or 'transition' in coach_type:
                return 'rush'
            elif 'aggressive' in coach_type or 'crash' in coach_type:
                return 'shoot_crash'
    
    # Default to possession (balanced)
    return 'possession'

def get_team_data(team):
    """Get team data including lines, play style, and player types"""
    # Get line assignments with player data
    lines = LineAssignment.query.filter_by(team_id=team.id).all()
    
    line_data = []
    for line in lines:
        player = Player.query.get(line.player_id)
        if player:
            line_data.append({
                'line_type': line.line_type,
                'line_number': line.line_number,
                'position': line.position,
                'player': {
                    'id': player.id,
                    'name': player.name,
                    'position': player.position,
                    'player_type': player.player_type or '',
                    'off': player.off,
                    'def': player.def_,
                    'phys': player.phys,
                    'lead': player.lead,
                    'const': player.const
                }
            })
    
    # Get coach
    coach_data = None
    if team.coach_id:
        coach = Coach.query.get(team.coach_id)
        if coach:
            coach_data = {
                'id': coach.id,
                'name': coach.name,
                'rating': coach.rating,
                'coach_type': coach.coach_type or ''
            }
    
    return {
        'id': team.id,
        'name': team.name,
        'city': team.city,
        'lines': line_data,
        'coach': coach_data,
        'play_style': get_effective_play_style(team)
    }

def simulate_game(home_team_id, away_team_id, is_playoff=False):
    """Simulate a single game using Rust engine"""
    # Prepare input data
    game_data = prepare_game_data(home_team_id, away_team_id, is_playoff)
    game_json = json.dumps(game_data)
    
    # Get Rust binary path
    rust_binary = Config.RUST_BINARY_PATH
    
    if not os.path.exists(rust_binary):
        raise RuntimeError(
            f"Rust simulation binary not found at {rust_binary}. "
            f"Please compile it by running: cd simulation && cargo build --release"
        )
    
    try:
        # Call Rust binary
        process = subprocess.Popen(
            [rust_binary, '--input', '-', '--output', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate(input=game_json.encode())
        
        if process.returncode != 0:
            raise RuntimeError(f"Rust simulation failed: {stderr.decode()}")
        
        # Parse result
        result = json.loads(stdout.decode())
        return result
        
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Rust simulation output: {e}")
    except Exception as e:
        raise RuntimeError(f"Error calling Rust simulator: {e}")

