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
    
    # Simulate 3 periods (simple approximation for mock)
    # This mirrors the Rust simulator: 3 periods, then OT if tied
    home_score = 0
    away_score = 0
    
    # Simulate 3 periods (each team has chance to score)
    for period in range(3):
        # Each period, both teams can score 0-3 goals
        home_goals = random.randint(0, 3) if random.random() < 0.7 else 0
        away_goals = random.randint(0, 3) if random.random() < 0.7 else 0
        home_score += home_goals
        away_score += away_goals
    
    went_to_overtime = False
    went_to_shootout = False
    
    # If tied after regulation (3 periods), go to overtime (like Rust simulator)
    if home_score == away_score:
        went_to_overtime = True
        # Overtime: 3-on-3, higher scoring chance (sudden death)
        # Simulate until someone scores
        ot_iterations = 0
        while home_score == away_score and ot_iterations < 10:  # Safety limit
            ot_iterations += 1
            # Higher chance of scoring in OT
            if random.random() < 0.3:  # 30% chance per "shot" in OT
                if random.random() < 0.5:
                    home_score += 1
                else:
                    away_score += 1
                    break
        
        # If still tied after OT (shouldn't happen often, but handle it)
        if home_score == away_score:
            went_to_shootout = True
            # Shootout winner (50/50)
            if random.random() < 0.5:
                home_score += 1
            else:
                away_score += 1
    
    # Get players for both teams
    home_lines = LineAssignment.query.filter_by(team_id=home_team_id).all()
    away_lines = LineAssignment.query.filter_by(team_id=away_team_id).all()
    
    # Find goalies and select which one plays (60% G1, 40% G2)
    home_goalies = [l for l in home_lines if l.line_type == 'goalie']
    away_goalies = [l for l in away_lines if l.line_type == 'goalie']
    
    home_goalie_line = home_goalies[0] if home_goalies and random.random() < 0.6 else (home_goalies[1] if len(home_goalies) > 1 else home_goalies[0] if home_goalies else None)
    away_goalie_line = away_goalies[0] if away_goalies and random.random() < 0.6 else (away_goalies[1] if len(away_goalies) > 1 else away_goalies[0] if away_goalies else None)
    
    home_stats = []
    for line in home_lines:
        player = Player.query.get(line.player_id)
        if not player:
            continue
            
        is_goalie = player.position == 'G'
        is_playing_goalie = home_goalie_line and line.id == home_goalie_line.id
        
        if is_goalie:
            # Only create stats for the goalie that plays
            if is_playing_goalie:
                shots_against = random.randint(20, 40)
                saves = max(0, shots_against - away_score)
                home_stats.append({
                    'player_id': player.id,
                    'player_name': player.name,
                    'goals': 0,
                    'assists': 0,
                    'shots': 0,
                    'hits': 0,
                    'blocks': 0,
                    'plus_minus': 0,
                    'saves': saves,
                    'goals_against': away_score,
                    'shots_against': shots_against
                })
        else:
            # Skater stats
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
        if not player:
            continue
            
        is_goalie = player.position == 'G'
        is_playing_goalie = away_goalie_line and line.id == away_goalie_line.id
        
        if is_goalie:
            # Only create stats for the goalie that plays
            if is_playing_goalie:
                shots_against = random.randint(20, 40)
                saves = max(0, shots_against - home_score)
                away_stats.append({
                    'player_id': player.id,
                    'player_name': player.name,
                    'goals': 0,
                    'assists': 0,
                    'shots': 0,
                    'hits': 0,
                    'blocks': 0,
                    'plus_minus': 0,
                    'saves': saves,
                    'goals_against': home_score,
                    'shots_against': shots_against
                })
        else:
            # Skater stats
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
        'away_stats': away_stats,
        'went_to_overtime': went_to_overtime,
        'went_to_shootout': went_to_shootout
    }
