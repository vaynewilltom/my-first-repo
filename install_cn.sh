#!/bin/bash

# 加密货币市场机器人安装脚本
# Cryptocurrency Market Bot Installation Script

# 设置错误时退出
set -e

echo "开始安装加密货币市场机器人..."
echo "Starting Cryptocurrency Market Bot installation..."

# 检查Python版本
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "未找到Python3，正在安装..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# 创建必要的目录
echo "创建数据和日志目录..."
mkdir -p ~/.crypto_market_bot/data
mkdir -p ~/.crypto_market_bot/logs

# 创建虚拟环境
echo "创建Python虚拟环境..."
python3 -m venv ~/.crypto_market_bot/venv
source ~/.crypto_market_bot/venv/bin/activate

# 安装依赖
echo "安装项目依赖..."
pip install -r requirements.txt

# 复制配置文件
echo "设置环境配置..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "请编辑 .env 文件并设置您的Telegram机器人令牌"
fi

# 设置系统服务
echo "配置系统服务..."
sudo tee /etc/systemd/system/crypto-market-bot@.service > /dev/null << EOL
[Unit]
Description=Crypto Market Telegram Bot
After=network.target

[Service]
Type=simple
User=%i
WorkingDirectory=%h/crypto_market_bot
Environment=PYTHONPATH=%h/crypto_market_bot
ExecStart=%h/.crypto_market_bot/venv/bin/python -m crypto_market_bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# 重新加载systemd配置
echo "重新加载系统服务配置..."
sudo systemctl daemon-reload

echo "安装完成！"
echo ""
echo "使用说明："
echo "1. 编辑 .env 文件设置您的Telegram机器人令牌"
echo "2. 启动服务：sudo systemctl start crypto-market-bot@$USER"
echo "3. 停止服务：sudo systemctl stop crypto-market-bot@$USER"
echo "4. 查看状态：sudo systemctl status crypto-market-bot@$USER"
echo "5. 查看日志：journalctl -u crypto-market-bot@$USER"
echo ""
echo "机器人命令："
echo "/gettop10 - 显示交易量前10的加密货币"
echo "/status - 显示机器人运行状态"
echo "/start - 开始接收更新"
echo "/stop - 停止接收更新"
