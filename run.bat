@echo off
echo Starting Personal Expense Tracker...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/updating dependencies...
pip install -r requirements.txt

echo.
echo Starting Flask application...
echo Server will be available at: http://localhost:5000
echo Press CTRL+C to stop the server
echo.

python app.py