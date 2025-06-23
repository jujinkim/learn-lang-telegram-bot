# Language Learning Telegram Bot

A Telegram bot that helps users practice language listening and translation with daily exercises. Currently supports Japanese with plans to add more languages.

## Features

- 🎌 Daily language practice at 9:00 AM (Asia/Seoul timezone)
- 🎧 Audio generation for language sentences (using gTTS)
- 📚 Level selection (Japanese: JLPT N1-N5)
- 💾 Personal wordbook for each user
- 🎯 Quiz mode with LLM-powered translation evaluation
- 🤖 Support for OpenAI, Claude, and Gemini LLMs

## Setup

1. **Create virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure the bot**:
   - Copy `config.json.example` to `config.json` and fill in your details, OR
   - Create a `.env` file with the following variables:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   LLM_PROVIDER=claude  # or openai, gemini
   LLM_API_KEY=your_llm_api_key_here
   ADMIN_IDS=your_telegram_user_id_here
   TIMEZONE=Asia/Seoul
   DAILY_TIME=09:00
   ```

4. **Get your bot's user ID** (optional, for reference):
```bash
# This will automatically add BOT_USER_ID to your .env file
python3 -c "
import asyncio
from telegram import Bot
from dotenv import load_dotenv, set_key
import os

async def get_bot_id():
    load_dotenv()
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    bot_info = await bot.get_me()
    print(f'Bot Username: @{bot_info.username}')
    print(f'Bot ID: {bot_info.id}')
    set_key('.env', 'BOT_USER_ID', str(bot_info.id))

asyncio.run(get_bot_id())
"
```

## Running the Bot

### **Quick Start (Foreground)**
```bash
source venv/bin/activate  # Activate virtual environment
python main.py
```

### **Run in Background (Recommended for Production)**

**Option 1: Using screen**
```bash
screen -S telegram-bot
source venv/bin/activate
python main.py
# Press Ctrl+A then D to detach from screen
# To reconnect: screen -r telegram-bot
```

**Option 2: Using nohup**
```bash
source venv/bin/activate
nohup python main.py > bot.log 2>&1 &
# Check if running: ps aux | grep main.py
# View logs: tail -f bot.log
# Stop: pkill -f main.py
```

**Option 3: Using systemd (Linux)**
```bash
# Create service file
sudo nano /etc/systemd/system/telegram-bot.service

# Add this content (adjust paths):
[Unit]
Description=Language Learning Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/learn-lang-telegram-bot
Environment=PATH=/path/to/learn-lang-telegram-bot/venv/bin
ExecStart=/path/to/learn-lang-telegram-bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

## Configuration

The bot can be configured using either environment variables (.env file) or a config.json file:

- `BOT_TOKEN`: Your Telegram bot token from @BotFather
- `LLM_PROVIDER`: Either "openai", "claude", or "gemini"
- `LLM_API_KEY`: Your API key for the chosen LLM provider
- `ADMIN_IDS`: Your Telegram user ID (allows you to use /push command to manually trigger practice)
- `TIMEZONE`: Timezone for daily messages (default: Asia/Seoul)
- `DAILY_TIME`: Time for daily broadcast (default: 09:00)

## Using the Bot

Once the bot is running, you can interact with it on Telegram:

1. **Find your bot**: Search for `@your_bot_username` on Telegram
2. **Start chatting**: Send `/start` to begin
3. **Select level**: Choose your Japanese proficiency level (N5-N1)
4. **Daily practice**: Receive automatic practice at 9:00 AM
5. **Interactive learning**: Use buttons to:
   - 🇯🇵 **일본어 보기** - View Japanese text
   - 🇰🇷 **한국어 뜻 보기** - View Korean translation
   - 🔁 **다시 듣기** - Replay audio
   - 📝 **단어장에 저장** - Save to wordbook
   - 🎯 **퀴즈 모드** - Test translation skills
   - ⚙️ **레벨 변경** - Change difficulty level

## Commands

- `/start` - Initialize bot and select language level
- `/push` - Manually trigger daily practice (admin only - requires your user ID in ADMIN_IDS)

## Troubleshooting

**Bot not responding?**
- Check if the bot process is running: `ps aux | grep main.py`
- Check logs: `tail -f bot.log` (if using nohup)
- Restart the bot if needed

**Getting API errors?**
- Verify your bot token and LLM API key are correct
- Check your internet connection
- Ensure your LLM provider has sufficient credits

**Daily messages not working?**
- Check timezone settings in your config
- Verify the scheduler is running (check logs for "Scheduler started")
- Test manually with `/push` command (as admin)

## Project Structure

- `main.py` - Bot initialization and scheduler
- `handlers.py` - Command and callback handlers
- `config.py` - Configuration management
- `utils.py` - Data management and audio generation
- `llm.py` - LLM integration for translation evaluation
- `data.json` - Language conversation database (currently Japanese)

## Data Format

Conversations are stored in `data.json` with the following structure:
```json
{
  "id": 1,
  "level": "N4",
  "jp": "ご注文はお決まりですか？",
  "kr": "주문은 정하셨나요？"
}
```

## Supported Languages

- 🇯🇵 Japanese (JLPT N1-N5 levels)
- 🌐 More languages coming soon...

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.