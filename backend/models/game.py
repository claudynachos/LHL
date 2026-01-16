from extensions import db
from datetime import datetime

class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulations.id'), nullable=False)
    season = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    home_score = db.Column(db.Integer, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)
    is_playoff = db.Column(db.Boolean, default=False)
    playoff_round = db.Column(db.Integer, nullable=True)  # 1-4
    series_id = db.Column(db.Integer, db.ForeignKey('playoff_series.id'), nullable=True)
    simulated = db.Column(db.Boolean, default=False)
    
    # Relationships
    player_stats = db.relationship('PlayerStat', backref='game', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'simulation_id': self.simulation_id,
            'season': self.season,
            'date': self.date.isoformat() if self.date else None,
            'home_team_id': self.home_team_id,
            'away_team_id': self.away_team_id,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'is_playoff': self.is_playoff,
            'playoff_round': self.playoff_round,
            'series_id': self.series_id,
            'simulated': self.simulated
        }

class PlayoffSeries(db.Model):
    __tablename__ = 'playoff_series'

    id = db.Column(db.Integer, primary_key=True)
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulations.id'), nullable=False)
    season = db.Column(db.Integer, nullable=False)
    round = db.Column(db.Integer, nullable=False)
    higher_seed_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    lower_seed_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    higher_seed_wins = db.Column(db.Integer, default=0)
    lower_seed_wins = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, complete
    winner_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    next_game_number = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    games = db.relationship('Game', backref='series', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'simulation_id': self.simulation_id,
            'season': self.season,
            'round': self.round,
            'higher_seed_team_id': self.higher_seed_team_id,
            'lower_seed_team_id': self.lower_seed_team_id,
            'higher_seed_wins': self.higher_seed_wins,
            'lower_seed_wins': self.lower_seed_wins,
            'status': self.status,
            'winner_team_id': self.winner_team_id,
            'next_game_number': self.next_game_number,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PlayerStat(db.Model):
    __tablename__ = 'player_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    
    # Stats
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    shots = db.Column(db.Integer, default=0)
    hits = db.Column(db.Integer, default=0)
    blocks = db.Column(db.Integer, default=0)
    plus_minus = db.Column(db.Integer, default=0)
    
    # Goalie stats
    saves = db.Column(db.Integer, default=0)
    goals_against = db.Column(db.Integer, default=0)
    shots_against = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'game_id': self.game_id,
            'player_id': self.player_id,
            'team_id': self.team_id,
            'goals': self.goals,
            'assists': self.assists,
            'shots': self.shots,
            'hits': self.hits,
            'blocks': self.blocks,
            'plus_minus': self.plus_minus,
            'saves': self.saves,
            'goals_against': self.goals_against,
            'shots_against': self.shots_against
        }

class Standing(db.Model):
    __tablename__ = 'standings'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulations.id'), nullable=False)
    season = db.Column(db.Integer, nullable=False)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    ot_losses = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)
    goals_for = db.Column(db.Integer, default=0)
    goals_against = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'simulation_id': self.simulation_id,
            'season': self.season,
            'wins': self.wins,
            'losses': self.losses,
            'ot_losses': self.ot_losses,
            'points': self.points,
            'goals_for': self.goals_for,
            'goals_against': self.goals_against
        }
