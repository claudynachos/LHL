#!/bin/bash

echo "🔧 Fixing Corrupted Cache Issues..."
echo ""

# Clear npm cache
echo "1. Clearing npm cache..."
npm cache clean --force
rm -rf ~/.npm

# Clear yarn cache
echo "2. Clearing yarn cache..."
yarn cache clean 2>/dev/null || true
rm -rf ~/.yarn/cache
rm -rf ~/.yarn/berry/cache

# Clear system temp
echo "3. Clearing temp files..."
rm -rf /tmp/npm-* /tmp/yarn-* 2>/dev/null || true

# Clear frontend
echo "4. Cleaning frontend directory..."
cd frontend
rm -rf node_modules package-lock.json yarn.lock .next .yarn

echo ""
echo "✅ All caches cleared!"
echo ""
echo "Now try installing again:"
echo "  yarn install --network-timeout 100000"
echo ""
echo "Or if that fails, try:"
echo "  npm install --legacy-peer-deps --network-timeout=100000"

cd ..
