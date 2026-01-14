# LHL API Documentation

Base URL: `http://localhost:5000` (development) or your deployed URL

All endpoints return JSON. Protected endpoints require JWT token in Authorization header:
```
Authorization: Bearer <token>
```

## Authentication Endpoints

### POST /api/auth/register
Register a new user account.

**Request:**
```json
{
  "username": "string (required)",
  "email": "string (required, valid email)",
  "password": "string (required, min 6 chars)"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "is_admin": false,
    "created_at": "2024-01-01T00:00:00"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Errors:**
- 400: Missing required fields
- 400: Username or email already exists

### POST /api/auth/login
Login with existing credentials.

**Request:**
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "user": { /* user object */ },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Errors:**
- 400: Missing credentials
- 401: Invalid credentials

### GET /api/auth/me
Get current user info (protected).

**Response (200):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "is_admin": false
}
```

## Simulation Endpoints

### POST /api/simulations/create
Create a new simulation (protected).

**Request:**
```json
{
  "year_length": 20,  // 20-25
  "num_teams": 6      // 4, 6, 8, 10, or 12
}
```

**Response (201):**
```json
{
  "message": "Simulation created successfully",
  "simulation": {
    "id": 1,
    "user_id": 1,
    "year_length": 20,
    "num_teams": 6,
    "current_season": 1,
    "current_date": "1980-10-01",
    "status": "draft"
  },
  "teams": [
    {
      "id": 1,
      "name": "MTL",
      "city": "Montreal",
      "conference": "Eastern",
      "user_controlled": true
    },
    // ... more teams
  ]
}
```

### GET /api/simulations/{id}
Get simulation details (protected).

**Response (200):**
```json
{
  "simulation": { /* simulation object */ },
  "teams": [ /* array of team objects */ ]
}
```

### GET /api/simulations
List user's simulations (protected).

**Response (200):**
```json
{
  "simulations": [
    { /* simulation object */ },
    // ...
  ]
}
```

### POST /api/simulations/{id}/draft
Make a draft pick (protected).

**Request:**
```json
{
  "player_id": 123,      // For player picks
  "coach_id": 5          // For coach pick (round 21)
}
```

**Response (200):**
```json
{
  "success": true,
  "pick_info": {
    "round": 1,
    "pick": 5,
    "total_picks": 126,
    "team_id": 3,
    "team_name": "TOR",
    "is_user_team": false
  },
  "next_pick": { /* next pick info */ },
  "draft_complete": false  // true when draft ends
}
```

### POST /api/simulations/{id}/simulate-to-playoffs
Simulate regular season games (protected).

**Response (200):**
```json
{
  "message": "Simulated 246 regular season games",
  "season": 1,
  "status": "playoffs"
}
```

### POST /api/simulations/{id}/simulate-round
Simulate one playoff round (protected).

**Request:**
```json
{
  "round": 1  // 1-3 depending on league size
}
```

**Response (200):**
```json
{
  "message": "Simulated playoff round 1",
  "games_simulated": 28
}
```

### POST /api/simulations/{id}/simulate-season
Simulate entire season including playoffs (protected).

**Response (200):**
```json
{
  "message": "Season completed",
  "next_season": 2
}
```

## Team Endpoints

### GET /api/teams/{id}
Get team details including roster and lines (protected).

**Response (200):**
```json
{
  "team": {
    "id": 1,
    "name": "MTL",
    "city": "Montreal",
    "conference": "Eastern",
    "coach_id": 3
  },
  "roster": [
    {
      "id": 15,
      "name": "Wayne Gretzky",
      "position": "C",
      "off": 99,
      "def": 75,
      "phys": 70,
      "lead": 95,
      "const": 95
    },
    // ... more players
  ],
  "lines": [
    {
      "line_type": "forward",
      "line_number": 1,
      "position": "C",
      "player_id": 15
    },
    // ... more line assignments
  ]
}
```

### GET /api/teams/{id}/roster
Get team roster only (protected).

### GET /api/teams/{id}/lines
Get team line assignments (protected).

### PUT /api/teams/{id}/lines
Update team lines (protected).

**Request:**
```json
{
  "lines": [
    {
      "player_id": 15,
      "line_type": "forward",
      "line_number": 1,
      "position": "C"
    },
    // ... all line assignments
  ]
}
```

### POST /api/teams/{id}/sign-free-agent
Sign a free agent player (protected).

**Request:**
```json
{
  "player_id": 42
}
```

## Stats Endpoints

### GET /api/stats/season/{simulation_id}
Get season statistics (protected).

**Query Parameters:**
- `season` (optional): Specific season number

**Response (200):**
```json
{
  "stats": [
    {
      "player_id": 15,
      "player_name": "Wayne Gretzky",
      "team_name": "MTL",
      "games_played": 82,
      "goals": 87,
      "assists": 121,
      "points": 208,
      "plus_minus": 62,
      "hits": 45,
      "blocks": 12,
      "shots": 324
    },
    // ... more players
  ]
}
```

### GET /api/stats/all-time/{simulation_id}
Get all-time statistics across all seasons (protected).

### GET /api/stats/standings/{simulation_id}
Get league standings (protected).

**Query Parameters:**
- `season` (optional): Specific season number

**Response (200):**
```json
{
  "eastern": [
    {
      "team_id": 1,
      "team_name": "MTL",
      "conference": "Eastern",
      "wins": 55,
      "losses": 27,
      "points": 110,
      "goals_for": 312,
      "goals_against": 245
    },
    // ... more teams
  ],
  "western": [ /* western conference teams */ ]
}
```

### GET /api/stats/trophies/{simulation_id}
Get trophy winners (protected).

**Response (200):**
```json
{
  "message": "Trophy tracking coming soon",
  "trophies": []
}
```

## Admin Endpoints

All admin endpoints require admin privileges.

### GET /api/admin/users
List all users (admin only).

**Response (200):**
```json
{
  "users": [
    {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "is_admin": false,
      "created_at": "2024-01-01T00:00:00"
    },
    // ... more users
  ]
}
```

### DELETE /api/admin/users/{user_id}
Delete a user (admin only).

**Response (200):**
```json
{
  "message": "User deleted successfully"
}
```

### GET /api/admin/analytics
Get analytics dashboard data (admin only).

**Response (200):**
```json
{
  "total_users": 150,
  "active_simulations": 42,
  "completed_simulations": 28,
  "popular_teams": []
}
```

### GET /api/admin/database-health
Get database health metrics (admin only).

**Response (200):**
```json
{
  "users": 150,
  "simulations": 70,
  "players": 84,
  "coaches": 18,
  "games_simulated": 12450,
  "total_player_stats": 98500
}
```

## Error Responses

All endpoints may return these error responses:

**400 Bad Request:**
```json
{
  "error": "Descriptive error message"
}
```

**401 Unauthorized:**
```json
{
  "error": "Unauthorized" 
}
```

**403 Forbidden:**
```json
{
  "error": "Admin access required"
}
```

**404 Not Found:**
```json
{
  "error": "Resource not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error"
}
```

## Rate Limiting

Currently no rate limiting is implemented. This will be added in production.

## Pagination

Currently all list endpoints return full results. Pagination will be added for large datasets.

## Versioning

Current API version: v1 (implicit)
Future versions will use URL versioning: `/api/v2/...`
