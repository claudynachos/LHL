#!/usr/bin/env python3
"""
Seed the database with player, goalie, and coach data
"""
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app
from extensions import db
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
                    player_type=player_data.get('type', ''),
                    era=player_data.get('era', ''),
                    off=player_data['off'],
                    def_=player_data['def'],
                    phys=player_data['phys'],
                    lead=player_data['lead'],
                    const=player_data['const'],
                    is_goalie=False
                )
                db.session.add(player)
            else:
                # Update existing player with type and era
                if player_data.get('type'):
                    existing.player_type = player_data.get('type', '')
                if player_data.get('era'):
                    existing.era = player_data.get('era', '')
        
        # Seed goalies
        print("Seeding goalies...")
        for goalie_data in data['goalies']:
            existing = Player.query.filter_by(name=goalie_data['name']).first()
            if not existing:
                # Goalies use 'gen' (general) rating - map to attributes
                gen_rating = goalie_data.get('gen', 80)
                goalie = Player(
                    name=goalie_data['name'],
                    position='G',
                    era=goalie_data.get('era', ''),
                    off=gen_rating,  # Use gen for all goalie stats
                    def_=gen_rating,
                    phys=gen_rating,
                    lead=gen_rating,
                    const=goalie_data.get('const', 80),
                    is_goalie=True
                )
                db.session.add(goalie)
            else:
                # Update existing goalie with era
                if goalie_data.get('era'):
                    existing.era = goalie_data.get('era', '')
        
        # Seed coaches
        print("Seeding coaches...")
        for coach_data in data['coaches']:
            existing = Coach.query.filter_by(name=coach_data['name']).first()
            if not existing:
                # Coaches have off/def - average them for overall rating
                off = coach_data.get('off', 80)
                def_ = coach_data.get('def', 80)
                rating = (off + def_) // 2
                coach = Coach(
                    name=coach_data['name'],
                    coach_type=coach_data.get('type', ''),
                    era=coach_data.get('era', ''),
                    rating=rating
                )
                db.session.add(coach)
            else:
                # Update existing coach with type and era
                if coach_data.get('type'):
                    existing.coach_type = coach_data.get('type', '')
                if coach_data.get('era'):
                    existing.era = coach_data.get('era', '')
        
        # Commit all changes
        db.session.commit()
        
        # Print summary
        print(f"\nDatabase seeded successfully!")
        print(f"  Players: {Player.query.filter_by(is_goalie=False).count()}")
        print(f"  Goalies: {Player.query.filter_by(is_goalie=True).count()}")
        print(f"  Coaches: {Coach.query.count()}")

if __name__ == '__main__':
    seed_database()
