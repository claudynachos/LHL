from extensions import db
from datetime import datetime

class Simulation(db.Model):
    __tablename__ = 'simulations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    year_length = db.Column(db.Integer, nullable=False)  # 20-25 years
    num_teams = db.Column(db.Integer, nullable=False)  # 4, 6, 8, 10, 12
    current_season = db.Column(db.Integer, default=1)
    current_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, season, playoffs, completed
    draft_pick = db.Column(db.Integer, default=1)  # Current draft pick number
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teams = db.relationship('Team', backref='simulation', lazy=True, cascade='all, delete-orphan')
    games = db.relationship('Game', backref='simulation', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'year_length': self.year_length,
            'num_teams': self.num_teams,
            'current_season': self.current_season,
            'current_date': self.current_date.isoformat() if self.current_date else None,
            'status': self.status,
            'draft_pick': self.draft_pick,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
