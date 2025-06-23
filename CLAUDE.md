# Learn Lang Telegram Bot Project

## Overview
A multi-language learning Telegram bot built with Python.

## Project Structure
- `main.py` - Main bot application entry point
- `handlers.py` - Telegram message handlers
- `llm.py` - Language model integration
- `utils.py` - Utility functions
- `config.py` - Configuration management
- `data.json` - Application data storage
- `requirements.txt` - Python dependencies

## Development Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `config.json.example` to `config.json` and configure
3. Run the bot: `python main.py`

## Testing
Run tests with: `python -m pytest` (if tests exist)

## Code Quality
- Linting: `python -m pylint *.py` or `python -m flake8`
- Type checking: `python -m mypy .`