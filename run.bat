@echo off

set VENV_DIR=.venv

if not exist "%VENV_DIR%" (
    echo Virtual environment not found. Creating...
    python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate"

if exist requirements.txt (
    echo Installing requirements...
    pip install -r requirements.txt
    echo Running main.py
    python main.py
    call "%VENV_DIR%\Scripts\deactivate"
) else (
    echo requirements.txt not found. Aborting.
)

pause
