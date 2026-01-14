"""Draft service for handling snake draft logic"""
from app import db
from models.team import Team, Roster
from models.player import Player, Coach
import random

class DraftManager:
    def __init__(self, simulation_id):
        self.simulation_id = simulation_id
        self.teams = Team.query.filter_by(simulation_id=simulation_id).order_by(Team.id).all()
        self.num_teams = len(self.teams)
        self.current_round = 1
        self.current_pick = 0
        self.total_rounds = 21  # 20 players + 1 coach
        
    def get_draft_order(self):
        """Get snake draft order"""
        order = []
        for round_num in range(1, self.total_rounds + 1):
            if round_num % 2 == 1:  # Odd rounds: 1 -> N
                order.extend([(round_num, team.id) for team in self.teams])
            else:  # Even rounds: N -> 1
                order.extend([(round_num, team.id) for team in reversed(self.teams)])
        return order
    
    def get_current_pick_info(self):
        """Get info about current pick"""
        order = self.get_draft_order()
        if self.current_pick >= len(order):
            return None  # Draft complete
        
        round_num, team_id = order[self.current_pick]
        team = Team.query.get(team_id)
        
        return {
            'round': round_num,
            'pick': self.current_pick + 1,
            'total_picks': len(order),
            'team_id': team_id,
            'team_name': team.name,
            'is_user_team': team.user_controlled
        }
    
    def make_pick(self, player_id=None, coach_id=None):
        """Make a draft pick"""
        pick_info = self.get_current_pick_info()
        if not pick_info:
            return {'error': 'Draft already completed'}
        
        team_id = pick_info['team_id']
        round_num = pick_info['round']
        
        # Last round is for coaches
        if round_num == self.total_rounds:
            if not coach_id:
                # Auto-pick random coach for AI
                available_coaches = Coach.query.filter(
                    ~Coach.id.in_(
                        db.session.query(Team.coach_id).filter(Team.coach_id.isnot(None))
                    )
                ).all()
                coach_id = random.choice(available_coaches).id if available_coaches else None
            
            if coach_id:
                team = Team.query.get(team_id)
                team.coach_id = coach_id
                db.session.commit()
        else:
            # Player pick
            if not player_id:
                # Auto-pick for AI team
                player_id = self.auto_pick_player(team_id, round_num)
            
            if player_id:
                # Add player to roster
                roster_entry = Roster(
                    team_id=team_id,
                    player_id=player_id,
                    simulation_id=self.simulation_id,
                    season_acquired=1
                )
                db.session.add(roster_entry)
                db.session.commit()
        
        self.current_pick += 1
        
        return {
            'success': True,
            'pick_info': pick_info,
            'next_pick': self.get_current_pick_info()
        }
    
    def auto_pick_player(self, team_id, round_num):
        """AI logic for picking best available player"""
        # Get already drafted players
        drafted = db.session.query(Roster.player_id).filter_by(
            simulation_id=self.simulation_id
        ).all()
        drafted_ids = [p[0] for p in drafted]
        
        # Get team's current roster to determine needs
        roster = db.session.query(Player).join(Roster).filter(
            Roster.team_id == team_id
        ).all()
        
        position_counts = {
            'C': len([p for p in roster if p.position == 'C']),
            'LW': len([p for p in roster if p.position == 'LW']),
            'RW': len([p for p in roster if p.position == 'RW']),
            'D': len([p for p in roster if p.position == 'D']),
            'G': len([p for p in roster if p.position == 'G'])
        }
        
        # Determine position need (target: 4C, 4LW, 4RW, 6D, 2G)
        targets = {'C': 4, 'LW': 4, 'RW': 4, 'D': 6, 'G': 2}
        needs = []
        for pos, target in targets.items():
            if position_counts.get(pos, 0) < target:
                needs.append(pos)
        
        if not needs:
            needs = ['C', 'LW', 'RW', 'D']  # Default to forwards/D
        
        # Find best available player at needed position
        available = Player.query.filter(
            ~Player.id.in_(drafted_ids),
            Player.position.in_(needs)
        ).order_by((Player.off + Player.def_ + Player.phys).desc()).first()
        
        if not available:
            # Fallback: any available player
            available = Player.query.filter(
                ~Player.id.in_(drafted_ids)
            ).order_by((Player.off + Player.def_ + Player.phys).desc()).first()
        
        return available.id if available else None

def process_draft_pick(simulation_id, data):
    """Process a draft pick"""
    manager = DraftManager(simulation_id)
    
    player_id = data.get('player_id')
    coach_id = data.get('coach_id')
    
    result = manager.make_pick(player_id=player_id, coach_id=coach_id)
    
    # Check if draft is complete
    if not result.get('next_pick'):
        from models.simulation import Simulation
        sim = Simulation.query.get(simulation_id)
        sim.status = 'season'
        db.session.commit()
        
        result['draft_complete'] = True
    
    return result
