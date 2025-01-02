import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from telegram import Update, Chat, Message
from telegram.ext import ContextTypes

from .telegram_bot import CryptoMarketBot

@pytest.fixture
def mock_update():
    update = Mock(spec=Update)
    update.effective_chat = Mock(spec=Chat)
    update.effective_chat.id = 123456
    update.message = Mock(spec=Message)
    return update

@pytest.fixture
def mock_context():
    return Mock(spec=ContextTypes.DEFAULT_TYPE)

@pytest.fixture
def bot():
    with patch('telegram.ext.Application.builder') as mock_builder:
        mock_app = AsyncMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        return CryptoMarketBot()

@pytest.mark.asyncio
async def test_start_command(bot, mock_update, mock_context):
    """Test /start command functionality"""
    # Test initial start
    await bot.start_command(mock_update, mock_context)
    assert mock_update.effective_chat.id in bot.active_chats
    assert mock_update.message.reply_text.called
    first_call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Welcome to the Crypto Market Bot!" in first_call_args
    
    # Test starting when already active
    mock_update.message.reply_text.reset_mock()
    await bot.start_command(mock_update, mock_context)
    second_call_args = mock_update.message.reply_text.call_args[0][0]
    assert "already receiving updates" in second_call_args

@pytest.mark.asyncio
async def test_stop_command(bot, mock_update, mock_context):
    """Test /stop command functionality"""
    # Add chat to active_chats
    bot.active_chats.add(mock_update.effective_chat.id)
    
    # Test stopping active updates
    await bot.stop_command(mock_update, mock_context)
    assert mock_update.effective_chat.id not in bot.active_chats
    assert mock_update.message.reply_text.called
    first_call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Updates stopped" in first_call_args
    
    # Test stopping when already stopped
    mock_update.message.reply_text.reset_mock()
    await bot.stop_command(mock_update, mock_context)
    second_call_args = mock_update.message.reply_text.call_args[0][0]
    assert "not currently receiving updates" in second_call_args

@pytest.mark.asyncio
async def test_status_command(bot, mock_update, mock_context):
    """Test /status command functionality"""
    # Test status when inactive
    await bot.status_command(mock_update, mock_context)
    first_call_args = mock_update.message.reply_text.call_args[0][0]
    assert "inactive" in first_call_args
    assert "Total active users: 0" in first_call_args
    
    # Test status when active
    bot.active_chats.add(mock_update.effective_chat.id)
    mock_update.message.reply_text.reset_mock()
    await bot.status_command(mock_update, mock_context)
    second_call_args = mock_update.message.reply_text.call_args[0][0]
    assert "active" in second_call_args
    assert "Total active users: 1" in second_call_args

@pytest.mark.asyncio
async def test_send_updates(bot, mock_update):
    """Test update sending functionality"""
    bot.active_chats.add(mock_update.effective_chat.id)
    
    # Mock scraper response
    mock_data = [
        {'name': 'Bitcoin', 'price': '$50,000', 'volume': '100M'},
        {'name': 'Ethereum', 'price': '$3,000', 'volume': '50M'}
    ]
    
    with patch.object(bot.scraper, 'get_top_cryptocurrencies', return_value=mock_data):
        # Create a task that runs for a short time
        task = asyncio.create_task(bot.send_updates())
        await asyncio.sleep(0.1)  # Let it run briefly
        task.cancel()  # Cancel the infinite loop
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify that the bot attempted to send messages
        assert bot.application.bot.send_message.called
        message_text = bot.application.bot.send_message.call_args[1]['text']
        assert 'Bitcoin' in message_text
        assert 'Ethereum' in message_text
