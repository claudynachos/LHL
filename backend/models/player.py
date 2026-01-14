from extensions import db

class Player(db.Model):
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(3), nullable=False)  # C, LW, RW, D, G
    off = db.Column(db.Integer, nullable=False)  # Offense (0-100)
    def_ = db.Column('def', db.Integer, nullable=False)  # Defense (0-100)
    phys = db.Column(db.Integer, nullable=False)  # Physicality (0-100)
    lead = db.Column(db.Integer, nullable=False)  # Leadership (0-100)
    const = db.Column(db.Integer, nullable=False)  # Consistency (0-100)
    is_goalie = db.Column(db.Boolean, default=False)
    
    # Relationships
    roster_entries = db.relationship('Roster', backref='player', lazy=True)
    line_assignments = db.relationship('LineAssignment', backref='player', lazy=True)
    stats = db.relationship('PlayerStat', backref='player', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'position': self.position,
            'off': self.off,
            'def': self.def_,
            'phys': self.phys,
            'lead': self.lead,
            'const': self.const,
            'is_goalie': self.is_goalie
        }

class Coach(db.Model):
    __tablename__ = 'coaches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Overall coaching rating (0-100)
    
    # Relationships
    teams = db.relationship('Team', backref='coach', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'rating': self.rating
        }
