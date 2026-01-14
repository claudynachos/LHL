from extensions import db

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulations.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # MTL, BOS, etc
    city = db.Column(db.String(100), nullable=False)  # Montreal, Boston, etc
    conference = db.Column(db.String(10), nullable=False)  # Eastern, Western
    user_controlled = db.Column(db.Boolean, default=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id'), nullable=True)
    
    # Relationships
    roster_entries = db.relationship('Roster', backref='team', lazy=True, cascade='all, delete-orphan')
    line_assignments = db.relationship('LineAssignment', backref='team', lazy=True, cascade='all, delete-orphan')
    home_games = db.relationship('Game', foreign_keys='Game.home_team_id', backref='home_team', lazy=True)
    away_games = db.relationship('Game', foreign_keys='Game.away_team_id', backref='away_team', lazy=True)
    standings = db.relationship('Standing', backref='team', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'simulation_id': self.simulation_id,
            'name': self.name,
            'city': self.city,
            'conference': self.conference,
            'user_controlled': self.user_controlled,
            'coach_id': self.coach_id
        }

class Roster(db.Model):
    __tablename__ = 'rosters'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulations.id'), nullable=False)
    season_acquired = db.Column(db.Integer, default=1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'player_id': self.player_id,
            'simulation_id': self.simulation_id,
            'season_acquired': self.season_acquired
        }

class LineAssignment(db.Model):
    __tablename__ = 'line_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    line_type = db.Column(db.String(10), nullable=False)  # forward, defense, goalie
    line_number = db.Column(db.Integer, nullable=False)  # 1-4 for forwards, 1-3 for defense, 1-2 for goalies
    position = db.Column(db.String(3), nullable=False)  # LW, C, RW, LD, RD, G
    
    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'player_id': self.player_id,
            'line_type': self.line_type,
            'line_number': self.line_number,
            'position': self.position
        }
