from extensions import db

class Player(db.Model):
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(3), nullable=False)  # C, LW, RW, D, G
    player_type = db.Column(db.String(50), nullable=True)  # playmaker, sniper, two-way, power forward, etc.
    era = db.Column(db.String(50), nullable=True)  # Era designation
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
    
    def calculate_overall(self):
        """Calculate overall rating for display purposes only"""
        # Goalies use their "gen" rating directly (stored in off/def/phys/lead attributes)
        if self.is_goalie or self.position == 'G':
            return float(self.off)  # For goalies, all attributes are set to gen rating
        
        # Skaters use the weighted formula
        # Formula: (OFF × 1.1 + DEF × 0.95 + PHYS × 0.9 × (LEAD/100) × (CONST/100)) / 2.5
        off_component = self.off * 1.1
        def_component = self.def_ * 0.95
        phys_component = self.phys * 0.9 * (self.lead / 100.0) * (self.const / 100.0)
        return (off_component + def_component + phys_component) / 2.5
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'position': self.position,
            'player_type': self.player_type,
            'era': self.era,
            'off': self.off,
            'def': self.def_,
            'phys': self.phys,
            'lead': self.lead,
            'const': self.const,
            'is_goalie': self.is_goalie,
            'overall': round(self.calculate_overall(), 1)
        }

class Coach(db.Model):
    __tablename__ = 'coaches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    coach_type = db.Column(db.String(50), nullable=True)  # Coach type
    era = db.Column(db.String(50), nullable=True)  # Era designation
    rating = db.Column(db.Integer, nullable=False)  # Overall coaching rating (0-100)
    
    # Relationships
    teams = db.relationship('Team', backref='coach', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'coach_type': self.coach_type,
            'era': self.era,
            'rating': self.rating
        }
