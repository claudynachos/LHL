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

def get_team_data(team):
    """Get team data including lines"""
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
                'rating': coach.rating
            }
    
    return {
        'id': team.id,
        'name': team.name,
        'city': team.city,
        'lines': line_data,
        'coach': coach_data
    }

def simulate_game(home_team_id, away_team_id, is_playoff=False):
    """Simulate a single game using Rust engine"""
    # Prepare input data
    game_data = prepare_game_data(home_team_id, away_team_id, is_playoff)
    game_json = json.dumps(game_data)
    
    # Get Rust binary path
    rust_binary = Config.RUST_BINARY_PATH
    
    if not os.path.exists(rust_binary):
        # Fallback to mock simulation if binary not found
        return mock_simulate_game(home_team_id, away_team_id)
    
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
        
    except Exception as e:
        print(f"Error calling Rust simulator: {e}")
        # Fallback to mock
        return mock_simulate_game(home_team_id, away_team_id)

def mock_simulate_game(home_team_id, away_team_id):
    """Mock simulation for testing when Rust binary not available"""
    import random
    
    # Simple random score generation
    home_score = random.randint(0, 6)
    away_score = random.randint(0, 6)
    
    # Get players for both teams
    home_lines = LineAssignment.query.filter_by(team_id=home_team_id).all()
    away_lines = LineAssignment.query.filter_by(team_id=away_team_id).all()
    
    home_stats = []
    for line in home_lines:
        player = Player.query.get(line.player_id)
        if player:
            goals = random.randint(0, 2) if random.random() < 0.3 else 0
            assists = random.randint(0, 2) if random.random() < 0.4 else 0
            
            home_stats.append({
                'player_id': player.id,
                'player_name': player.name,
                'goals': goals,
                'assists': assists,
                'shots': random.randint(0, 5),
                'hits': random.randint(0, 4),
                'blocks': random.randint(0, 3),
                'plus_minus': home_score - away_score,
                'saves': 0,
                'goals_against': 0,
                'shots_against': 0
            })
    
    away_stats = []
    for line in away_lines:
        player = Player.query.get(line.player_id)
        if player:
            goals = random.randint(0, 2) if random.random() < 0.3 else 0
            assists = random.randint(0, 2) if random.random() < 0.4 else 0
            
            away_stats.append({
                'player_id': player.id,
                'player_name': player.name,
                'goals': goals,
                'assists': assists,
                'shots': random.randint(0, 5),
                'hits': random.randint(0, 4),
                'blocks': random.randint(0, 3),
                'plus_minus': away_score - home_score,
                'saves': 0,
                'goals_against': 0,
                'shots_against': 0
            })
    
    return {
        'home_score': home_score,
        'away_score': away_score,
        'home_stats': home_stats,
        'away_stats': away_stats
    }
