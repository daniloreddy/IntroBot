@echo off
cd /d "%~dp0.."

if not exist "venv\" (
    echo venv non trovato, creazione in corso...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.dev.txt
) else (
    call venv\Scripts\activate
)

echo === ruff lint ===
ruff check .
if errorlevel 1 exit /b 1

echo === ruff format ===
ruff format --check .
if errorlevel 1 exit /b 1

echo === mypy ===
mypy introbot.py cogs\ services\ utils\
if errorlevel 1 exit /b 1

if exist "tests\" (
    echo === pytest ===
    pytest tests\ -v
    if errorlevel 1 exit /b 1
) else (
    echo === pytest: nessuna directory tests\, skip ===
)
