"""League initialization and management"""
from models.team import Team

# Team configurations based on league size
# East Conference: MTL, BOS, TOR (6+), PHI (8+), PIT (10+), QC (12+)
# West Conference: DET, CHI, NYR (6+), LA (8+), EDM (10+), NYI (12+)
TEAM_CONFIGS = {
    4: [
        {'name': 'MTL', 'city': 'Montreal', 'conference': 'Eastern'},
        {'name': 'BOS', 'city': 'Boston', 'conference': 'Eastern'},
        {'name': 'DET', 'city': 'Detroit', 'conference': 'Western'},
        {'name': 'CHI', 'city': 'Chicago', 'conference': 'Western'},
    ],
    6: [
        {'name': 'MTL', 'city': 'Montreal', 'conference': 'Eastern'},
        {'name': 'BOS', 'city': 'Boston', 'conference': 'Eastern'},
        {'name': 'TOR', 'city': 'Toronto', 'conference': 'Eastern'},
        {'name': 'DET', 'city': 'Detroit', 'conference': 'Western'},
        {'name': 'CHI', 'city': 'Chicago', 'conference': 'Western'},
        {'name': 'NYR', 'city': 'New York', 'conference': 'Western'},
    ],
    8: [
        {'name': 'MTL', 'city': 'Montreal', 'conference': 'Eastern'},
        {'name': 'BOS', 'city': 'Boston', 'conference': 'Eastern'},
        {'name': 'TOR', 'city': 'Toronto', 'conference': 'Eastern'},
        {'name': 'PHI', 'city': 'Philadelphia', 'conference': 'Eastern'},
        {'name': 'DET', 'city': 'Detroit', 'conference': 'Western'},
        {'name': 'CHI', 'city': 'Chicago', 'conference': 'Western'},
        {'name': 'NYR', 'city': 'New York', 'conference': 'Western'},
        {'name': 'LA', 'city': 'Los Angeles', 'conference': 'Western'},
    ],
    10: [
        {'name': 'MTL', 'city': 'Montreal', 'conference': 'Eastern'},
        {'name': 'BOS', 'city': 'Boston', 'conference': 'Eastern'},
        {'name': 'TOR', 'city': 'Toronto', 'conference': 'Eastern'},
        {'name': 'PHI', 'city': 'Philadelphia', 'conference': 'Eastern'},
        {'name': 'PIT', 'city': 'Pittsburgh', 'conference': 'Eastern'},
        {'name': 'DET', 'city': 'Detroit', 'conference': 'Western'},
        {'name': 'CHI', 'city': 'Chicago', 'conference': 'Western'},
        {'name': 'NYR', 'city': 'New York', 'conference': 'Western'},
        {'name': 'LA', 'city': 'Los Angeles', 'conference': 'Western'},
        {'name': 'EDM', 'city': 'Edmonton', 'conference': 'Western'},
    ],
    12: [
        {'name': 'MTL', 'city': 'Montreal', 'conference': 'Eastern'},
        {'name': 'BOS', 'city': 'Boston', 'conference': 'Eastern'},
        {'name': 'TOR', 'city': 'Toronto', 'conference': 'Eastern'},
        {'name': 'PHI', 'city': 'Philadelphia', 'conference': 'Eastern'},
        {'name': 'PIT', 'city': 'Pittsburgh', 'conference': 'Eastern'},
        {'name': 'QC', 'city': 'Quebec', 'conference': 'Eastern'},
        {'name': 'DET', 'city': 'Detroit', 'conference': 'Western'},
        {'name': 'CHI', 'city': 'Chicago', 'conference': 'Western'},
        {'name': 'NYR', 'city': 'New York', 'conference': 'Western'},
        {'name': 'LA', 'city': 'Los Angeles', 'conference': 'Western'},
        {'name': 'EDM', 'city': 'Edmonton', 'conference': 'Western'},
        {'name': 'NYI', 'city': 'New York Islanders', 'conference': 'Western'},
    ]
}

def initialize_league(simulation_id, num_teams, user_team_id=None):
    """Initialize league teams based on size"""
    if num_teams not in TEAM_CONFIGS:
        raise ValueError(f"Invalid number of teams: {num_teams}")
    
    teams = []
    team_configs = TEAM_CONFIGS[num_teams]
    
    # Create all teams (all AI-controlled initially)
    for i, config in enumerate(team_configs):
        team = Team(
            simulation_id=simulation_id,
            name=config['name'],
            city=config['city'],
            conference=config['conference'],
            user_controlled=False  # Will be set based on user_team_id
        )
        teams.append(team)
    
    return teams

def get_playoff_teams(num_teams):
    """Determine how many teams make playoffs"""
    if num_teams == 4:
        return 4  # All teams make playoffs
    elif num_teams == 6:
        return 4  # Top 4 make playoffs
    else:  # 8, 10, 12 teams
        return 8  # Top 8 make playoffs
