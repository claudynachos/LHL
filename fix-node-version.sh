#!/bin/bash

echo "🔧 Fixing Node.js Version and npm Cache Issues..."
echo ""

# Check Node version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
echo "Current Node version: $(node --version)"

if [ "$NODE_VERSION" -lt 18 ]; then
    echo ""
    echo "⚠️  Node.js version is too old (need 18+, you have $(node --version))"
    echo ""
    echo "OPTION 1: Upgrade Node.js (Recommended)"
    echo "  Install nvm: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    echo "  Then: nvm install 18 && nvm use 18"
    echo ""
    echo "OPTION 2: Use Next.js 13 (compatible with Node 16)"
    echo "  I've already updated package.json to use Next.js 13.5.6"
    echo ""
    read -p "Press Enter to continue with Next.js 13 (or Ctrl+C to upgrade Node first)..."
fi

echo ""
echo "1. Clearing npm cache..."
npm cache clean --force
echo "✓ Cache cleared"
echo ""

echo "2. Removing corrupted files..."
cd frontend
rm -rf node_modules package-lock.json .next
echo "✓ Cleaned"
echo ""

echo "3. Installing dependencies with Next.js 13 (compatible with Node 16)..."
npm install --legacy-peer-deps
echo ""

if [ $? -eq 0 ]; then
    echo "✅ Installation successful!"
    echo ""
    echo "Now run: cd .. && npm run dev"
else
    echo "❌ Installation failed. Try:"
    echo "  1. Upgrade Node.js to 18+: brew install node@18"
    echo "  2. Or use yarn: yarn install"
fi

cd ..
