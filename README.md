# Legend Hockey League (LHL)

A hockey simulation game where you draft teams of NHL legends and simulate epic 20-25 year seasons.

## Features

- **Draft System**: Snake draft format to build your dream team of hockey legends
- **Season Simulation**: Simulate full seasons with realistic game outcomes
- **Playoff System**: Compete for the championship through bracket-style playoffs
- **Player Stats**: Track individual player performance across seasons
- **Team Management**: Configure lines and strategy for your team

## Tech Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: Flask, SQLAlchemy, Flask-JWT-Extended
- **Database**: PostgreSQL

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (running locally)

## Quick Start

### 1. Setup PostgreSQL Database

```bash
# Create the database
createdb -U postgres lhl_db
```

### 2. Configure Environment

Create `backend/.env`:

```
DATABASE_URL=postgresql://postgres@localhost/lhl_db
JWT_SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 3. Install Dependencies & Seed Database

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create tables
python -c "from app import app; from extensions import db; app.app_context().push(); db.create_all()"

# Seed player data
cd ..
python scripts/seed_database.py

# Frontend
cd frontend
npm install
```

### 4. Run the Application

```bash
# From project root
bash start.sh
```

The app will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5001

## Usage

1. **Register/Login**: Create an account or log in
2. **Create Simulation**: Choose simulation length (20-25 years) and number of teams (4-12)
3. **Draft**: Select players in snake draft format to build your roster
4. **Simulate**: Watch your team compete through seasons and playoffs
5. **Track Stats**: View player and team statistics

## Project Structure

```
LHL/
├── backend/           # Flask API
│   ├── api/          # Route handlers
│   ├── models/       # SQLAlchemy models
│   ├── services/     # Business logic
│   └── app.py        # Main application
├── frontend/          # Next.js app
│   ├── app/          # Pages and components
│   └── lib/          # Utilities and types
├── data/             # Sample player data
├── scripts/          # Database scripts
└── start.sh          # Startup script
```

## API Endpoints

See [API_DOCS.md](./API_DOCS.md) for full API documentation.

### Key Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/simulations/create` - Create new simulation
- `GET /api/simulations/:id` - Get simulation details
- `POST /api/simulations/:id/draft` - Make draft pick
- `GET /api/players/` - Get all available players

## License

MIT
