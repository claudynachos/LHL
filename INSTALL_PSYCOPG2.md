# Fix: psycopg2 Installation Issue

## Problem
You're seeing: `ModuleNotFoundError: No module named 'psycopg2'`

This happens because `psycopg2-binary` can be tricky to install on some systems.

## Quick Fix

Run this command:

```bash
cd backend
source venv/bin/activate
pip install psycopg2-binary
deactivate
cd ..
```

Then try starting again:
```bash
npm run dev
```

## Alternative Solutions

### Option 1: Use psycopg2-binary (Recommended)
```bash
cd backend
source venv/bin/activate
pip uninstall psycopg -y  # Remove psycopg3 if installed
pip install psycopg2-binary==2.9.9
deactivate
cd ..
```

### Option 2: Install from requirements.txt
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..
```

### Option 3: If psycopg2-binary fails (macOS with M1/M2)

You might need PostgreSQL development libraries:

```bash
# Install PostgreSQL (if not already installed)
brew install postgresql

# Then install psycopg2-binary
cd backend
source venv/bin/activate
pip install psycopg2-binary
deactivate
cd ..
```

### Option 4: Use psycopg3 (requires code change)

If you want to use the newer psycopg3, you need to update the connection string:

1. Install psycopg3:
```bash
cd backend
source venv/bin/activate
pip install "psycopg[binary]"
deactivate
cd ..
```

2. Update `backend/app.py` line 11:
```python
# Change from:
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/lhl_db')

# To:
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql+psycopg://localhost/lhl_db')
```

## Verify Installation

After installing, verify it works:

```bash
cd backend
source venv/bin/activate
python -c "import psycopg2; print('psycopg2 installed successfully!')"
deactivate
cd ..
```

If this prints without errors, you're good to go!

## Still Having Issues?

If `psycopg2-binary` won't install, try:

1. **Update pip:**
```bash
pip install --upgrade pip
pip install psycopg2-binary
```

2. **Use pre-built wheel:**
```bash
pip install --only-binary :all: psycopg2-binary
```

3. **Check Python version:**
```bash
python --version
# Should be 3.10+ but not 3.14 (too new, may have issues)
```

If you're on Python 3.14, consider using Python 3.11 or 3.12 for better compatibility.
