# Testing AI Draft Picks

## Method 1: Browser Console (Easiest)

1. Open your draft page in the browser
2. Open Developer Tools (F12 or Cmd+Option+I)
3. Go to the Console tab
4. Paste and run this code:

```javascript
// Get the simulation ID from the URL
const simulationId = window.location.pathname.match(/\/simulation\/(\d+)/)?.[1];

if (!simulationId) {
  console.error('Could not find simulation ID from URL');
} else {
  console.log('Testing AI pick for simulation:', simulationId);
  
  // Get current state
  fetch(`/api/simulations/${simulationId}/draft/current`, {
    headers: {
      'Authorization': `Bearer ${document.cookie.match(/token=([^;]+)/)?.[1]}`
    }
  })
  .then(r => r.json())
  .then(data => {
    console.log('Current pick:', data);
    
    if (data.is_user_team) {
      console.log('⚠️ Current pick is for user team, cannot test AI pick');
      return;
    }
    
    // Make AI pick
    return fetch(`/api/simulations/${simulationId}/draft/sim-next-ai`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${document.cookie.match(/token=([^;]+)/)?.[1]}`,
        'Content-Type': 'application/json'
      }
    });
  })
  .then(r => r ? r.json() : null)
  .then(data => {
    if (data) {
      console.log('AI Pick Response:', data);
      if (data.error) {
        console.error('❌ Error:', data.error);
      } else {
        console.log('✓ AI pick completed');
        console.log('Next pick:', data.next_pick);
      }
    }
    
    // Get updated history
    return fetch(`/api/simulations/${simulationId}/draft/history`, {
      headers: {
        'Authorization': `Bearer ${document.cookie.match(/token=([^;]+)/)?.[1]}`
      }
    });
  })
  .then(r => r.json())
  .then(data => {
    console.log('Updated draft history (last 5 picks):');
    const history = data.history || [];
    history.slice(-5).forEach(pick => {
      const player = pick.player?.name || 'N/A';
      const coach = pick.coach?.name || 'N/A';
      const picked = player !== 'N/A' ? player : (coach !== 'N/A' ? coach : 'EMPTY');
      console.log(`  R${pick.round} P${pick.pick}: ${pick.team_name} - ${picked}`);
    });
  })
  .catch(err => console.error('Error:', err));
}
```

## Method 2: Using curl (if you have your token)

1. Get your JWT token from browser cookies (Application/Storage tab → Cookies)
2. Get your simulation ID from the URL
3. Run:

```bash
# Replace TOKEN and SIMULATION_ID
TOKEN="your_jwt_token_here"
SIMULATION_ID="your_simulation_id"

# Test AI pick
curl -X POST "http://localhost:5000/api/simulations/${SIMULATION_ID}/draft/sim-next-ai" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | python3 -m json.tool

# Check draft history
curl -X GET "http://localhost:5000/api/simulations/${SIMULATION_ID}/draft/history" \
  -H "Authorization: Bearer ${TOKEN}" | python3 -m json.tool
```

## Method 3: Check Backend Logs

The backend console will show detailed debug output:
- `DEBUG auto_pick: Found X available players`
- `DEBUG auto_pick: Round X, Selected from Y candidates: PlayerName`
- `AI PICK: Team X (Round Y) - Player Name - ADDED TO ROSTER`

Look for these messages to see what's happening with each AI pick.

## What to Look For

1. **Empty picks**: Check if the debug logs show a player was selected but the history shows empty
2. **Errors**: Look for `ERROR` or `WARNING` messages in the backend console
3. **Available players count**: If it shows 0 available players, that's the problem
4. **Player selection**: Check if a player is being selected but not saved
