#!/usr/bin/env python3
"""
Seed the database with player, goalie, and coach data
"""
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, db
from models.player import Player, Coach

def seed_database():
    """Seed database with players and coaches"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Load sample data
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_data.json')
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        # Seed players
        print("Seeding players...")
        for player_data in data['players']:
            existing = Player.query.filter_by(name=player_data['name']).first()
            if not existing:
                player = Player(
                    name=player_data['name'],
                    position=player_data['position'],
                    off=player_data['off'],
                    def_=player_data['def'],
                    phys=player_data['phys'],
                    lead=player_data['lead'],
                    const=player_data['const'],
                    is_goalie=False
                )
                db.session.add(player)
        
        # Seed goalies
        print("Seeding goalies...")
        for goalie_data in data['goalies']:
            existing = Player.query.filter_by(name=goalie_data['name']).first()
            if not existing:
                goalie = Player(
                    name=goalie_data['name'],
                    position='G',
                    off=goalie_data['off'],
                    def_=goalie_data['def'],
                    phys=goalie_data['phys'],
                    lead=goalie_data['lead'],
                    const=goalie_data['const'],
                    is_goalie=True
                )
                db.session.add(goalie)
        
        # Seed coaches
        print("Seeding coaches...")
        for coach_data in data['coaches']:
            existing = Coach.query.filter_by(name=coach_data['name']).first()
            if not existing:
                coach = Coach(
                    name=coach_data['name'],
                    rating=coach_data['rating']
                )
                db.session.add(coach)
        
        # Commit all changes
        db.session.commit()
        
        # Print summary
        print(f"\nDatabase seeded successfully!")
        print(f"  Players: {Player.query.filter_by(is_goalie=False).count()}")
        print(f"  Goalies: {Player.query.filter_by(is_goalie=True).count()}")
        print(f"  Coaches: {Coach.query.count()}")

if __name__ == '__main__':
    seed_database()
