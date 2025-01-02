import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, mock_open
from telegram import Update, Chat, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import plotly.graph_objects as go
from datetime import datetime, timedelta

from .telegram_bot import CryptoMarketBot

@pytest.fixture
def mock_update():
    update = Mock(spec=Update)
    update.effective_chat = Mock(spec=Chat)
    update.effective_chat.id = 123456
    update.message = Mock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.callback_query = None  # Will be set in specific tests
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
    
    # Mock scraper response with correct data format
    mock_data = [
        {'name': 'Bitcoin', 'rank': 1, 'price': 50000.0, 'volume_percentage': 25.5},
        {'name': 'Ethereum', 'rank': 2, 'price': 3000.0, 'volume_percentage': 15.3}
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
        assert '$50,000.00' in message_text
        assert '25.5%' in message_text
        assert 'Ethereum' in message_text
        assert '$3,000.00' in message_text
        assert '15.3%' in message_text

@pytest.mark.asyncio
async def test_gettop10_command_success(bot, mock_update, mock_context):
    """Test successful execution of /gettop10 command"""
    # Mock scraper response
    mock_data = [
        {'name': 'Bitcoin', 'rank': 1, 'price': 50000.0, 'volume_percentage': 25.5},
        {'name': 'Ethereum', 'rank': 2, 'price': 3000.0, 'volume_percentage': 15.3},
        # Add more than 10 to verify slicing
        *[{'name': f'Coin{i}', 'rank': i+3, 'price': 100.0, 'volume_percentage': 5.0} 
          for i in range(15)]
    ]
    
    with patch.object(bot.scraper, 'get_top_cryptocurrencies', return_value=mock_data):
        await bot.gettop10_command(mock_update, mock_context)
        
        # Verify response was sent
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        
        # Check response formatting and content
        assert 'Top 10 Cryptocurrencies by Volume (Upbit)' in response
        assert 'Bitcoin' in response
        assert '$50,000.00' in response
        assert '25.5%' in response
        assert 'Ethereum' in response
        assert '$3,000.00' in response
        assert '15.3%' in response
        # Verify only top 10 are included
        assert 'Coin8' in response  # Should be included
        assert 'Coin12' not in response  # Should not be included

@pytest.mark.asyncio
async def test_gettop10_command_no_data(bot, mock_update, mock_context):
    """Test /gettop10 command when no data is available"""
    with patch.object(bot.scraper, 'get_top_cryptocurrencies', return_value=[]):
        await bot.gettop10_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once_with(
            "Unable to fetch cryptocurrency data at the moment. Please try again later."
        )

@pytest.mark.asyncio
async def test_gettop10_command_error(bot, mock_update, mock_context):
    """Test /gettop10 command error handling"""
    with patch.object(bot.scraper, 'get_top_cryptocurrencies', 
                     side_effect=Exception("Test error")):
        await bot.gettop10_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once_with(
            "Sorry, there was an error processing your request. Please try again later."
        )

@pytest.mark.asyncio
async def test_gettop10_command_with_charts(bot, mock_update, mock_context):
    """Test /gettop10 command with chart buttons"""
    mock_data = [
        {'name': 'Bitcoin', 'rank': 1, 'price': 50000.0, 'volume_percentage': 25.5},
        {'name': 'Ethereum', 'rank': 2, 'price': 3000.0, 'volume_percentage': 15.3}
    ]
    
    with patch.object(bot.scraper, 'get_top_cryptocurrencies', return_value=mock_data):
        await bot.gettop10_command(mock_update, mock_context)
        
        # Verify response includes chart buttons
        call_args = mock_update.message.reply_text.call_args
        reply_markup = call_args[1]['reply_markup']
        assert isinstance(reply_markup, InlineKeyboardMarkup)
        
        # Check button formatting
        buttons = reply_markup.inline_keyboard
        assert len(buttons) == 2  # One button per cryptocurrency
        assert "📈 Bitcoin Chart" in buttons[0][0].text
        assert "chart_Bitcoin" == buttons[0][0].callback_data
        assert "📈 Ethereum Chart" in buttons[1][0].text
        assert "chart_Ethereum" == buttons[1][0].callback_data

@pytest.mark.asyncio
async def test_chart_callback_success(bot, mock_update, mock_context):
    """Test successful chart generation callback"""
    # Create mock callback query
    query = Mock(spec=CallbackQuery)
    query.data = "chart_Bitcoin"
    query.message = Mock()
    query.message.chat_id = 123456
    query.answer = AsyncMock()
    mock_update.callback_query = query
    mock_context.bot.send_photo = AsyncMock()
    
    # Mock historical data
    mock_history = [
        {'timestamp': datetime.now() - timedelta(hours=i), 
         'volume_percentage': 10 + i} 
        for i in range(24)
    ]
    
    
    with patch.object(bot.db, 'get_crypto_history', return_value=mock_history), \
         patch('plotly.graph_objects.Figure.write_image'), \
         patch('builtins.open', mock_open()), \
         patch('os.unlink'):
        
        await bot.handle_chart_callback(mock_update, mock_context)
        
        # Verify chart was generated and sent
        assert mock_context.bot.send_photo.called
        caption = mock_context.bot.send_photo.call_args[1]['caption']
        assert "Bitcoin" in caption
        assert "24-hour trading volume trend" in caption
        assert query.answer.called

@pytest.mark.asyncio
async def test_chart_callback_no_data(bot, mock_update, mock_context):
    """Test chart callback when no historical data is available"""
    query = Mock(spec=CallbackQuery)
    query.data = "chart_Bitcoin"
    query.answer = AsyncMock()
    mock_update.callback_query = query
    
    with patch.object(bot.db, 'get_crypto_history', return_value=[]):
        await bot.handle_chart_callback(mock_update, mock_context)
        assert query.answer.called
        assert "No historical data available" in query.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_chart_callback_error(bot, mock_update, mock_context):
    """Test chart callback error handling"""
    query = Mock(spec=CallbackQuery)
    query.data = "chart_Bitcoin"
    query.answer = AsyncMock()
    mock_update.callback_query = query
    
    with patch.object(bot.db, 'get_crypto_history', side_effect=Exception("Test error")):
        await bot.handle_chart_callback(mock_update, mock_context)
        assert query.answer.called
        assert "Error generating chart" in query.answer.call_args[0][0]
