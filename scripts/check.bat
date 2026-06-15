@echo off
cd /d "%~dp0.."

echo === ruff lint ===
.venv\Scripts\ruff check .
if errorlevel 1 exit /b 1

echo === ruff format ===
.venv\Scripts\ruff format --check .
if errorlevel 1 exit /b 1

echo === mypy ===
.venv\Scripts\mypy introbot.py cogs\ services\ utils\
if errorlevel 1 exit /b 1

if exist "tests\" (
    echo === pytest ===
    .venv\Scripts\pytest tests\ -v
    if errorlevel 1 exit /b 1
) else (
    echo === pytest: nessuna directory tests\, skip ===
)
