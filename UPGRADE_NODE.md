# Fix Node.js Version Issue

## Problem
You have Node.js v16.20.2, but Next.js 14 requires Node >=18.17.0

## Solution Options

### Option 1: Upgrade Node.js (Recommended)

**Using Homebrew (macOS):**
```bash
brew install node@18
brew link --overwrite node@18
```

**Using NVM (Node Version Manager - Better):**
```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Restart terminal or run:
source ~/.zshrc

# Install and use Node 18
nvm install 18
nvm use 18
nvm alias default 18
```

**Verify:**
```bash
node --version  # Should show v18.x.x or higher
```

### Option 2: Use Next.js 13 (Works with Node 16)

I've already updated `frontend/package.json` to use Next.js 13.5.6 which is compatible with Node 16.

Just run:
```bash
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
cd ..
npm run dev
```

### Option 3: Use Yarn Instead

Yarn sometimes handles corrupted cache better:
```bash
# Install yarn if not installed
npm install -g yarn

# Then in frontend directory
cd frontend
yarn install
cd ..
npm run dev
```

## Quick Fix Script

I've created a fix script:
```bash
chmod +x fix-node-version.sh
./fix-node-version.sh
```

This will:
- Check your Node version
- Clear npm cache
- Clean corrupted files
- Install Next.js 13 (compatible with Node 16)

## Recommendation

**Best long-term solution:** Upgrade to Node.js 18+ using nvm. This gives you:
- Latest features
- Better performance
- Compatibility with modern packages
- Easy version switching

**Quick fix for now:** Use the fix script which downgrades to Next.js 13.
