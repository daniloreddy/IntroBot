#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
    echo "venv non trovato, creazione in corso..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.dev.txt
else
    source .venv/bin/activate
fi

echo "=== ruff lint ==="
ruff check .

echo "=== ruff format ==="
ruff format --check .

echo "=== mypy ==="
mypy introbot.py cogs/ services/ utils/

if [ -d "tests" ]; then
    echo "=== pytest ==="
    pytest tests/ -v
else
    echo "=== pytest: nessuna directory tests/, skip ==="
fi
