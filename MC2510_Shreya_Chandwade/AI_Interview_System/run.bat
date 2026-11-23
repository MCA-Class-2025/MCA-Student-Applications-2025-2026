@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\pip.exe install -r requirements.txt
)

echo Starting AI Interview System at http://127.0.0.1:8000
call venv\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8000 --reload
