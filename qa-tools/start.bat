@echo off
echo Starting QA Tools Desktop...

REM Check if .venv exists, if not create it
IF NOT EXIST ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Checking Python dependencies...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Run the application
echo Launching application...
python -m app.main
pause
