#!/usr/bin/env python3
"""
Test script to test AI draft picks via API
"""
import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5000"
# Try 5001 if 5000 doesn't work
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=2)
except:
    BASE_URL = "http://localhost:5001"

def login(username, password):
    """Login and get JWT token"""
    url = f"{BASE_URL}/api/auth/login"
    data = {"username": username, "password": password}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def get_simulations(token):
    """Get list of simulations"""
    url = f"{BASE_URL}/api/simulations"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('simulations', [])
    else:
        print(f"Failed to get simulations: {response.status_code} - {response.text}")
        return []

def get_draft_current(token, simulation_id):
    """Get current draft pick info"""
    url = f"{BASE_URL}/api/simulations/{simulation_id}/draft/current"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get current pick: {response.status_code} - {response.text}")
        return None

def get_draft_history(token, simulation_id):
    """Get draft history"""
    url = f"{BASE_URL}/api/simulations/{simulation_id}/draft/history"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('history', [])
    else:
        print(f"Failed to get draft history: {response.status_code} - {response.text}")
        return []

def sim_next_ai_pick(token, simulation_id):
    """Simulate next AI pick"""
    url = f"{BASE_URL}/api/simulations/{simulation_id}/draft/sim-next-ai"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers)
    return response

def main():
    print("=" * 60)
    print("AI Draft Pick Test Script")
    print("=" * 60)
    print()
    
    # Get credentials
    username = input("Enter username (or press Enter for 'admin'): ").strip() or "admin"
    password = input("Enter password (or press Enter for 'admin'): ").strip() or "admin"
    
    print(f"\nLogging in as {username}...")
    token = login(username, password)
    if not token:
        print("Failed to login. Exiting.")
        sys.exit(1)
    print("✓ Login successful")
    
    print("\nFetching simulations...")
    simulations = get_simulations(token)
    if not simulations:
        print("No simulations found. Please create a simulation first.")
        sys.exit(1)
    
    # Filter for draft status
    draft_sims = [s for s in simulations if s.get('status') == 'draft']
    if not draft_sims:
        print("No simulations in draft status found.")
        print("Available simulations:")
        for sim in simulations:
            print(f"  - ID: {sim['id']}, Name: {sim['name']}, Status: {sim['status']}")
        sys.exit(1)
    
    print(f"\nFound {len(draft_sims)} simulation(s) in draft status:")
    for i, sim in enumerate(draft_sims):
        print(f"  {i+1}. ID: {sim['id']}, Name: {sim['name']}")
    
    if len(draft_sims) == 1:
        simulation_id = draft_sims[0]['id']
        print(f"\nUsing simulation ID: {simulation_id}")
    else:
        choice = input(f"\nSelect simulation (1-{len(draft_sims)}): ").strip()
        try:
            simulation_id = draft_sims[int(choice) - 1]['id']
        except (ValueError, IndexError):
            print("Invalid choice. Exiting.")
            sys.exit(1)
    
    # Get current pick info
    print("\n" + "=" * 60)
    print("Current Draft State")
    print("=" * 60)
    current = get_draft_current(token, simulation_id)
    if current:
        if current.get('draft_complete'):
            print("Draft is complete!")
            sys.exit(0)
        print(f"Round: {current.get('round')}")
        print(f"Pick: {current.get('pick')}/{current.get('total_picks')}")
        print(f"Team: {current.get('team_name')}")
        print(f"Is User Team: {current.get('is_user_team')}")
    
    # Get draft history
    history = get_draft_history(token, simulation_id)
    print(f"\nTotal picks made: {len(history)}")
    if history:
        print("\nLast 5 picks:")
        for pick in history[-5:]:
            player_name = pick.get('player', {}).get('name', 'N/A')
            coach_name = pick.get('coach', {}).get('name', 'N/A')
            picked = player_name if player_name != 'N/A' else (coach_name if coach_name != 'N/A' else 'EMPTY')
            print(f"  R{pick.get('round')} P{pick.get('pick')}: {pick.get('team_name')} - {picked}")
    
    # Test AI pick
    print("\n" + "=" * 60)
    print("Testing AI Pick")
    print("=" * 60)
    
    if current and current.get('is_user_team'):
        print("Current pick is for user team. Cannot test AI pick.")
        sys.exit(0)
    
    input("\nPress Enter to simulate next AI pick...")
    
    response = sim_next_ai_pick(token, simulation_id)
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('error'):
            print(f"❌ Error: {data['error']}")
        elif data.get('draft_complete'):
            print("✓ Draft is now complete!")
        else:
            print("✓ AI pick completed successfully!")
            next_pick = data.get('next_pick', {})
            if next_pick:
                print(f"\nNext pick:")
                print(f"  Round: {next_pick.get('round')}")
                print(f"  Pick: {next_pick.get('pick')}")
                print(f"  Team: {next_pick.get('team_name')}")
                print(f"  Is User Team: {next_pick.get('is_user_team')}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Get updated history
    print("\n" + "=" * 60)
    print("Updated Draft History")
    print("=" * 60)
    history = get_draft_history(token, simulation_id)
    print(f"Total picks made: {len(history)}")
    if history:
        print("\nLast 5 picks:")
        for pick in history[-5:]:
            player_name = pick.get('player', {}).get('name', 'N/A')
            coach_name = pick.get('coach', {}).get('name', 'N/A')
            picked = player_name if player_name != 'N/A' else (coach_name if coach_name != 'N/A' else 'EMPTY')
            print(f"  R{pick.get('round')} P{pick.get('pick')}: {pick.get('team_name')} - {picked}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
