# Final Fix for Corrupted Cache Issue

The "incorrect data check" errors mean your package manager cache is corrupted. Here's how to fix it:

## Step 1: Clear ALL Caches

```bash
# Clear npm
npm cache clean --force
rm -rf ~/.npm

# Clear yarn  
yarn cache clean
rm -rf ~/.yarn/cache

# Clear frontend
cd frontend
rm -rf node_modules package-lock.json yarn.lock .next
cd ..
```

Or run the script:
```bash
chmod +x FIX_CACHE.sh
./FIX_CACHE.sh
```

## Step 2: Try Installing with Extended Timeout

```bash
cd frontend

# Try yarn with long timeout
yarn install --network-timeout 100000

# OR try npm with timeout
npm install --legacy-peer-deps --network-timeout=100000
```

## Step 3: If Still Failing - Use Different Registry

Sometimes the default registry has issues. Try a different one:

```bash
cd frontend

# Use Taobao mirror (faster, more reliable in some regions)
yarn config set registry https://registry.npmmirror.com
yarn install

# Or use npm with different registry
npm config set registry https://registry.npmmirror.com
npm install --legacy-peer-deps
```

## Step 4: Nuclear Option - Skip Optional Dependencies

If the SWC packages keep failing, install without optional deps:

```bash
cd frontend
yarn install --ignore-optional
# or
npm install --legacy-peer-deps --no-optional
```

## Step 5: Manual Package Installation

If all else fails, install core packages manually:

```bash
cd frontend

# Install just the essentials
yarn add next@13.4.19 react@^18.2.0 react-dom@^18.2.0
yarn add -D typescript @types/react @types/node tailwindcss postcss autoprefixer
yarn add axios js-cookie
yarn add @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

## Quick Test: Use npx (No Installation Needed)

If installation keeps failing, you can run Next.js directly without installing:

```bash
cd frontend
npx next@13.4.19 dev
```

This downloads Next.js on-the-fly and runs it. Not ideal for development, but it will work.

## Recommended: Start Fresh

If nothing works, the cache corruption might be system-wide. Try:

```bash
# 1. Clear everything
cd frontend
rm -rf node_modules package-lock.json yarn.lock .next
cd ..
rm -rf ~/.npm ~/.yarn

# 2. Restart your terminal/computer (clears system cache)

# 3. Try again with yarn
cd frontend
yarn install --network-timeout 100000
```

The issue is corrupted downloads in your cache. Clearing all caches and using a longer timeout should fix it.
