"""Service for managing team line assignments"""
from extensions import db
from models.team import Team, Roster, LineAssignment
from models.player import Player


def auto_populate_lines(team_id):
    """Auto-populate lines for a team based on roster"""
    team = Team.query.get(team_id)
    if not team:
        return False
    
    # Check if lines already exist
    existing_lines = LineAssignment.query.filter_by(team_id=team_id).count()
    if existing_lines > 0:
        return False  # Lines already populated
    
    # Get roster players (ordered by draft order via Roster.id)
    roster_query = db.session.query(Player, Roster.id.label('roster_order')).join(Roster).filter(
        Roster.team_id == team_id,
        Roster.simulation_id == team.simulation_id
    ).order_by(Roster.id).all()
    
    # Create a mapping of player to draft order
    player_draft_order = {player.id: roster_order for player, roster_order in roster_query}
    roster = [player for player, _ in roster_query]
    
    # Separate players by position
    centers = [p for p in roster if p.position == 'C']
    left_wings = [p for p in roster if p.position == 'LW']
    right_wings = [p for p in roster if p.position == 'RW']
    # Only LD and RD (no generic D)
    left_defensemen = [p for p in roster if p.position == 'LD']
    right_defensemen = [p for p in roster if p.position == 'RD']
    goalies = [p for p in roster if p.position == 'G']
    
    # Sort by overall rating (best players first)
    def get_overall(player):
        return (player.off * 1.1 + player.def_ * 0.95 + player.phys * 0.9) * (player.lead / 100) * (player.const / 100) / 2.5
    
    centers.sort(key=get_overall, reverse=True)
    left_wings.sort(key=get_overall, reverse=True)
    right_wings.sort(key=get_overall, reverse=True)
    left_defensemen.sort(key=get_overall, reverse=True)
    right_defensemen.sort(key=get_overall, reverse=True)
    goalies.sort(key=get_overall, reverse=True)
    
    line_assignments = []
    
    # Assign forward lines (4 lines: LW, C, RW)
    for line_num in range(1, 5):
        if line_num <= len(left_wings):
            line_assignments.append(LineAssignment(
                team_id=team_id,
                player_id=left_wings[line_num - 1].id,
                line_type='forward',
                line_number=line_num,
                position='LW'
            ))
        if line_num <= len(centers):
            line_assignments.append(LineAssignment(
                team_id=team_id,
                player_id=centers[line_num - 1].id,
                line_type='forward',
                line_number=line_num,
                position='C'
            ))
        if line_num <= len(right_wings):
            line_assignments.append(LineAssignment(
                team_id=team_id,
                player_id=right_wings[line_num - 1].id,
                line_type='forward',
                line_number=line_num,
                position='RW'
            ))
    
    # Assign defense pairs (3 pairs: LD, RD)
    # Simple assignment: best LD to pair 1, best RD to pair 1, etc.
    for pair_num in range(1, 4):
        # Assign LD for this pair
        if pair_num <= len(left_defensemen):
            line_assignments.append(LineAssignment(
                team_id=team_id,
                player_id=left_defensemen[pair_num - 1].id,
                line_type='defense',
                line_number=pair_num,
                position='LD'
            ))
        
        # Assign RD for this pair
        if pair_num <= len(right_defensemen):
            line_assignments.append(LineAssignment(
                team_id=team_id,
                player_id=right_defensemen[pair_num - 1].id,
                line_type='defense',
                line_number=pair_num,
                position='RD'
            ))
    
    # Assign goalies (2 goalies: G1, G2)
    for goalie_num in range(1, 3):
        if goalie_num <= len(goalies):
            line_assignments.append(LineAssignment(
                team_id=team_id,
                player_id=goalies[goalie_num - 1].id,
                line_type='goalie',
                line_number=goalie_num,
                position='G'
            ))
    
    # Add all assignments to database
    for assignment in line_assignments:
        db.session.add(assignment)
    
    db.session.commit()
    return True


def auto_populate_all_teams(simulation_id):
    """Auto-populate lines for all teams in a simulation"""
    teams = Team.query.filter_by(simulation_id=simulation_id).all()
    populated_count = 0
    
    for team in teams:
        if auto_populate_lines(team.id):
            populated_count += 1
    
    return populated_count
