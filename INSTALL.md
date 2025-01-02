# Installation Instructions

## Prerequisites
- Python 3.8 or higher
- systemd (standard on most Linux distributions)
- Git

## Setup Steps

1. Clone the repository:
```bash
git clone https://github.com/vaynewilltom/my-first-repo.git
cd my-first-repo
```

2. Install Python dependencies:
```bash
pip3 install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root:
```bash
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > .env
```
Replace `your_bot_token_here` with your actual Telegram bot token.

4. Install the systemd service:
```bash
# Copy service file to systemd directory
sudo cp crypto_market_bot.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable crypto_market_bot

# Start the service
sudo systemctl start crypto_market_bot
```

## Service Management

- Check service status:
```bash
sudo systemctl status crypto_market_bot
```

- View logs:
```bash
# View service logs
sudo journalctl -u crypto_market_bot

# View application logs
tail -f /var/log/crypto_market_bot/crypto_market_bot.log
```

- Stop the service:
```bash
sudo systemctl stop crypto_market_bot
```

- Restart the service:
```bash
sudo systemctl restart crypto_market_bot
```

## Troubleshooting

1. If the service fails to start, check the logs:
```bash
sudo journalctl -u crypto_market_bot -n 50 --no-pager
```

2. Ensure proper permissions:
```bash
# Set correct ownership for the log directory
sudo chown -R ubuntu:ubuntu /var/log/crypto_market_bot

# Set correct permissions for the .env file
chmod 600 .env
```

3. Verify the bot token:
```bash
# Check if the .env file contains the token
grep TELEGRAM_BOT_TOKEN .env
```
