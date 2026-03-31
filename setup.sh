#!/bin/bash
# setup.sh -- One-click setup for AI Fitness Coach
#
# This script will:
#   1. Check Python version
#   2. Install dependencies (if any)
#   3. Create config files from examples
#   4. Initialize the database
#   5. Guide you through profile setup
#   6. Optionally install cron jobs

set -euo pipefail

AFC_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "======================================"
echo "  AI Fitness Coach -- Setup"
echo "======================================"
echo ""

# --- 1. Check Python ---
echo "[1/6] Checking Python..."
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    echo "  Found Python ${PY_VERSION}"
    if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]); then
        echo "  Error: Python 3.12+ required (found ${PY_VERSION})"
        exit 1
    fi
    echo "  OK"
else
    echo "  Error: Python 3 not found. Install Python 3.12+ and try again."
    exit 1
fi
echo ""

# --- 2. Install dependencies ---
echo "[2/6] Checking dependencies..."
if [ -f "${AFC_DIR}/requirements.txt" ]; then
    # Currently no external deps needed, but run pip if any are uncommented
    ACTIVE_DEPS=$(grep -v '^#' "${AFC_DIR}/requirements.txt" | grep -v '^$' | head -1 || true)
    if [ -n "$ACTIVE_DEPS" ]; then
        echo "  Installing Python packages..."
        pip3 install -r "${AFC_DIR}/requirements.txt"
    else
        echo "  No external dependencies needed (uses Python standard library only)"
    fi
fi
echo ""

# --- 3. Create config files ---
echo "[3/6] Setting up configuration..."

# .env
if [ ! -f "${AFC_DIR}/.env" ]; then
    cp "${AFC_DIR}/config/.env.example" "${AFC_DIR}/.env"
    echo "  Created .env from template"
else
    echo "  .env already exists, skipping"
fi

# profile.json
if [ ! -f "${AFC_DIR}/config/profile.json" ]; then
    cp "${AFC_DIR}/config/profile.example.json" "${AFC_DIR}/config/profile.json"
    echo "  Created config/profile.json from template"
else
    echo "  config/profile.json already exists, skipping"
fi

# data directory
mkdir -p "${AFC_DIR}/data"
echo ""

# --- 4. Initialize database ---
echo "[4/6] Initializing database..."
python3 "${AFC_DIR}/src/db_manager.py" "${AFC_DIR}/data/fitness.db"
echo ""

# --- 5. Profile setup ---
echo "[5/6] Profile setup..."
echo ""
echo "  Your profile is at: config/profile.json"
echo "  Edit it to customize your:"
echo "    - Name"
echo "    - Fitness goals (target weight, primary goal)"
echo "    - Nutrition targets (daily calories, protein)"
echo "    - Workout preferences (duration, frequency, equipment)"
echo "    - Gym location and available equipment"
echo ""

read -p "  Open profile.json for editing now? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v code &>/dev/null; then
        code "${AFC_DIR}/config/profile.json"
    elif [ -n "${EDITOR:-}" ]; then
        $EDITOR "${AFC_DIR}/config/profile.json"
    elif command -v nano &>/dev/null; then
        nano "${AFC_DIR}/config/profile.json"
    elif command -v vim &>/dev/null; then
        vim "${AFC_DIR}/config/profile.json"
    else
        echo "  No editor found. Please edit config/profile.json manually."
    fi
fi
echo ""

# --- 6. Cron jobs (optional) ---
echo "[6/6] Automated reminders (optional)..."
echo ""
echo "  The AI Fitness Coach can send automated WhatsApp reminders via cron jobs."
echo "  This requires:"
echo "    - Claude Code CLI installed"
echo "    - WhatsApp channel plugin configured"
echo "    - AFC_WHATSAPP_CHAT_ID set in .env"
echo ""

read -p "  Install cron jobs for automated reminders? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    bash "${AFC_DIR}/cron/install-cron.sh"
fi
echo ""

# --- Done ---
echo "======================================"
echo "  Setup complete!"
echo "======================================"
echo ""
echo "Quick start:"
echo "  # Log your weight"
echo "  python3 src/fitness-cli.py log-weight 70.5"
echo ""
echo "  # Log a meal"
echo '  python3 src/fitness-cli.py log-food "Chicken breast and rice" 550 45 60 12'
echo ""
echo "  # Get a workout suggestion"
echo "  python3 src/fitness-cli.py suggest-workout --duration 40"
echo ""
echo "  # Check your status"
echo "  python3 src/fitness-cli.py quick-status"
echo ""
echo "For full command reference: docs/COMMANDS.md"
echo "For architecture details:   docs/ARCHITECTURE.md"
echo ""
