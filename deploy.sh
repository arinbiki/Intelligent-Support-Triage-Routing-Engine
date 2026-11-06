#!/usr/bin/env bash
# ==============================================================================
# One-Click Turnkey Deployment Script for Linux / macOS
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================================="
echo "   Intelligent Support Triage & Routing Engine | Turnkey Installer (Unix)"
echo "=========================================================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[-] Python 3.11+ is required but not found. Please install Python and retry."
    exit 1
fi

echo "[+] Found Python: $(python3 --version)"

# Setup Virtual Environment
if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment at .venv..."
    python3 -m venv .venv
fi

VENV_PYTHON=".venv/bin/python"

echo "[*] Installing Python dependencies..."
$VENV_PYTHON -m pip install --upgrade pip --quiet
$VENV_PYTHON -m pip install -e . --quiet
$VENV_PYTHON -c "import nltk; nltk.download('vader_lexicon', quiet=True)"
echo "[+] Core dependencies and VADER lexicon installed."

# Initialize SQLite database
echo "[*] Initializing SQLite WAL database & ERP seeds..."
$VENV_PYTHON database/init_db.py

# Train production model
echo "[*] Training Department Classifier & building model bundle..."
$VENV_PYTHON models/train_model.py

# Run test suite
echo "[*] Executing automated verification suite..."
$VENV_PYTHON -m unittest discover -s tests

echo "=========================================================================="
echo "✅ DEPLOYMENT COMPLETE! Engine is ready for production use."
echo "   Run 1M Simulation:  .venv/bin/python scripts/simulate_1m_live_operations.py"
echo "=========================================================================="
