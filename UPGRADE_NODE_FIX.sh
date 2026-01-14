#!/bin/bash

echo "🔧 Upgrading Node.js and npm..."
echo ""

# Check current versions
echo "Current versions:"
node --version
npm --version
echo ""

echo "Node.js 16 is too old. You need Node 18+ for modern packages."
echo ""
echo "OPTION 1: Install Node 18 via Homebrew (Recommended)"
echo "  brew install node@18"
echo "  brew link --overwrite node@18"
echo ""
echo "OPTION 2: Use NVM (Node Version Manager - Best)"
echo "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
echo "  source ~/.zshrc"
echo "  nvm install 18"
echo "  nvm use 18"
echo "  nvm alias default 18"
echo ""
echo "OPTION 3: Update npm to version compatible with Node 16"
echo "  npm install -g npm@9.9.3"
echo ""

read -p "Choose option (1/2/3) or press Enter to exit: " choice

case $choice in
  1)
    echo "Installing Node 18 via Homebrew..."
    brew install node@18
    brew link --overwrite node@18
    echo "✅ Node.js updated!"
    echo "New version: $(node --version)"
    ;;
  2)
    echo "Installing NVM..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
    echo ""
    echo "✅ NVM installed! Now run:"
    echo "  source ~/.zshrc"
    echo "  nvm install 18"
    echo "  nvm use 18"
    ;;
  3)
    echo "Updating npm to version compatible with Node 16..."
    npm install -g npm@9.9.3
    echo "✅ npm updated!"
    echo "New version: $(npm --version)"
    ;;
  *)
    echo "Exiting. Run this script again when ready."
    exit 0
    ;;
esac

echo ""
echo "Now try installing frontend dependencies:"
echo "  cd frontend"
echo "  npm cache clean --force"
echo "  rm -rf ~/.npm node_modules"
echo "  npm install --legacy-peer-deps"
