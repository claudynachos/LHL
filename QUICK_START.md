# Quick Start Guide - Run These Commands

## Step 1: Go to project root
```bash
cd /Users/michel/Documents/CODING/LHL
```

## Step 2: Make scripts executable
```bash
chmod +x COMPLETE_FIX.sh
chmod +x START_SERVERS.sh
```

## Step 3: Run the fix
```bash
./COMPLETE_FIX.sh
```

## Step 4: Start servers
```bash
npm run dev
```

---

## OR: Manual Quick Fix

If scripts don't work, run these commands one by one:

```bash
# Go to root
cd /Users/michel/Documents/CODING/LHL

# Fix frontend
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json .next
npm install --legacy-peer-deps
cd ..

# Start servers
npm run dev
```

---

## If npm install still fails:

```bash
cd frontend

# Try yarn instead
yarn install

# Then start separately:
# Terminal 1 (backend):
cd ../backend
source venv/bin/activate
python app.py

# Terminal 2 (frontend):
cd frontend
yarn dev
```
