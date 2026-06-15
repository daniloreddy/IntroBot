#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

echo "=== ruff lint ==="
.venv/bin/ruff check .

echo "=== ruff format ==="
.venv/bin/ruff format --check .

echo "=== mypy ==="
.venv/bin/mypy introbot.py cogs/ services/ utils/

if [ -d "tests" ]; then
    echo "=== pytest ==="
    .venv/bin/pytest tests/ -v
else
    echo "=== pytest: nessuna directory tests/, skip ==="
fi
