@echo off

set "SCRIPT_DIR=%~dp0"
echo Script directory: %SCRIPT_DIR%

call %SCRIPT_DIR%\coffy-env\Scripts\activate
python introbot.py