# Building Crypto Market App for Windows 11

## Prerequisites
1. Install Python 3.12.x from [Python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Check "Install for all users"

## Setup Steps
1. Extract the project files to a folder (e.g., `C:\crypto_market_app`)
2. Open Command Prompt as Administrator
3. Navigate to the project directory:
   ```cmd
   cd C:\crypto_market_app
   ```
4. Create and activate a virtual environment:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```
5. Install required packages:
   ```cmd
   pip install -r requirements.txt
   pip install pyinstaller
   ```

## Build Steps
1. With the virtual environment active, run:
   ```cmd
   pyinstaller --name crypto_market_app --onefile --windowed --add-data "src;src" src/main.py
   ```
2. The executable will be created in the `dist` folder
3. Copy the executable to your desired location

## Verification
1. Double-click `crypto_market_app.exe` in the `dist` folder
2. Verify that:
   - The application window opens
   - Cryptocurrency data is displayed
   - Charts can be viewed by clicking on cryptocurrencies
   - Data refreshes every 5 minutes

## Troubleshooting
If you encounter any issues:
1. Ensure all prerequisites are installed
2. Check that Python is in your system PATH
3. Verify all dependencies are installed correctly
4. Try running the script directly with Python first:
   ```cmd
   python src/main.py
   ```

For additional support, please report any issues with detailed error messages.
