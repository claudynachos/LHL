from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func, desc

bp = Blueprint('stats', __name__)

def calculate_player_overall(position, is_goalie, off, def_val, phys, lead, const):
    """Calculate overall rating from raw attributes"""
    if is_goalie or position == 'G':
        return float(off)  # For goalies, off stores the gen rating
    # Skaters formula
    off_component = off * 1.1
    def_component = def_val * 0.95
    phys_component = phys * 0.9 * (lead / 100.0) * (const / 100.0)
    return round((off_component + def_component + phys_component) / 2.5, 1)

@bp.route('/season/<int:simulation_id>', methods=['GET'])
@jwt_required()
def get_season_stats(simulation_id):
    """Get current season stats"""
    from extensions import db
    from models.game import PlayerStat, Game
    from models.player import Player
    from models.team import Team, Roster
    from models.simulation import Simulation
    
    season = request.args.get('season', type=int)
    team_id = request.args.get('team_id', type=int)
    position_filter = request.args.get('position_filter')  # 'forward', 'defenseman', or None
    game_type = request.args.get('game_type', default='regular')  # 'regular', 'playoff', or 'all'
    
    # If no season specified, use current_season from simulation
    if season is None:
        simulation = Simulation.query.get(simulation_id)
        if simulation:
            season = simulation.current_season
    
    # Build base query with Game join (needed for filtering and wins calculation)
    # Note: Player.overall is calculated, not a column - we need the raw attributes
    base_query = db.session.query(
        Player.id,
        Player.name,
        Player.position,
        Player.is_goalie,
        Player.off,
        Player.def_.label('def_val'),
        Player.phys,
        Player.lead,
        Player.const,
        Team.id.label('team_id'),
        Team.name.label('team_name'),
        Game.id.label('game_id'),
        Game.home_team_id,
        Game.away_team_id,
        Game.home_score,
        Game.away_score,
        Game.is_playoff,
        PlayerStat.goals,
        PlayerStat.assists,
        PlayerStat.plus_minus,
        PlayerStat.hits,
        PlayerStat.blocks,
        PlayerStat.shots,
        PlayerStat.time_on_ice,
        PlayerStat.takeaways,
        PlayerStat.giveaways,
        # Goalie stats
        PlayerStat.saves,
        PlayerStat.goals_against,
        PlayerStat.shots_against
    ).join(PlayerStat, Player.id == PlayerStat.player_id)\
     .join(Team, PlayerStat.team_id == Team.id)\
     .join(Game, PlayerStat.game_id == Game.id)\
     .filter(Team.simulation_id == simulation_id)
    
    # Apply filters - always filter by season (current_season if not specified)
    if season:
        base_query = base_query.filter(Game.season == season)
    
    # Filter by game type (regular season vs playoffs)
    if game_type == 'regular':
        base_query = base_query.filter(Game.is_playoff == False)
    elif game_type == 'playoff':
        base_query = base_query.filter(Game.is_playoff == True)
    # If game_type == 'all', don't filter by is_playoff
    
    if team_id:
        base_query = base_query.filter(Team.id == team_id)
    
    if position_filter == 'forward':
        base_query = base_query.filter(Player.position.in_(['C', 'LW', 'RW']))
    elif position_filter == 'defenseman':
        base_query = base_query.filter(Player.position.in_(['LD', 'RD']))
    
    # Get all rows for aggregation
    all_rows = base_query.all()
    
    # If no stats found, return all rostered players with 0 stats
    if len(all_rows) == 0:
        # Get all players from rosters for the simulation
        roster_query = db.session.query(
            Player.id,
            Player.name,
            Player.position,
            Player.is_goalie,
            Player.off,
            Player.def_.label('def_val'),
            Player.phys,
            Player.lead,
            Player.const,
            Team.id.label('team_id'),
            Team.name.label('team_name')
        ).join(Roster, Player.id == Roster.player_id)\
         .join(Team, Roster.team_id == Team.id)\
         .filter(Team.simulation_id == simulation_id)
        
        if team_id:
            roster_query = roster_query.filter(Team.id == team_id)
        
        if position_filter == 'forward':
            roster_query = roster_query.filter(Player.position.in_(['C', 'LW', 'RW']))
        elif position_filter == 'defenseman':
            roster_query = roster_query.filter(Player.position.in_(['LD', 'RD']))
        
        rostered_players = roster_query.all()
        
        result_stats = []
        for player in rostered_players:
            stat_dict = {
                'player_id': player.id,
                'player_name': player.name,
                'player_overall': calculate_player_overall(
                    player.position, player.is_goalie, player.off, player.def_val, player.phys, player.lead, player.const
                ),
                'position': player.position,
                'team_id': player.team_id,
                'team_name': player.team_name,
                'games_played': 0,
                'goals': 0,
                'assists': 0,
                'points': 0,
                'plus_minus': 0,
                'hits': 0,
                'blocks': 0,
                'shots': 0,
                'saves': 0,
                'goals_against': 0,
                'shots_against': 0,
                'wins': 0 if player.position == 'G' else None,
                'save_percentage': None,
                'goals_against_average': None
            }
            result_stats.append(stat_dict)
        
        # Sort by overall rating (descending) for initial display
        result_stats.sort(key=lambda x: x.get('player_overall') or 0, reverse=True)
        
        return jsonify({
            'stats': result_stats[:100]
        }), 200
    
    # Aggregate stats by player
    player_stats_dict = {}
    for row in all_rows:
        player_id = row.id
        if player_id not in player_stats_dict:
            player_stats_dict[player_id] = {
                'player_id': row.id,
                'player_name': row.name,
                'position': row.position,
                'player_overall': calculate_player_overall(
                    row.position, row.is_goalie, row.off, row.def_val, row.phys, row.lead, row.const
                ),
                'team_id': row.team_id,
                'team_name': row.team_name,
                'games_played': 0,
                'goals': 0,
                'assists': 0,
                'points': 0,
                'plus_minus': 0,
                'hits': 0,
                'blocks': 0,
                'shots': 0,
                'time_on_ice': 0,
                'takeaways': 0,
                'giveaways': 0,
                'saves': 0,
                'goals_against': 0,
                'shots_against': 0,
                'wins': 0,
                'game_ids': set()
            }
        
        stat = player_stats_dict[player_id]
        
        # Track unique games
        is_new_game = row.game_id not in stat['game_ids']
        if is_new_game:
            stat['game_ids'].add(row.game_id)
            stat['games_played'] += 1
            
            # Calculate wins for goalies
            if row.position == 'G':
                # Determine if goalie's team won
                goalie_team_id = row.team_id
                if goalie_team_id == row.home_team_id:
                    # Goalie is on home team
                    if row.home_score is not None and row.away_score is not None and row.home_score > row.away_score:
                        stat['wins'] += 1
                elif goalie_team_id == row.away_team_id:
                    # Goalie is on away team
                    if row.home_score is not None and row.away_score is not None and row.away_score > row.home_score:
                        stat['wins'] += 1
        
        # Accumulate stats (these can be per-period or per-game, so always add)
        stat['goals'] += row.goals or 0
        stat['assists'] += row.assists or 0
        stat['plus_minus'] += row.plus_minus or 0
        stat['hits'] += row.hits or 0
        stat['blocks'] += row.blocks or 0
        stat['shots'] += row.shots or 0
        stat['time_on_ice'] += row.time_on_ice or 0
        stat['takeaways'] += row.takeaways or 0
        stat['giveaways'] += row.giveaways or 0
        stat['saves'] += row.saves or 0
        stat['goals_against'] += row.goals_against or 0
        stat['shots_against'] += row.shots_against or 0
    
    # Convert to list and calculate percentages
    result_stats = []
    for player_id, stat in player_stats_dict.items():
        stat_dict = {
            'player_id': stat['player_id'],
            'player_name': stat['player_name'],
            'player_overall': stat['player_overall'],
            'team_name': stat['team_name'],
            'position': stat['position'],
            'games_played': stat['games_played'],
            'goals': stat['goals'],
            'assists': stat['assists'],
            'points': stat['goals'] + stat['assists'],  # Points = goals + assists
            'plus_minus': stat['plus_minus'],
            'hits': stat['hits'],
            'blocks': stat['blocks'],
            'shots': stat['shots'],
            'time_on_ice': stat['time_on_ice'],
            'takeaways': stat['takeaways'],
            'giveaways': stat['giveaways'],
            'saves': stat['saves'],
            'goals_against': stat['goals_against'],
            'shots_against': stat['shots_against'],
            'wins': stat['wins'] if stat['position'] == 'G' else None
        }
        
        # Calculate save percentage and GAA for goalies
        if stat['position'] == 'G' and stat['shots_against'] > 0:
            stat_dict['save_percentage'] = round(stat['saves'] / stat['shots_against'] * 100, 3)
            stat_dict['goals_against_average'] = round(stat['goals_against'] / (stat['games_played'] or 1), 2) if stat['games_played'] else 0.0
        else:
            stat_dict['save_percentage'] = None
            stat_dict['goals_against_average'] = None
        
        result_stats.append(stat_dict)
    
    # Sort: goalies by save_percentage (desc), skaters by points (desc)
    # Frontend will filter by viewMode, so this is just for initial ordering
    result_stats.sort(key=lambda x: (
        x['save_percentage'] if x['position'] == 'G' and x['save_percentage'] is not None else 0,
        x['points'] if x['position'] != 'G' else 0
    ), reverse=True)
    
    return jsonify({
        'stats': result_stats[:100]
    }), 200

@bp.route('/all-time/<int:simulation_id>', methods=['GET'])
@jwt_required()
def get_alltime_stats(simulation_id):
    """Get all-time stats across all seasons"""
    from extensions import db
    from models.game import PlayerStat, Game
    from models.player import Player
    from models.team import Team
    
    game_type = request.args.get('game_type', default='regular')  # 'regular', 'playoff', or 'all'
    
    try:
        # Build base query with Game join (needed for wins calculation for goalies)
        base_query = db.session.query(
            Player.id,
            Player.name,
            Player.position,
            Player.is_goalie,
            Player.off,
            Player.def_.label('def_val'),
            Player.phys,
            Player.lead,
            Player.const,
            Team.id.label('team_id'),
            Team.name.label('team_name'),
            Game.id.label('game_id'),
            Game.home_team_id,
            Game.away_team_id,
            Game.home_score,
            Game.away_score,
            Game.is_playoff,
            PlayerStat.goals,
            PlayerStat.assists,
            PlayerStat.plus_minus,
            PlayerStat.hits,
            PlayerStat.blocks,
            PlayerStat.shots,
            # Goalie stats
            PlayerStat.saves,
            PlayerStat.goals_against,
            PlayerStat.shots_against
        ).join(PlayerStat, Player.id == PlayerStat.player_id)\
         .join(Team, PlayerStat.team_id == Team.id)\
         .join(Game, PlayerStat.game_id == Game.id)\
         .filter(Team.simulation_id == simulation_id)
        
        # Filter by game type (regular season vs playoffs)
        if game_type == 'regular':
            base_query = base_query.filter(Game.is_playoff == False)
        elif game_type == 'playoff':
            base_query = base_query.filter(Game.is_playoff == True)
        # If game_type == 'all', don't filter by is_playoff
        
        # Get all rows for aggregation
        all_rows = base_query.all()
        
        # Aggregate stats by player
        player_stats_dict = {}
        for row in all_rows:
            player_id = row.id
            if player_id not in player_stats_dict:
                player_stats_dict[player_id] = {
                    'player_id': row.id,
                    'player_name': row.name,
                    'position': row.position,
                    'player_overall': calculate_player_overall(
                        row.position, row.is_goalie, row.off, row.def_val, row.phys, row.lead, row.const
                    ),
                    'team_id': row.team_id,
                    'team_name': row.team_name,
                    'games_played': 0,
                    'goals': 0,
                    'assists': 0,
                    'points': 0,
                    'plus_minus': 0,
                    'hits': 0,
                    'blocks': 0,
                    'shots': 0,
                    'saves': 0,
                    'goals_against': 0,
                    'shots_against': 0,
                    'wins': 0,
                    'game_ids': set()
                }
            
            stat = player_stats_dict[player_id]
            
            # Track unique games
            is_new_game = row.game_id not in stat['game_ids']
            if is_new_game:
                stat['game_ids'].add(row.game_id)
                stat['games_played'] += 1
                
                # Calculate wins for goalies
                if row.position == 'G':
                    # Determine if goalie's team won
                    goalie_team_id = row.team_id
                    if goalie_team_id == row.home_team_id:
                        # Goalie is on home team
                        if row.home_score is not None and row.away_score is not None and row.home_score > row.away_score:
                            stat['wins'] += 1
                    elif goalie_team_id == row.away_team_id:
                        # Goalie is on away team
                        if row.home_score is not None and row.away_score is not None and row.away_score > row.home_score:
                            stat['wins'] += 1
            
            # Accumulate stats
            stat['goals'] += row.goals or 0
            stat['assists'] += row.assists or 0
            stat['plus_minus'] += row.plus_minus or 0
            stat['hits'] += row.hits or 0
            stat['blocks'] += row.blocks or 0
            stat['shots'] += row.shots or 0
            stat['saves'] += row.saves or 0
            stat['goals_against'] += row.goals_against or 0
            stat['shots_against'] += row.shots_against or 0
        
        # Convert to list and calculate percentages
        result_stats = []
        for player_id, stat in player_stats_dict.items():
            stat_dict = {
                'player_id': stat['player_id'],
                'player_name': stat['player_name'],
                'player_overall': stat['player_overall'],
                'position': stat['position'],
                'team_id': stat['team_id'],
                'team_name': stat['team_name'],
                'games_played': stat['games_played'],
                'goals': stat['goals'],
                'assists': stat['assists'],
                'points': stat['goals'] + stat['assists'],  # Points = goals + assists
                'plus_minus': stat['plus_minus'],
                'hits': stat['hits'],
                'blocks': stat['blocks'],
                'shots': stat['shots'],
                'saves': stat['saves'],
                'goals_against': stat['goals_against'],
                'shots_against': stat['shots_against'],
                'wins': stat['wins'] if stat['position'] == 'G' else None
            }
            
            # Calculate save percentage and GAA for goalies
            if stat['position'] == 'G' and stat['shots_against'] > 0:
                stat_dict['save_percentage'] = round(stat['saves'] / stat['shots_against'] * 100, 3)
                stat_dict['goals_against_average'] = round(stat['goals_against'] / (stat['games_played'] or 1), 2) if stat['games_played'] else 0.0
            else:
                stat_dict['save_percentage'] = None
                stat_dict['goals_against_average'] = None
            
            result_stats.append(stat_dict)
        
        # Sort: goalies by save_percentage (desc), skaters by points (desc)
        result_stats.sort(key=lambda x: (
            x['save_percentage'] if x['position'] == 'G' and x['save_percentage'] is not None else 0,
            x['points'] if x['position'] != 'G' else 0
        ), reverse=True)
        
        return jsonify({
            'stats': result_stats[:100]
        }), 200
    except Exception as e:
        # If there's an error (e.g., no data yet, database issue), return empty list
        print(f"Error in get_alltime_stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'stats': []
        }), 200

@bp.route('/standings/<int:simulation_id>', methods=['GET'])
@jwt_required()
def get_standings(simulation_id):
    """Get league standings"""
    from extensions import db
    from models.game import Standing
    from models.team import Team
    from models.simulation import Simulation
    
    season = request.args.get('season', type=int)
    
    # If no season specified, use current_season from simulation
    if season is None:
        simulation = Simulation.query.get(simulation_id)
        if simulation:
            season = simulation.current_season
    
    query = db.session.query(Standing, Team)\
        .join(Team, Standing.team_id == Team.id)\
        .filter(Standing.simulation_id == simulation_id)
    
    # Always filter by season (current_season if not specified)
    if season:
        query = query.filter(Standing.season == season)
    
    standings = query.all()
    
    # Group by conference
    eastern = []
    western = []
    
    for standing, team in standings:
        standing_dict = standing.to_dict()
        standing_dict['team_name'] = team.name
        standing_dict['conference'] = team.conference
        
        if team.conference == 'Eastern':
            eastern.append(standing_dict)
        else:
            western.append(standing_dict)
    
    # Sort by points
    eastern.sort(key=lambda x: x['points'], reverse=True)
    western.sort(key=lambda x: x['points'], reverse=True)
    
    return jsonify({
        'eastern': eastern,
        'western': western
    }), 200

