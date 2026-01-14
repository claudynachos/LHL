# Legend Hockey League (LHL)

A web-based hockey simulation game featuring historical NHL legends. Draft teams and simulate 20-25 year seasons with detailed statistics tracking.

## Features

- **Draft System**: Snake draft with 20 players + 1 coach per team
- **Simulation Engine**: Rust-powered game simulation with realistic NHL statistics
- **Multiple League Sizes**: 4, 6, 8, 10, or 12 teams
- **Detailed Stats**: Track goals, assists, hits, blocks, +/-, and more
- **Lines Configuration**: Customize your forward lines, defense pairs, and goalies
- **Multi-Season Support**: Simulate 20-25 year dynasties
- **Admin Panel**: User management and analytics dashboard

## Tech Stack

- **Frontend**: Next.js 14 with TypeScript, TailwindCSS
- **Backend**: Python Flask with SQLAlchemy
- **Simulation**: Rust (compiled binary)
- **Database**: PostgreSQL
- **Authentication**: JWT tokens
- **Deployment**: Vercel

## Project Structure

```
lhl/
├── frontend/              # Next.js application
│   ├── app/              # App router pages
│   ├── components/       # React components
│   └── lib/             # API clients and utilities
├── backend/              # Flask API
│   ├── api/             # Route handlers
│   ├── models/          # SQLAlchemy models
│   └── services/        # Business logic
├── simulation/           # Rust simulation engine
│   └── src/             # Rust source code
├── data/                # Player/coach data
└── scripts/             # Utility scripts
```

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- PostgreSQL
- Rust 1.70+ (for compiling simulation engine)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd LHL
```

2. **Set up the backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up the database**
```bash
# Create PostgreSQL database
createdb lhl_db

# Copy environment file
cp .env.example .env

# Edit .env with your database credentials
# DATABASE_URL=postgresql://user:password@localhost/lhl_db
# JWT_SECRET_KEY=your-secret-key

# Run migrations and seed data
python scripts/seed_database.py
```

4. **Compile Rust simulation engine**
```bash
cd ../simulation
cargo build --release
```

5. **Set up the frontend**
```bash
cd ../frontend
npm install
cp .env.example .env.local

# Edit .env.local
# NEXT_PUBLIC_API_URL=http://localhost:5000
```

### Running Locally

1. **Start the backend** (Terminal 1)
```bash
cd backend
source venv/bin/activate
python app.py
```

2. **Start the frontend** (Terminal 2)
```bash
cd frontend
npm run dev
```

3. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## Usage

### Creating Your First Simulation

1. Register an account or login
2. Click "Start New Simulation"
3. Choose league size (4-12 teams) and duration (20-25 years)
4. Complete the snake draft (20 players + 1 coach per team)
5. Configure your team's lines
6. Start simulating!

### Simulation Controls

- **Simulate to Playoffs**: Run all regular season games
- **Simulate Playoff Round**: Simulate one playoff round
- **Simulate Full Season**: Complete entire season including playoffs

### Viewing Stats

- **Season Stats**: Current season leaders
- **All-Time Stats**: Historical records across all seasons
- **Standings**: Conference tables with W-L-PTS
- **Trophies**: Award winners by season

## API Documentation

### Authentication

#### POST /api/auth/register
Register a new user
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

#### POST /api/auth/login
Login user
```json
{
  "username": "string",
  "password": "string"
}
```

### Simulations

#### POST /api/simulations/create
Create new simulation
```json
{
  "year_length": 20,
  "num_teams": 6
}
```

#### GET /api/simulations/{id}
Get simulation details

#### POST /api/simulations/{id}/draft
Make a draft pick
```json
{
  "player_id": 123
}
```

#### POST /api/simulations/{id}/simulate-to-playoffs
Simulate regular season

#### POST /api/simulations/{id}/simulate-season
Simulate full season

### Stats

#### GET /api/stats/season/{simulation_id}
Get current season statistics

#### GET /api/stats/standings/{simulation_id}
Get league standings

## Simulation Algorithm

The Rust simulation engine uses realistic NHL statistics and formulas. See [simulation/ALGORITHM.md](simulation/ALGORITHM.md) for detailed documentation including:

- Ice time distribution (Line 1: 35%, Line 2: 30%, etc.)
- Skill weightings (OFF, DEF, PHYS, LEAD, CONST)
- Goal probability calculations
- Home ice advantage (+5%)
- Playoff physicality boost (+20%)
- Coach impact modifiers

## Deployment to Vercel

### Prerequisites
- Vercel account
- PostgreSQL database (Vercel Postgres or external provider)

### Steps

1. **Install Vercel CLI**
```bash
npm install -g vercel
```

2. **Set environment variables in Vercel**
```bash
vercel env add DATABASE_URL
vercel env add JWT_SECRET_KEY
```

3. **Deploy**
```bash
vercel --prod
```

4. **Upload Rust binary**
After compilation, ensure the Rust binary is included in the deployment or uploaded separately to Vercel storage.

## Testing

### Run backend tests
```bash
cd backend
pytest
```

### Run frontend tests
```bash
cd frontend
npm test
```

### Test simulation engine
```bash
cd simulation
cargo test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Performance Targets

- ✅ Draft team and simulate season in < 5 clicks
- ✅ Single game simulation: < 100ms
- ✅ Full season (82 games): < 5 seconds
- ✅ Stats pages load: < 1 second

## Future Enhancements (V2)

- Multiplayer synchronization
- In-season trades
- Player progression system
- Advanced analytics and visualizations
- Mobile app (iOS/Android)
- Custom leagues and rules

## License

MIT License

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

Built with ❤️ for hockey fans everywhere
