@echo off
cd /d "%~dp0.."

if not exist ".venv\" (
    echo venv non trovato, creazione in corso...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

python introbot.py
