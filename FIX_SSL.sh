#!/bin/bash

echo "🔧 Fixing SSL Certificate Issue..."
echo ""

# Option 1: Disable strict SSL (quick fix)
echo "Option 1: Configuring npm to handle SSL issues..."
npm config set strict-ssl false

# Option 2: Update CA certificates
echo "Option 2: Updating CA certificates..."
if command -v brew &> /dev/null; then
    brew install ca-certificates 2>/dev/null || echo "  (ca-certificates may already be installed)"
fi

# Option 3: Set registry to HTTP (less secure but works)
echo ""
echo "Trying installation with relaxed SSL..."
cd frontend

npm install --legacy-peer-deps

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation successful!"
    echo ""
    echo "To re-enable strict SSL later:"
    echo "  npm config set strict-ssl true"
else
    echo ""
    echo "Still failing. Trying HTTP registry..."
    npm config set registry http://registry.npmjs.org/
    npm install --legacy-peer-deps
    npm config set registry https://registry.npmjs.org/  # Reset to HTTPS
fi

cd ..
