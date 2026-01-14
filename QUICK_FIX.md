# Quick Fix for Installation Issues

## Problem
You're seeing:
- `ModuleNotFoundError: No module named 'flask'` (backend)
- `sh: next: command not found` (frontend)
- npm package corruption errors

## Solution

Run this command in your terminal:

```bash
bash fix-install.sh
```

Or manually:

### Step 1: Clean npm cache
```bash
npm cache clean --force
```

### Step 2: Install backend dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install Flask==3.0.2 Flask-CORS==4.0.0 Flask-SQLAlchemy==3.1.1 Flask-JWT-Extended==4.6.0 python-dotenv==1.0.1 openpyxl==3.1.2 alembic==1.13.1 bcrypt==4.1.2 "psycopg[binary]"
deactivate
cd ..
```

### Step 3: Install frontend dependencies
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
```

### Step 4: Start the app
```bash
npm run dev
```

## Alternative: Use the fix script

I've created `fix-install.sh` that does all of this automatically:

```bash
chmod +x fix-install.sh
./fix-install.sh
```

Then run:
```bash
npm run dev
```

## If npm install still fails

Try these in order:

1. **Clear npm cache and retry:**
```bash
npm cache clean --force
cd frontend
rm -rf node_modules package-lock.json
npm install
```

2. **Use yarn instead:**
```bash
cd frontend
yarn install
```

3. **Install with verbose logging:**
```bash
cd frontend
npm install --verbose
```

4. **Check your npm version:**
```bash
npm --version
# Should be 8+ or 9+
# If older, update: npm install -g npm@latest
```
