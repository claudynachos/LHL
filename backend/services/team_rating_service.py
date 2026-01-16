"""Service for calculating team overall ratings"""
from extensions import db
from models.team import Team, Roster, LineAssignment
from models.player import Player
from models.player import Coach

# Ice time percentages (from simulation algorithm)
FORWARD_LINE_TIME = [0.35, 0.30, 0.20, 0.15]  # Lines 1-4
DEFENSE_LINE_TIME = [0.45, 0.35, 0.20]  # Pairs 1-3

# Skill weightings [OFF, DEF, PHYS] for each line/pair
FORWARD_WEIGHTS = [
    [0.50, 0.30, 0.20],  # Line 1
    [0.40, 0.40, 0.20],  # Line 2
    [0.25, 0.50, 0.25],  # Line 3
    [0.20, 0.40, 0.40],  # Line 4
]

DEFENSE_WEIGHTS = [
    [0.40, 0.30, 0.30],  # Pair 1
    [0.30, 0.40, 0.30],  # Pair 2
    [0.10, 0.50, 0.40],  # Pair 3
]


def calculate_line_rating(players, weights):
    """Calculate rating for a line/pair based on player attributes and weights"""
    if not players:
        return 50.0
    
    total_rating = 0.0
    leadership_boost = 0.0
    
    for player in players:
        rating = (player.off * weights[0]) + (player.def_ * weights[1]) + (player.phys * weights[2])
        total_rating += rating
        leadership_boost += player.lead
    
    # Apply leadership boost (avg team leadership adds 0-5% boost)
    avg_leadership = leadership_boost / len(players)
    leadership_multiplier = 1.0 + (avg_leadership - 75.0) / 1000.0
    
    return (total_rating / len(players)) * leadership_multiplier


def calculate_team_overall(team_id):
    """Calculate team overall rating based on lines, ice time, and coach"""
    team = Team.query.get(team_id)
    if not team:
        return None
    
    # Get all line assignments
    line_assignments = LineAssignment.query.filter_by(team_id=team_id).all()
    
    if not line_assignments:
        # No lines assigned, return None
        return None
    
    # Build player lookup
    player_map = {}
    for assignment in line_assignments:
        if assignment.player_id not in player_map:
            player = Player.query.get(assignment.player_id)
            if player:
                player_map[assignment.player_id] = player
    
    total_rating = 0.0
    weight_sum = 0.0
    
    # Calculate forward lines rating
    for line_num in range(1, 5):
        line_players = []
        for assignment in line_assignments:
            if (assignment.line_type == 'forward' and 
                assignment.line_number == line_num and 
                assignment.player_id in player_map):
                line_players.append(player_map[assignment.player_id])
        
        if line_players:
            line_rating = calculate_line_rating(line_players, FORWARD_WEIGHTS[line_num - 1])
            ice_time = FORWARD_LINE_TIME[line_num - 1]
            total_rating += line_rating * ice_time
            weight_sum += ice_time
    
    # Calculate defense pairs rating
    for pair_num in range(1, 4):
        pair_players = []
        for assignment in line_assignments:
            if (assignment.line_type == 'defense' and 
                assignment.line_number == pair_num and 
                assignment.player_id in player_map):
                pair_players.append(player_map[assignment.player_id])
        
        if pair_players:
            pair_rating = calculate_line_rating(pair_players, DEFENSE_WEIGHTS[pair_num - 1])
            ice_time = DEFENSE_LINE_TIME[pair_num - 1]
            total_rating += pair_rating * ice_time
            weight_sum += ice_time
    
    # Get goalie rating (use starter G1, weighted 30%)
    goalie_assignments = [a for a in line_assignments if a.line_type == 'goalie' and a.line_number == 1]
    if goalie_assignments and goalie_assignments[0].player_id in player_map:
        goalie = player_map[goalie_assignments[0].player_id]
        # For goalies, rating is average of off/def/phys (all set to gen rating)
        goalie_rating = (goalie.off + goalie.def_ + goalie.phys) / 3.0
        total_rating += goalie_rating * 0.3
        weight_sum += 0.3
    
    if weight_sum == 0:
        return None
    
    # Calculate base team rating
    base_rating = total_rating / weight_sum
    
    # Apply coach modifier
    coach_modifier = 1.0
    if team.coach_id:
        coach = Coach.query.get(team.coach_id)
        if coach:
            coach_modifier = 1.0 + (coach.rating - 75.0) / 500.0  # ±5% max
    
    final_rating = base_rating * coach_modifier
    
    return round(final_rating, 1)
