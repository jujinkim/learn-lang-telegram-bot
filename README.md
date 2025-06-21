# Language Learning Telegram Bot

A Telegram bot that helps users practice language listening and translation with daily exercises. Currently supports Japanese with plans to add more languages.

## Features

- 🎌 Daily language practice at 9:00 AM (Asia/Seoul timezone)
- 🎧 Audio generation for language sentences (using gTTS)
- 📚 Level selection (Japanese: JLPT N1-N5)
- 💾 Personal wordbook for each user
- 🎯 Quiz mode with LLM-powered translation evaluation
- 🤖 Support for OpenAI and Claude LLMs

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the bot:
   - Copy `.env.example` to `.env` or `config.json.example` to `config.json`
   - Add your Telegram bot token
   - Add your LLM API key (OpenAI or Claude)
   - Set admin user IDs (optional)

3. Run the bot:
```bash
python main.py
```

## Configuration

The bot can be configured using either environment variables (.env file) or a config.json file:

- `BOT_TOKEN`: Your Telegram bot token from @BotFather
- `LLM_PROVIDER`: Either "openai" or "claude"
- `LLM_API_KEY`: Your API key for the chosen LLM provider
- `ADMIN_IDS`: Comma-separated list of admin user IDs (for /push command)
- `TIMEZONE`: Timezone for daily messages (default: Asia/Seoul)
- `DAILY_TIME`: Time for daily broadcast (default: 09:00)

## Commands

- `/start` - Initialize bot and select language level
- `/push` - (Admin only) Manually send daily practice

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