# Workaround: Run Without Installing

Since installation keeps failing due to corrupted cache, here's a workaround to get the app running:

## Option 1: Update npm First (Most Likely Fix)

Your npm is very old (8.19.4). Newer versions handle cache better:

```bash
# Update npm (may need sudo)
sudo npm install -g npm@latest

# Or without sudo (if you have nvm)
npm install -g npm@latest

# Then clear cache and try again
npm cache clean --force
rm -rf ~/.npm
cd frontend
npm install --legacy-peer-deps
```

## Option 2: Use Different Registry

The npm registry might be having issues. Try a mirror:

```bash
cd frontend

# Use Chinese mirror (often more reliable)
npm config set registry https://registry.npmmirror.com
npm install --legacy-peer-deps

# Reset to default after
npm config set registry https://registry.npmjs.org
```

## Option 3: Manual Package Download

Download Next.js manually and extract:

```bash
cd frontend
mkdir -p node_modules/next
cd node_modules/next

# Download Next.js directly
curl -L https://registry.npmjs.org/next/-/next-13.4.19.tgz -o next.tgz
tar -xzf next.tgz --strip-components=1
rm next.tgz

# Install other minimal deps
cd ../../..
npm install react react-dom --legacy-peer-deps
npm install axios js-cookie --legacy-peer-deps
```

## Option 4: Use Docker (Clean Environment)

If nothing works, use Docker to run in a clean environment:

```bash
# Create Dockerfile
cat > Dockerfile << EOF
FROM node:18-alpine
WORKDIR /app
COPY frontend/package.json .
RUN npm install
COPY frontend .
CMD ["npm", "run", "dev"]
EOF

# Run
docker build -t lhl-frontend .
docker run -p 3000:3000 lhl-frontend
```

## Option 5: Simplest - Just Run Backend for Now

Since the backend is working, you can test the API directly:

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python app.py

# Terminal 2: Test API
curl http://localhost:5000/api/health
```

The frontend is just a UI - the core functionality (simulation engine, API) works without it.

## Recommended: Update npm First

The most likely fix is updating npm:

```bash
# Check current version
npm --version

# Update (choose one):
# With sudo:
sudo npm install -g npm@latest

# Without sudo (if you have nvm):
npm install -g npm@latest

# Then try again
cd frontend
npm cache clean --force
rm -rf ~/.npm node_modules
npm install --legacy-peer-deps
```

Newer npm versions (11.x) have much better cache handling and should fix the corruption issues.
