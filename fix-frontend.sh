#!/bin/bash

echo "🔧 Fixing Frontend Installation..."
echo ""

cd frontend

echo "1. Cleaning old installation..."
rm -rf node_modules package-lock.json .next
echo "✓ Cleaned"
echo ""

echo "2. Clearing npm cache..."
npm cache clean --force
echo "✓ Cache cleared"
echo ""

echo "3. Installing dependencies (this may take a few minutes)..."
npm install
echo ""

if [ $? -eq 0 ]; then
    echo "✅ Frontend dependencies installed successfully!"
    echo ""
    echo "Now you can run: npm run dev"
else
    echo "❌ Installation failed. Try these alternatives:"
    echo ""
    echo "Option 1: Use yarn instead"
    echo "  yarn install"
    echo ""
    echo "Option 2: Install with verbose logging"
    echo "  npm install --verbose"
    echo ""
    echo "Option 3: Update npm first"
    echo "  npm install -g npm@latest"
    echo "  npm install"
fi

cd ..
