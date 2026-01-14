# Simple Fix - Your Node.js is Too Old

## The Problem
- You have Node.js v16.20.2
- Latest npm requires Node 20.17.0+
- Next.js 13+ works better with Node 18+

## Solution: Upgrade Node.js

### Option 1: Use Homebrew (Easiest)

```bash
# Install Node 18
brew install node@18

# Link it (overwrites old version)
brew link --overwrite node@18

# Verify
node --version  # Should show v18.x.x
npm --version   # Should show 9.x.x or 10.x.x

# Then fix frontend
cd frontend
npm cache clean --force
rm -rf ~/.npm node_modules package-lock.json
npm install --legacy-peer-deps
```

### Option 2: Use NVM (Best - Allows Multiple Versions)

```bash
# Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Restart terminal or run:
source ~/.zshrc

# Install and use Node 18
nvm install 18
nvm use 18
nvm alias default 18

# Verify
node --version  # Should show v18.x.x

# Then fix frontend
cd frontend
npm cache clean --force
rm -rf ~/.npm node_modules package-lock.json
npm install --legacy-peer-deps
```

### Option 3: Just Update npm (Quick Fix, But Node 16 Still Old)

```bash
# Install npm 9 (compatible with Node 16)
npm install -g npm@9.9.3

# Verify
npm --version  # Should show 9.9.3

# Then try frontend install
cd frontend
npm cache clean --force
rm -rf ~/.npm node_modules
npm install --legacy-peer-deps
```

## Recommended: Option 1 or 2

Upgrading to Node 18 will:
- ✅ Fix the cache corruption issues
- ✅ Give you modern npm
- ✅ Make Next.js installation work smoothly
- ✅ Future-proof your setup

After upgrading Node.js, the frontend installation should work perfectly!

## After Upgrading Node.js

```bash
# Clear everything
cd frontend
npm cache clean --force
rm -rf ~/.npm node_modules package-lock.json .next

# Install fresh
npm install --legacy-peer-deps

# Start servers
cd ..
npm run dev
```
