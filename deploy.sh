#!/bin/bash
set -e

# Configuration
DEPLOY_DIR="/opt/crypto_market_bot"
VENV_DIR="$DEPLOY_DIR/venv"
DATA_DIR="$DEPLOY_DIR/data"
LOG_DIR="/var/log/crypto_market_bot"
SERVICE_NAME="crypto_market_bot"
PROJECT_DIR="$(pwd)"

# Create deployment directories
echo "Creating deployment directories..."
sudo mkdir -p $DEPLOY_DIR $DATA_DIR $LOG_DIR
sudo chown -R $USER:$USER $DEPLOY_DIR $LOG_DIR

# Set directory permissions
sudo chmod 755 $DEPLOY_DIR
sudo chmod 700 $DATA_DIR $LOG_DIR

# Set up Python virtual environment
echo "Setting up virtual environment..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Function to detect package manager
detect_package_manager() {
    if command -v dnf >/dev/null 2>&1; then
        echo "dnf"
    elif command -v yum >/dev/null 2>&1; then
        echo "yum"
    elif command -v apt-get >/dev/null 2>&1; then
        echo "apt-get"
    else
        echo "Unknown package manager" >&2
        exit 1
    fi
}

# Install system dependencies
echo "Installing system dependencies..."
PKG_MGR=$(detect_package_manager)
echo "Using package manager: $PKG_MGR"

case $PKG_MGR in
    "dnf"|"yum")
        sudo $PKG_MGR update -y
        sudo $PKG_MGR install -y python3-devel python3-pip python3-virtualenv gcc make
        ;;
    "apt-get")
        sudo $PKG_MGR update
        sudo $PKG_MGR install -y python3-pip python3-venv python3-dev build-essential
        ;;
    *)
        echo "Unsupported package manager" >&2
        exit 1
        ;;
esac

# Copy project files
echo "Copying project files..."
cp -r $PROJECT_DIR/* $DEPLOY_DIR/

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir -r $DEPLOY_DIR/requirements.txt

# Create environment file
echo "Setting up environment variables..."
cat > $DEPLOY_DIR/.env << EOL
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
PYTHONPATH=$DEPLOY_DIR
DB_PATH=$DATA_DIR/market_data.db
LOG_LEVEL=INFO
LOG_FILE=$LOG_DIR/bot.log
SCRAPE_INTERVAL=300
CACHE_SIZE=20
DISPLAY_SIZE=10
CHART_HISTORY_HOURS=24
CHART_UPDATE_INTERVAL=300
EOL

# Set environment file permissions
chmod 600 $DEPLOY_DIR/.env

# Set up systemd service
echo "Configuring systemd service..."
sudo cp $DEPLOY_DIR/crypto_market_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "Deployment completed successfully!"
echo "Check status with: sudo systemctl status $SERVICE_NAME"
echo "View logs with: sudo journalctl -u $SERVICE_NAME -f"
echo "Database location: $DATA_DIR/market_data.db"
echo "Log file location: $LOG_DIR/bot.log"
