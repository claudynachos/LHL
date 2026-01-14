# Manual Fix Instructions

Since npm install is failing, try these steps:

## Option 1: Install with verbose logging to see the error

```bash
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json .next
npm install --legacy-peer-deps --verbose 2>&1 | tee install.log
```

Then check `install.log` for the actual error.

## Option 2: Use Yarn (Recommended)

```bash
# Install yarn via Homebrew (no sudo needed)
brew install yarn

# Then install frontend deps
cd frontend
yarn install

# Start with yarn
cd ..
# Terminal 1:
cd backend && source venv/bin/activate && python app.py
# Terminal 2:
cd frontend && yarn dev
```

## Option 3: Fix npm permissions

```bash
# Fix npm permissions (don't use sudo)
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc

# Then try again
cd frontend
npm install --legacy-peer-deps
```

## Option 4: Use npx to run Next.js directly

If installation keeps failing, you can try running Next.js via npx:

```bash
cd frontend
npx next@13.5.6 dev
```

## Quick Test: Check what's actually failing

```bash
cd frontend
npm install --legacy-peer-deps 2>&1 | head -50
```

This will show you the first 50 lines of the error so we can see what's actually wrong.
