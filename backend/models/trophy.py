from extensions import db
from datetime import datetime

class Trophy(db.Model):
    __tablename__ = 'trophies'
    
    id = db.Column(db.Integer, primary_key=True)
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulations.id'), nullable=False)
    season = db.Column(db.Integer, nullable=False)
    trophy_name = db.Column(db.String(100), nullable=False)  # e.g., "Stanley Cup", "Hart Trophy"
    trophy_type = db.Column(db.String(20), nullable=False)  # 'team' or 'individual'
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)  # For individual awards
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)  # For team awards
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    player = db.relationship('Player', backref='trophies', lazy=True)
    team = db.relationship('Team', backref='trophies', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'simulation_id': self.simulation_id,
            'season': self.season,
            'trophy_name': self.trophy_name,
            'trophy_type': self.trophy_type,
            'player_id': self.player_id,
            'team_id': self.team_id,
            'player_name': self.player.name if self.player else None,
            'team_name': self.team.name if self.team else None,
            'team_city': self.team.city if self.team else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
