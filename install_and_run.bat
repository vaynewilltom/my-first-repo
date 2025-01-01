@echo off
echo Installing Crypto Market App...

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please download and install Python 3.12 from:
    echo https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Create and activate virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

:: Upgrade pip and install wheel
echo Upgrading pip and installing wheel...
python -m pip install --upgrade pip wheel

:: Install the application
echo Installing Crypto Market App...
python -m pip install crypto_market_app-0.1.0-py3-none-any.whl

:: Run the application
echo Starting Crypto Market App...
crypto-market-app

:: Keep the window open if there's an error
if errorlevel 1 (
    echo.
    echo An error occurred. Please check the messages above.
    pause
)

:: Deactivate virtual environment
call venv\Scripts\deactivate.bat
