# LHL Setup Guide

## Complete Setup Instructions

This guide will help you get the Legend Hockey League app running locally.

## Step 1: System Requirements

Ensure you have these installed:
- **Node.js** 18+ and npm
- **Python** 3.10+
- **PostgreSQL** 14+
- **Rust** 1.70+ (optional, for compiling simulation engine)

## Step 2: Database Setup

```bash
# Install PostgreSQL if not already installed
# macOS:
brew install postgresql@14
brew services start postgresql@14

# Create database
createdb lhl_db

# Create user (optional)
psql postgres
CREATE USER lhl_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE lhl_db TO lhl_user;
\q
```

## Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (note: may need PostgreSQL dev libraries)
# macOS:
brew install postgresql

# Install Python packages
pip install Flask==3.0.2 Flask-CORS==4.0.0 Flask-SQLAlchemy==3.1.1 Flask-JWT-Extended==4.6.0 python-dotenv==1.0.1 openpyxl==3.1.2 alembic==1.13.1 bcrypt==4.1.2

# For PostgreSQL, use psycopg3 instead:
pip install psycopg[binary]

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://localhost/lhl_db
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
FLASK_ENV=development
FLASK_APP=app.py
RUST_BINARY_PATH=../simulation/target/release/hockey_sim
EOF
```

## Step 4: Initialize Database

```bash
# Still in backend directory with venv activated
cd ..
python3 scripts/seed_database.py
```

This will:
- Create all database tables
- Seed 60+ legendary players
- Seed 24 goalies
- Seed 18 coaches

## Step 5: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:5000
EOF
```

## Step 6: Rust Simulation Engine (Optional)

The app includes a mock simulator that works without Rust. To use the real Rust engine:

```bash
cd simulation

# Install Rust if not installed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Compile the simulation engine
cargo build --release

# The binary will be at: simulation/target/release/hockey_sim
```

## Step 7: Run the Application

### Terminal 1 - Backend
```bash
cd backend
source venv/bin/activate
python app.py
```

Backend will run on http://localhost:5000

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

Frontend will run on http://localhost:3000

## Step 8: Access the App

1. Open http://localhost:3000
2. Click "Register" to create an account
3. Start a new simulation
4. Complete the draft
5. Begin simulating!

## Troubleshooting

### PostgreSQL Connection Issues

If you see database connection errors:
```bash
# Check if PostgreSQL is running
pg_isready

# Check connection string in backend/.env
# Should match your PostgreSQL setup
```

### Python Package Installation Issues

If `psycopg2-binary` fails to install:
```bash
# Use psycopg3 instead (better compatibility)
pip uninstall psycopg2-binary
pip install "psycopg[binary]"

# Update requirements.txt to use psycopg instead
```

### Frontend API Connection Issues

Check that:
1. Backend is running on port 5000
2. `NEXT_PUBLIC_API_URL` in frontend/.env.local points to http://localhost:5000
3. No CORS errors in browser console

### Database Not Seeding

If seed script fails:
```bash
# Manually create tables
cd backend
source venv/bin/activate
python3
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()

# Then run seed script again
cd ..
python3 scripts/seed_database.py
```

## Quick Test

After setup, test the following flow:
1. ✅ Register a user
2. ✅ Login
3. ✅ Create a simulation (6 teams, 20 years)
4. ✅ Draft completes (20 players + 1 coach per team)
5. ✅ Simulate to playoffs
6. ✅ View stats and standings

## Production Deployment

See [README.md](README.md) for Vercel deployment instructions.

## Need Help?

- Check the main [README.md](README.md)
- Review API documentation in README
- Check algorithm documentation in [simulation/ALGORITHM.md](simulation/ALGORITHM.md)
- Open an issue on GitHub

---

Happy simulating! 🏒
