#!/bin/bash

# Set error handling
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Messages in Chinese
CN_MESSAGES=(
    "请使用root权限运行此脚本 (使用 sudo)"
    "正在创建目录..."
    "正在安装系统依赖..."
    "不支持的包管理器。请手动安装Python 3和pip。"
    "正在设置Python虚拟环境..."
    "正在复制项目文件..."
    "正在安装Python依赖..."
    "正在创建环境配置文件..."
    "正在创建系统服务..."
    "正在设置权限..."
    "正在启动服务..."
    "安装成功完成！"
    "常用命令："
    "- 查看服务状态："
    "- 查看日志："
    "- 重启服务："
    "- 停止服务："
)

# Function to print status messages
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
    echo -e "${GREEN}[✓]${NC} $2"  # Chinese message
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
    echo -e "${RED}[✗]${NC} $2"  # Chinese message
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    echo -e "${YELLOW}[!]${NC} $2"  # Chinese message
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)" "${CN_MESSAGES[0]}"
    exit 1
fi

# Installation directory
INSTALL_DIR="/opt/crypto_market_bot"
LOG_DIR="/var/log/crypto_market_bot"
DATA_DIR="${INSTALL_DIR}/data"
ENV_FILE="${INSTALL_DIR}/.env"

# Create necessary directories
print_status "Creating directories..." "${CN_MESSAGES[1]}"
mkdir -p "${INSTALL_DIR}" "${LOG_DIR}" "${DATA_DIR}"

# Install system dependencies
print_status "Installing system dependencies..." "${CN_MESSAGES[2]}"
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
elif command -v yum &> /dev/null; then
    yum update -y
    yum install -y python3 python3-pip
else
    print_error "Unsupported package manager. Please install Python 3 and pip manually." "${CN_MESSAGES[3]}"
    exit 1
fi

# Create and activate virtual environment
print_status "Setting up Python virtual environment..." "${CN_MESSAGES[4]}"
python3 -m venv "${INSTALL_DIR}/venv"
source "${INSTALL_DIR}/venv/bin/activate"

# Copy project files
print_status "Copying project files..." "${CN_MESSAGES[5]}"
cp -r ./src/* "${INSTALL_DIR}/"
cp requirements.txt "${INSTALL_DIR}/"

# Install Python dependencies
print_status "Installing Python dependencies..." "${CN_MESSAGES[6]}"
pip install -r "${INSTALL_DIR}/requirements.txt"

# Create environment file
print_status "Creating environment file..." "${CN_MESSAGES[7]}"
cat > "${ENV_FILE}" << EOL
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=7837117135:AAF9vMJAwqFUpRogMfkdOAHWaoxBr0Zx2TI

# Database Configuration
DB_PATH=${DATA_DIR}/market_data.db

# Scraping Configuration
SCRAPE_INTERVAL=300
CACHE_SIZE=20
DISPLAY_SIZE=10

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=${LOG_DIR}/bot.log

# Chart Configuration
CHART_HISTORY_HOURS=24
CHART_UPDATE_INTERVAL=300
EOL

# Create systemd service
print_status "Creating systemd service..." "${CN_MESSAGES[8]}"
cat > /etc/systemd/system/crypto_market_bot.service << EOL
[Unit]
Description=Crypto Market Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
Environment=PYTHONPATH=${INSTALL_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${INSTALL_DIR}/venv/bin/python3 -m main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Set correct permissions
print_status "Setting permissions..." "${CN_MESSAGES[9]}"
chmod 644 /etc/systemd/system/crypto_market_bot.service
chmod 600 "${ENV_FILE}"
chown -R root:root "${INSTALL_DIR}"
chmod -R 755 "${INSTALL_DIR}"

# Enable and start service
print_status "Starting service..." "${CN_MESSAGES[10]}"
systemctl daemon-reload
systemctl enable crypto_market_bot
systemctl start crypto_market_bot

# Print status information
print_status "Installation completed successfully!" "${CN_MESSAGES[11]}"
echo -e "\n${CN_MESSAGES[12]}"  # Useful commands in Chinese
echo "${CN_MESSAGES[13]} systemctl status crypto_market_bot"  # Check service status
echo "${CN_MESSAGES[14]} journalctl -u crypto_market_bot -f"  # View logs
echo "${CN_MESSAGES[15]} systemctl restart crypto_market_bot"  # Restart service
echo "${CN_MESSAGES[16]} systemctl stop crypto_market_bot"  # Stop service

# Print English commands for reference
echo -e "\nCommands in English:"
echo "- Check service status: systemctl status crypto_market_bot"
echo "- View logs: journalctl -u crypto_market_bot -f"
echo "- Restart service: systemctl restart crypto_market_bot"
echo "- Stop service: systemctl stop crypto_market_bot"
