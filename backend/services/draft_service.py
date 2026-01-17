"""Draft service for handling snake draft logic"""
from extensions import db
from models.team import Team, Roster
from models.player import Player, Coach
from sqlalchemy import text
import random

class DraftManager:
    def __init__(self, simulation_id):
        self.simulation_id = simulation_id
        all_teams = Team.query.filter_by(simulation_id=simulation_id).order_by(Team.id).all()
        self.num_teams = len(all_teams)
        self.total_rounds = 21  # 20 players + 1 coach
        
        # Get lottery order for round 1 (randomized but consistent via seeded random)
        # Use simulation_id as seed to ensure consistent ordering
        import random as random_module
        rng = random_module.Random(simulation_id)  # Use separate RNG instance
        self.lottery_order = all_teams.copy()
        rng.shuffle(self.lottery_order)

        self.teams = self.lottery_order  # Use lottery order for round 1
        self.base_teams = all_teams  # Keep original order for reference
        
        # Get current pick from simulation
        from models.simulation import Simulation
        simulation = Simulation.query.get(simulation_id)
        self.current_pick = (simulation.draft_pick or 1) - 1  # Convert to 0-based index

    def _get_taken_coach_ids(self):
        """Fetch taken coach IDs directly from the database."""
        result = db.session.execute(
            text(
                "SELECT coach_id FROM teams "
                "WHERE simulation_id = :simulation_id AND coach_id IS NOT NULL"
            ),
            {"simulation_id": self.simulation_id},
        )
        return [row[0] for row in result.fetchall()]

    def _assign_coach_to_team(self, team_id, coach_id, context):
        """Assign a coach using a direct DB update to avoid stale ORM state."""
        current = db.session.execute(
            text(
                "SELECT coach_id FROM teams "
                "WHERE id = :team_id AND simulation_id = :simulation_id"
            ),
            {"team_id": team_id, "simulation_id": self.simulation_id},
        ).fetchone()
        if not current:
            raise ValueError(f"{context}: Team {team_id} not found")
        if current[0] is not None:
            raise ValueError(
                f"{context}: Team {team_id} already has coach {current[0]}"
            )

        existing = db.session.execute(
            text(
                "SELECT id FROM teams "
                "WHERE simulation_id = :simulation_id AND coach_id = :coach_id"
            ),
            {"simulation_id": self.simulation_id, "coach_id": coach_id},
        ).fetchone()
        if existing:
            raise ValueError(
                f"{context}: Coach {coach_id} is already assigned to team {existing[0]}"
            )

        result = db.session.execute(
            text(
                "UPDATE teams SET coach_id = :coach_id "
                "WHERE id = :team_id AND simulation_id = :simulation_id "
                "AND coach_id IS NULL"
            ),
            {
                "coach_id": coach_id,
                "team_id": team_id,
                "simulation_id": self.simulation_id,
            },
        )
        if result.rowcount != 1:
            raise ValueError(
                f"{context}: Failed to assign coach {coach_id} to team {team_id}"
            )

        db.session.flush()

    def _get_position_counts(self, team_id):
        roster = db.session.query(Player).join(Roster).filter(
            Roster.team_id == team_id,
            Roster.simulation_id == self.simulation_id
        ).all()
        return {
            'C': len([p for p in roster if p.position == 'C']),
            'LW': len([p for p in roster if p.position == 'LW']),
            'RW': len([p for p in roster if p.position == 'RW']),
            'LD': len([p for p in roster if p.position == 'LD']),
            'RD': len([p for p in roster if p.position == 'RD']),
            'G': len([p for p in roster if p.position == 'G']),
        }

    def _get_position_targets(self):
        return {'C': 4, 'LW': 4, 'RW': 4, 'LD': 3, 'RD': 3, 'G': 2}

    def _validate_position_capacity(self, team_id, player_position):
        targets = self._get_position_targets()
        position_counts = self._get_position_counts(team_id)
        if player_position in targets and position_counts[player_position] >= targets[player_position]:
            raise ValueError(
                f"Position {player_position} is full for this team. Please pick another position."
            )
        
    def get_draft_order(self):
        """Get snake draft order (round 1 is lottery order, then snakes)"""
        order = []
        for round_num in range(1, self.total_rounds + 1):
            if round_num % 2 == 1:  # Odd rounds: 1 -> N (use lottery order for round 1)
                order.extend([(round_num, team.id) for team in self.lottery_order])
            else:  # Even rounds: N -> 1
                order.extend([(round_num, team.id) for team in reversed(self.lottery_order)])
        return order
    
    def get_first_round_order(self):
        """Get first round lottery order"""
        return [{'team_id': team.id, 'team_name': f"{team.city} {team.name}"} for team in self.lottery_order]
    
    def get_current_pick_info(self):
        """Get info about current pick"""
        order = self.get_draft_order()
        if self.current_pick >= len(order):
            return None  # Draft complete
        
        # Normal draft pick
        round_num, team_id = order[self.current_pick]
        team = Team.query.get(team_id)
        
        # Check if this is the last pick (round 21) and team doesn't have a coach
        must_pick_coach = False
        if round_num == self.total_rounds and not team.coach_id:
            must_pick_coach = True
        
        return {
            'round': round_num,
            'pick': self.current_pick + 1,
            'total_picks': len(order),
            'team_id': team_id,
            'team_name': f"{team.city} {team.name}",
            'is_user_team': team.user_controlled,
            'must_pick_coach': must_pick_coach
        }
    
    def make_pick(self, player_id=None, coach_id=None):
        """Make a draft pick - all operations in a single transaction"""
        pick_info = self.get_current_pick_info()
        if not pick_info:
            return {'error': 'Draft already completed'}
        
        team_id = pick_info['team_id']
        round_num = pick_info['round']
        team = Team.query.get(team_id)
        
        # Start a transaction - everything must succeed or rollback
        try:
            # Handle coach pick (can be picked in any round)
            if coach_id:
                self._assign_coach_to_team(
                    team_id,
                    coach_id,
                    "Manual pick",
                )
                print(f"DEBUG: Assigned coach {coach_id} to team {team_id}")
            # Handle player pick
            elif player_id:
                # Check if player is already drafted (prevent duplicates)
                existing = Roster.query.filter_by(
                    player_id=player_id,
                    simulation_id=self.simulation_id
                ).first()
                if existing:
                    raise ValueError(f"Player {player_id} is already drafted by another team")

                player = Player.query.get(player_id)
                if not player:
                    raise ValueError(f"Player {player_id} not found in database")
                self._validate_position_capacity(team_id, player.position)
                
                # Add player to roster
                roster_entry = Roster(
                    team_id=team_id,
                    player_id=player_id,
                    simulation_id=self.simulation_id,
                    season_acquired=1
                )
                db.session.add(roster_entry)
                if player:
                    print(f"DEBUG: Added player {player.name} ({player.position}) to team {team_id} roster")
            else:
                # Auto-pick for AI team - consider both players and coaches
                # Check if this pick is mandatory coach selection (last pick, round 21)
                must_pick_coach = pick_info.get('must_pick_coach', False)
                
                if must_pick_coach:
                    # Must pick a coach - find best available
                    taken_coach_ids = self._get_taken_coach_ids()
                    
                    # Get available coaches (those NOT in the taken list)
                    if taken_coach_ids:
                        available_coaches = Coach.query.filter(~Coach.id.in_(taken_coach_ids)).all()
                    else:
                        available_coaches = Coach.query.all()
                    if available_coaches:
                        best_coach = max(available_coaches, key=lambda c: c.rating)
                        self._assign_coach_to_team(
                            team_id,
                            best_coach.id,
                            "Mandatory coach pick",
                        )
                        print(f"AI PICK: Team {team_id} (Round {round_num}) - Coach {best_coach.name} (Rating: {best_coach.rating}) - MANDATORY")
                    else:
                        raise ValueError(f"No available coaches for mandatory coach pick (team {team_id}, round {round_num}). Taken: {taken_coach_ids}")
                else:
                    # AI auto-pick
                    try:
                        pick_result = self.auto_pick_best_option(team_id, round_num)
                    except Exception as e:
                        print(f"ERROR in auto_pick_best_option for team {team_id} round {round_num}: {e}")
                        import traceback
                        traceback.print_exc()
                        raise  # Re-raise to trigger rollback
                    
                    if not pick_result:
                        raise ValueError(f"auto_pick_best_option returned None for team {team_id} round {round_num}")
                    
                    if 'type' not in pick_result or 'id' not in pick_result:
                        raise ValueError(f"Invalid pick result structure: {pick_result}. Expected 'type' and 'id' keys.")
                    
                    if not pick_result.get('id'):
                        raise ValueError(f"Pick result has no ID: {pick_result}")
                    
                    if pick_result['type'] == 'coach' and pick_result.get('id'):
                        coach = Coach.query.get(pick_result['id'])
                        if not coach:
                            raise ValueError(f"Coach {pick_result['id']} not found in database")
                        self._assign_coach_to_team(
                            team_id,
                            pick_result['id'],
                            "AI coach pick",
                        )
                        print(f"AI PICK: Team {team_id} (Round {round_num}) - Coach {coach.name} (Rating: {coach.rating})")
                    elif pick_result['type'] == 'player' and pick_result.get('id'):
                        player = Player.query.get(pick_result['id'])
                        if not player:
                            raise ValueError(f"Player {pick_result['id']} not found in database")
                        
                        # Double-check if player is already drafted (check ALL teams, not just this one)
                        # This is a final safety check before adding
                        existing = Roster.query.filter_by(
                            player_id=pick_result['id'],
                            simulation_id=self.simulation_id
                        ).first()
                        if existing:
                            raise ValueError(f"Player {player.name} (ID: {pick_result['id']}) is already drafted by team {existing.team_id}. This should not happen - auto_pick_best_option should have filtered this out.")
                        
                        # Verify player still exists and is valid
                        if not player.id:
                            raise ValueError(f"Player {pick_result['id']} has invalid ID")
                        
                        roster_entry = Roster(
                            team_id=team_id,
                            player_id=pick_result['id'],
                            simulation_id=self.simulation_id,
                            season_acquired=1
                        )
                        db.session.add(roster_entry)
                        # Flush to ensure it's in the session and get the ID
                        db.session.flush()
                        roster_entry_id = roster_entry.id
                        print(f"AI PICK: Team {team_id} (Round {round_num}) - Player {player.name} ({player.position}, OVR: {player.calculate_overall():.1f}) - ADDED TO ROSTER (ID: {roster_entry_id})")
                        
                        # Verify the roster entry was actually created
                        if not roster_entry_id:
                            raise ValueError(f"Roster entry was not assigned an ID after flush - this should not happen")
                    else:
                        raise ValueError(f"Invalid pick result: type={pick_result.get('type')}, id={pick_result.get('id')}")
            
            # Increment pick counter (part of same transaction)
            self.current_pick += 1
            
            # Update simulation draft_pick (part of same transaction)
            from models.simulation import Simulation
            simulation = Simulation.query.get(self.simulation_id)
            if simulation:
                simulation.draft_pick = self.current_pick + 1  # Convert back to 1-based
            
            # Commit everything together - atomic operation
            db.session.commit()
            
            # Verify the commit worked by checking if roster entry exists (for AI player picks)
            # pick_result is only defined in the else block, so check if we're in that path
            if not coach_id and not player_id:
                # This was an AI auto-pick - check if it was a player pick
                # We need to check what was actually picked
                if 'pick_result' in locals() and pick_result and pick_result.get('type') == 'player':
                    saved_entry = Roster.query.filter_by(
                        team_id=team_id,
                        player_id=pick_result['id'],
                        simulation_id=self.simulation_id
                    ).first()
                    if not saved_entry:
                        raise ValueError(f"CRITICAL: Roster entry for player {pick_result['id']} was not saved after commit! This is a serious bug.")
                    print(f"VERIFIED: Roster entry {saved_entry.id} exists in database after commit")
            
        except Exception as e:
            print(f"ERROR in make_pick for team {team_id} round {round_num}: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            # Re-raise to see the error
            raise
        
        return {
            'success': True,
            'pick_info': pick_info,
            'next_pick': self.get_current_pick_info()
        }
    
    def auto_pick_best_option(self, team_id, round_num):
        """AI logic for picking best available option (player or coach)"""
        # Get team's current roster (including uncommitted changes)
        roster = db.session.query(Player).join(Roster).filter(
            Roster.team_id == team_id,
            Roster.simulation_id == self.simulation_id
        ).all()
        
        print(f"DEBUG auto_pick: Team {team_id}, Round {round_num}, Current roster size: {len(roster)}")
        
        # Calculate position counts (LD and RD are separate)
        position_counts = self._get_position_counts(team_id)
        targets = self._get_position_targets()
        
        # Do not force a specific defense side. If one side is full, the team can
        # draft any other open position (including the other defense side).
        
        # Analyze team balance (offensive, defensive, physical players)
        avg_off = sum(p.off for p in roster) / len(roster) if roster else 0
        avg_def = sum(p.def_ for p in roster) / len(roster) if roster else 0
        avg_phys = sum(p.phys for p in roster) / len(roster) if roster else 0
        
        # Get count of drafted players for debugging
        drafted_count = db.session.query(Roster).filter_by(simulation_id=self.simulation_id).count()
        total_players = db.session.query(Player).count()
        print(f"DEBUG auto_pick: Drafted players: {drafted_count}, Total players: {total_players}")
        
        # Filter available players - use LEFT JOIN to find players not in roster
        # This will see uncommitted changes in the same transaction
        from sqlalchemy import and_
        try:
            available_players = db.session.query(Player).outerjoin(
                Roster,
                and_(
                    Roster.player_id == Player.id,
                    Roster.simulation_id == self.simulation_id
                )
            ).filter(
                Roster.player_id.is_(None)
            ).all()
        except Exception as e:
            print(f"ERROR in available players query: {e}")
            # Fallback: use a simpler query
            drafted_ids = [r[0] for r in db.session.query(Roster.player_id).filter_by(simulation_id=self.simulation_id).all()]
            available_players = db.session.query(Player).filter(~Player.id.in_(drafted_ids)).all() if drafted_ids else db.session.query(Player).all()
        
        print(f"DEBUG auto_pick: Found {len(available_players)} available players")
        available_players_before_capacity = list(available_players)
        available_players_by_position = {}
        for player in available_players:
            position = player.position or "Unknown"
            available_players_by_position[position] = available_players_by_position.get(position, 0) + 1
        
        # If we found 0 players, flag it for later error handling (allow coach pick if possible)
        no_available_players_error = None
        if len(available_players) == 0:
            no_available_players_error = (
                f"No available players found for team {team_id} in round {round_num}. "
                f"Drafted: {drafted_count}, Total: {total_players}."
            )
            print(f"ERROR: {no_available_players_error}")
        
        # Enforce roster capacity: only allow positions that are not full
        available_players = [
            p for p in available_players
            if p.position not in targets or position_counts.get(p.position, 0) < targets[p.position]
        ]

        # If no players remain after capacity filtering, but there are still undrafted players,
        # allow AI to pick the best available to avoid deadlock when a position has no players left.
        # This is an AI-only fallback that avoids breaking the draft.
        if not available_players and available_players_before_capacity:
            open_positions = [
                pos for pos, target in targets.items()
                if position_counts.get(pos, 0) < target
            ]
            available_positions = {p.position for p in available_players_before_capacity}
            if not open_positions or not (set(open_positions) & available_positions):
                print(
                    "WARNING auto_pick: No available players for open positions. "
                    "Falling back to best available regardless of targets."
                )
                available_players = available_players_before_capacity

        # No need to filter out generic 'D' - there are no generic 'D' players in the database
        
        # Early rounds (1-3): Random selection within OVR delta bracket
        best_score = -1
        best_option = None
        best_type = None
        
        # Track if we've selected a player (to ensure best_score is set)
        player_selected = False
        
        # Ensure we have available players (if not, defer error until after coach check)
        if not available_players:
            open_positions = [pos for pos, target in targets.items() if position_counts.get(pos, 0) < target]
            drafted_count = db.session.query(Roster).filter_by(simulation_id=self.simulation_id).count()
            total_players = db.session.query(Player).count()
            reason_parts = [
                f"No available players for team {team_id} in round {round_num}.",
                f"Open positions: {', '.join(open_positions) if open_positions else 'none'}.",
                f"Available pool by position: {available_players_by_position}.",
                f"Position counts: {position_counts}. Targets: {targets}.",
                f"Drafted: {drafted_count}, Total: {total_players}, Available after filters: 0.",
            ]
            no_available_players_error = " ".join(reason_parts)
            print(f"ERROR: {no_available_players_error}")
        
        if available_players and round_num <= 3:
            # Determine delta based on round
            delta = 3 if round_num == 1 else (4 if round_num == 2 else 5)
            
            # Find best overall rating
            best_overall_rating = 0
            for player in available_players:
                overall = player.calculate_overall()
                if overall > best_overall_rating:
                    best_overall_rating = overall
            
            # Filter players within delta of best
            candidates = []
            for player in available_players:
                player_overall = player.calculate_overall()
                if player_overall >= best_overall_rating - delta:
                    candidates.append(player)
            
            # Randomly select from candidates
            if candidates:
                best_option = random.choice(candidates)
                best_type = 'player'
                best_score = best_option.calculate_overall()  # Set best_score for coach comparison
                player_selected = True
                print(f"DEBUG auto_pick: Round {round_num}, Selected from {len(candidates)} candidates: {best_option.name} (OVR: {best_option.calculate_overall():.1f})")
            else:
                # Fallback: pick best available
                best_option = max(available_players, key=lambda p: p.calculate_overall())
                best_type = 'player'
                best_score = best_option.calculate_overall()  # Set best_score for coach comparison
                player_selected = True
                print(f"DEBUG auto_pick: Round {round_num}, No candidates in delta, using best: {best_option.name} (OVR: {best_option.calculate_overall():.1f})")
        elif available_players:
            # Rounds 4+: Use scoring system with needs and balance
            position_bonus_multiplier = 0.0
            if round_num <= 6:
                position_bonus_multiplier = 0.5  # Small bonus
            elif round_num <= 12:
                position_bonus_multiplier = 1.0  # Standard bonus
            else:
                position_bonus_multiplier = 2.0  # Higher bonus in late rounds
            
            # Track best overall rating to ensure we don't pass on significantly better players
            best_overall_rating = 0
            for player in available_players:
                overall = player.calculate_overall()
                if overall > best_overall_rating:
                    best_overall_rating = overall
            
            # Initialize with first player as fallback
            if available_players:
                best_option = available_players[0]
                best_type = 'player'
                best_score = available_players[0].calculate_overall()
                player_selected = True
            
            for player in available_players:
                # Base score: overall rating (already includes consistency)
                score = player.calculate_overall()
                
                # Position need bonus: how much we need this position
                current = position_counts.get(player.position, 0)
                target = targets.get(player.position, 0)
                deficit = max(0, target - current)
                
                # Apply position bonus with round-based multiplier
                if player.position in ['LD', 'RD']:
                    position_bonus = deficit * 5 * position_bonus_multiplier
                else:
                    position_bonus = deficit * 3 * position_bonus_multiplier
                score += position_bonus
                
                # Balance bonus: prefer players that complement team style
                balance_bonus = 0
                if not player.is_goalie and player.position != 'G':
                    if avg_off < 75 and player.off > 75:
                        balance_bonus += 1
                    if avg_def < 75 and player.def_ > 75:
                        balance_bonus += 1
                    if avg_phys < 75 and player.phys > 75:
                        balance_bonus += 1
                score += balance_bonus
                
                # Safeguard: If this player is significantly better (5+ OVR points), 
                # ensure they're not passed over even with bonuses
                player_overall = player.calculate_overall()
                if player_overall < best_overall_rating - 4:
                    # Player is 5+ OVR worse - heavily penalize to avoid picking them
                    score -= 10
                
                if score > best_score:
                    best_score = score
                    best_option = player
                    best_type = 'player'
        
        # Ensure best_score is set if we have a player
        if best_option and best_type == 'player' and best_score == -1:
            best_score = best_option.calculate_overall()
        
        # Get team
        team = Team.query.get(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found in simulation {self.simulation_id}")
        
        # Consider coaches if team doesn't have one
        # Coaches compete with players: compare rating vs overall
        if not team.coach_id:
            # Get taken coach IDs directly from database - always fresh
            taken_coach_ids = self._get_taken_coach_ids()
            
            # Get available coaches (those NOT in the taken list)
            if taken_coach_ids:
                available_coaches = Coach.query.filter(~Coach.id.in_(taken_coach_ids)).all()
            else:
                available_coaches = Coach.query.all()
            
            # Compare best coach rating to best player overall
            if available_coaches:
                best_coach = max(available_coaches, key=lambda c: c.rating)
                best_player_overall = best_option.calculate_overall() if (best_option and best_type == 'player') else 0
                
                # Pick whichever is better: coach rating or player overall
                if best_coach.rating > best_player_overall:
                    best_score = best_coach.rating
                    best_option = best_coach
                    best_type = 'coach'
                    print(f"DEBUG auto_pick: Coach {best_coach.name} (Rating: {best_coach.rating}) beats player (OVR: {best_player_overall:.1f})")
        
        if best_option and best_type == 'player':
            print(f"DEBUG auto_pick: Round {round_num}, Best player: {best_option.name} ({best_option.position}, OVR: {best_option.calculate_overall():.1f}, Score: {best_score:.1f})")
        
        # Return the best option
        if best_type == 'coach' and best_option:
            print(f"DEBUG auto_pick: Returning coach {best_option.id} ({best_option.name})")
            return {'type': 'coach', 'id': best_option.id}
        elif best_type == 'player' and best_option:
            print(f"DEBUG auto_pick: Returning player {best_option.id} ({best_option.name}, {best_option.position})")
            return {'type': 'player', 'id': best_option.id}
        else:
            # This should never happen if filtering logic is correct
            # Fallback: try to pick the best available player regardless
            if available_players:
                fallback_player = max(available_players, key=lambda p: p.calculate_overall())
                print(f"WARNING: Using fallback pick for team {team_id} in round {round_num} - selected {fallback_player.name}")
                return {'type': 'player', 'id': fallback_player.id}
            else:
                error_msg = no_available_players_error or (
                    f"No valid pick found for team {team_id} in round {round_num}. "
                    f"Available players: {len(available_players)}, best_type: {best_type}, best_option: {best_option}"
                )
                print(f"ERROR: {error_msg}")
                raise ValueError(error_msg)

def get_draft_history(simulation_id):
    """Get draft history - all picks made so far"""
    from models.simulation import Simulation
    
    # Refresh the session to ensure we see latest committed data
    db.session.expire_all()
    
    simulation = Simulation.query.get(simulation_id)
    if not simulation:
        return []
    
    manager = DraftManager(simulation_id)
    order = manager.get_draft_order()
    current_pick = (simulation.draft_pick or 1) - 1
    
    # Get all rosters ordered by Roster.id (creation order = pick order globally)
    all_rosters_list = Roster.query.filter_by(simulation_id=simulation_id).order_by(Roster.id).all()
    print(f"Draft history: Found {len(all_rosters_list)} total roster entries for simulation {simulation_id}")
    
    # Get all teams with their coaches
    all_teams = Team.query.filter_by(simulation_id=simulation_id).all()
    team_coaches = {team.id: team.coach_id for team in all_teams if team.coach_id}
    
    # New approach: Use global roster entry order to match picks
    # Roster entries are created in the exact order picks were made (for player picks)
    # We iterate through picks and consume roster entries in global order
    
    # Build a global queue of roster entries with their team info
    global_roster_queue = []
    for roster_entry in all_rosters_list:
        player = Player.query.get(roster_entry.player_id)
        global_roster_queue.append({
            'team_id': roster_entry.team_id,
            'player_id': roster_entry.player_id,
            'roster_id': roster_entry.id,
            'player': player
        })
    
    # Track which teams have used their coach pick
    teams_with_coach_pick_used = set()
    
    # Track per-team: how many roster entries we've consumed
    team_roster_consumed = {team.id: 0 for team in all_teams}
    
    # Count how many roster entries each team should have based on picks made
    team_expected_rosters = {team.id: 0 for team in all_teams}
    for pick_index in range(current_pick):
        if pick_index >= len(order):
            break
        round_num, team_id = order[pick_index]
        team_expected_rosters[team_id] = team_expected_rosters.get(team_id, 0) + 1
    
    # Subtract 1 for teams that have a coach (they have 1 fewer roster entry than picks)
    for team_id, coach_id in team_coaches.items():
        if coach_id:
            team_expected_rosters[team_id] = max(0, team_expected_rosters.get(team_id, 0) - 1)
    
    # Group roster entries by team for counting
    team_actual_rosters = {}
    for entry in global_roster_queue:
        tid = entry['team_id']
        team_actual_rosters[tid] = team_actual_rosters.get(tid, 0) + 1
    
    history = []
    global_roster_idx = 0
    
    for pick_index in range(current_pick):
        if pick_index >= len(order):
            break
        
        round_num, team_id = order[pick_index]
        team = Team.query.get(team_id)
        
        pick_data = {
            'round': round_num,
            'pick': pick_index + 1,
            'team_id': team_id,
            'team_name': f"{team.city} {team.name}",
            'is_user_team': team.user_controlled
        }
        
        # Determine if this pick was a coach or player
        # Strategy: Look at the next roster entry in global order
        # If it belongs to this team, it's a player pick
        # If not (or no more entries for this team), check if this team has a coach they haven't used yet
        
        team_has_coach = team_id in team_coaches and team_coaches[team_id]
        team_coach_used = team_id in teams_with_coach_pick_used
        team_remaining_rosters = team_actual_rosters.get(team_id, 0) - team_roster_consumed.get(team_id, 0)
        
        # Check if this pick should be a coach pick
        # A pick is a coach pick if:
        # 1. The team has a coach assigned AND hasn't used their coach pick yet
        # 2. AND either there are no more roster entries for this team, 
        #    OR the next global roster entry is for a different team
        
        is_coach_pick = False
        if team_has_coach and not team_coach_used:
            if team_remaining_rosters == 0:
                # No more roster entries for this team - must be coach
                is_coach_pick = True
            elif global_roster_idx < len(global_roster_queue):
                next_entry = global_roster_queue[global_roster_idx]
                if next_entry['team_id'] != team_id:
                    # Next roster entry is for a different team - this pick was a coach
                    is_coach_pick = True
        
        if is_coach_pick:
            coach = Coach.query.get(team_coaches[team_id])
            if coach:
                pick_data['coach'] = coach.to_dict()
                teams_with_coach_pick_used.add(team_id)
                print(f"Draft history: Pick {pick_index + 1} (R{round_num}) - Team {team_id} ({team.city} {team.name}) picked coach {coach.name}")
        else:
            # Player pick - consume the next roster entry in global order
            if global_roster_idx < len(global_roster_queue):
                entry = global_roster_queue[global_roster_idx]
                # Sanity check: the entry should be for this team
                if entry['team_id'] == team_id:
                    if entry['player']:
                        pick_data['player'] = entry['player'].to_dict()
                        print(f"Draft history: Pick {pick_index + 1} (R{round_num}) - Team {team_id} ({team.city} {team.name}) picked player {entry['player'].name}")
                    global_roster_idx += 1
                    team_roster_consumed[team_id] = team_roster_consumed.get(team_id, 0) + 1
                else:
                    # Mismatch - this shouldn't happen, log warning
                    print(f"Draft history: WARNING - Pick {pick_index + 1} (R{round_num}) - Team {team_id} expected but roster entry is for team {entry['team_id']}")
                    # Skip this and try to continue
            else:
                print(f"Draft history: WARNING - Pick {pick_index + 1} (R{round_num}) - No roster entry available for team {team_id}")
        
        history.append(pick_data)
    
    return history

def process_draft_pick(simulation_id, data):
    """Process a draft pick"""
    manager = DraftManager(simulation_id)
    
    # Check if this is a mandatory coach pick (last pick, round 21)
    pick_info = manager.get_current_pick_info()
    if pick_info and pick_info.get('must_pick_coach'):
        # Must pick a coach - validate that coach_id is provided
        coach_id = data.get('coach_id')
        if not coach_id:
            return {'error': 'Coach selection is mandatory for the last pick'}, 400
        
        try:
            result = manager.make_pick(coach_id=coach_id)
        except ValueError as e:
            return {'error': str(e)}, 400
    else:
        player_id = data.get('player_id')
        coach_id = data.get('coach_id')
        try:
            result = manager.make_pick(player_id=player_id, coach_id=coach_id)
        except ValueError as e:
            return {'error': str(e)}, 400
    
    # Check if draft is complete
    if not result.get('next_pick'):
        from models.simulation import Simulation
        from services.lines_service import auto_populate_all_teams
        sim = Simulation.query.get(simulation_id)
        sim.status = 'season'
        db.session.commit()
        
        # Auto-populate lines for all teams
        auto_populate_all_teams(simulation_id)
        
        result['draft_complete'] = True
    
    return result

def sim_to_next_user_pick(simulation_id):
    """Simulate all picks until it's the user's turn"""
    manager = DraftManager(simulation_id)
    
    while True:
        pick_info = manager.get_current_pick_info()
        if not pick_info:
            # Draft complete
            from models.simulation import Simulation
            from services.lines_service import auto_populate_all_teams
            from services.game_service import generate_season_schedule, initialize_standings
            sim = Simulation.query.get(simulation_id)
            sim.status = 'season'
            db.session.commit()
            
            # Auto-populate lines for all teams
            auto_populate_all_teams(simulation_id)
            
            # Generate season schedule when draft completes
            generate_season_schedule(simulation_id, sim.current_season)
            
            # Initialize standings with 0s so they're visible before games are played
            initialize_standings(simulation_id, sim.current_season)
            
            return {'draft_complete': True}
        
        if pick_info['is_user_team']:
            # Reached user's pick
            return {'next_pick': pick_info}
        
        # Auto-pick for AI
        try:
            result = manager.make_pick()
        except ValueError as e:
            return {'error': f'Failed to make AI pick: {str(e)}'}
        if result.get('error'):
            return result

def sim_next_ai_pick(simulation_id):
    """Simulate the next AI pick"""
    manager = DraftManager(simulation_id)
    
    pick_info = manager.get_current_pick_info()
    if not pick_info:
        # Draft complete
        from models.simulation import Simulation
        from services.lines_service import auto_populate_all_teams
        from services.game_service import generate_season_schedule, initialize_standings
        sim = Simulation.query.get(simulation_id)
        sim.status = 'season'
        db.session.commit()
        
        # Auto-populate lines for all teams
        auto_populate_all_teams(simulation_id)
        
        # Generate season schedule and initialize standings
        generate_season_schedule(simulation_id, sim.current_season)
        initialize_standings(simulation_id, sim.current_season)
        
        return {'draft_complete': True}
    
    if pick_info['is_user_team']:
        return {'error': "It's your turn to pick, not AI's"}
    
    try:
        # make_pick handles all validation and transaction management
        result = manager.make_pick()
        
        # Verify the result indicates success
        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error in make_pick')
            print(f"ERROR: make_pick returned unsuccessful result: {result}")
            return {'error': error_msg}
        
        # Check if draft is complete
        if not result.get('next_pick'):
            from models.simulation import Simulation
            from services.lines_service import auto_populate_all_teams
            from services.game_service import generate_season_schedule, initialize_standings
            sim = Simulation.query.get(simulation_id)
            sim.status = 'season'
            db.session.commit()
            
            # Auto-populate lines for all teams
            auto_populate_all_teams(simulation_id)
            
            # Generate season schedule and initialize standings
            generate_season_schedule(simulation_id, sim.current_season)
            initialize_standings(simulation_id, sim.current_season)
            
            result['draft_complete'] = True
        
        return result
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR in sim_next_ai_pick: {error_msg}")
        import traceback
        traceback.print_exc()
        # make_pick already handles rollback, but ensure we're in a clean state
        db.session.rollback()
        return {'error': f'Failed to make AI pick: {error_msg}'}

def sim_all_draft(simulation_id):
    """Simulate the entire draft"""
    manager = DraftManager(simulation_id)
    
    while True:
        pick_info = manager.get_current_pick_info()
        if not pick_info:
            # Draft complete
            from models.simulation import Simulation
            from services.lines_service import auto_populate_all_teams
            from services.game_service import generate_season_schedule, initialize_standings
            sim = Simulation.query.get(simulation_id)
            sim.status = 'season'
            db.session.commit()
            
            # Auto-populate lines for all teams
            auto_populate_all_teams(simulation_id)
            
            # Generate season schedule when draft completes
            generate_season_schedule(simulation_id, sim.current_season)
            
            # Initialize standings with 0s so they're visible before games are played
            initialize_standings(simulation_id, sim.current_season)
            
            return {'draft_complete': True}
        
        # Auto-pick (AI logic for all teams)
        try:
            result = manager.make_pick()
            if result.get('error'):
                error_msg = result.get('error', 'Unknown error in make_pick')
                print(f"ERROR in sim_all_draft: make_pick returned error: {error_msg}")
                return {'error': error_msg}
            
            if result.get('draft_complete'):
                return result
        except Exception as e:
            error_msg = str(e)
            print(f"ERROR in sim_all_draft: Exception during make_pick: {error_msg}")
            import traceback
            traceback.print_exc()
            # make_pick already handles rollback, but ensure we're in a clean state
            db.session.rollback()
            return {'error': f'Failed to make AI pick: {error_msg}'}
