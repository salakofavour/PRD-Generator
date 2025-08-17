@echo off
echo Starting PRD Generator...
echo.

REM Check if virtual environment exists
if exist "venv" (
    echo Activating virtual environment...
    call venv\Scripts\activate
) else (
    echo No virtual environment found. Creating one...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing requirements...
    pip install -r requirements.txt
)

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please copy .env.example to .env and add your OpenAI API key.
    echo.
    pause
    exit /b 1
)

echo.
echo Starting Streamlit application...
echo Open your browser to: http://localhost:8501
echo.
streamlit run app.py

pause