#!/bin/bash

echo "🚨 NUCLEAR FIX - Complete Cache & npm Reset"
echo "=========================================="
echo ""

# Step 1: Update npm (old version might be the issue)
echo "Step 1: Updating npm..."
npm install -g npm@latest --force 2>&1 | grep -v "WARN" || echo "  (npm update may require sudo, continuing...)"

# Step 2: Nuclear cache clear
echo ""
echo "Step 2: Clearing ALL caches..."
npm cache clean --force
rm -rf ~/.npm
rm -rf ~/.npm/_cacache
rm -rf ~/.yarn/cache
rm -rf ~/.yarn/berry/cache
yarn cache clean 2>/dev/null || true

# Step 3: Clear system temp
echo "Step 3: Clearing system temp..."
rm -rf /tmp/npm-* /tmp/yarn-* /tmp/.npm 2>/dev/null || true

# Step 4: Clear frontend
echo "Step 4: Cleaning frontend..."
cd frontend
rm -rf node_modules package-lock.json yarn.lock .next .yarn

# Step 5: Try with fresh npm and no cache
echo ""
echo "Step 5: Installing with --prefer-offline=false (force fresh download)..."
npm install --legacy-peer-deps --prefer-offline=false --cache /tmp/npm-cache 2>&1 | tail -20

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Installation completed."
    cd ..
    echo ""
    echo "Now run: npm run dev"
else
    echo ""
    echo "❌ Still failing. Trying alternative registry..."
    cd ..
    
    # Try different registry
    echo ""
    echo "Step 6: Trying with different registry (npmmirror.com)..."
    cd frontend
    npm config set registry https://registry.npmmirror.com
    npm install --legacy-peer-deps --prefer-offline=false
    npm config set registry https://registry.npmjs.org  # Reset to default
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo ""
        echo "✅ SUCCESS with alternative registry!"
        cd ..
        echo "Now run: npm run dev"
    else
        echo ""
        echo "❌ All methods failed."
        echo ""
        echo "Last resort options:"
        echo "1. Restart your computer (clears system cache)"
        echo "2. Update Node.js: brew install node@18"
        echo "3. Use Docker to run in clean environment"
        exit 1
    fi
fi

cd ..
