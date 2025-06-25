import os
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.bot_token: str = ""
        self.llm_provider: str = "gemini"
        self.llm_api_key: str = ""
        self.admin_ids: list[int] = []
        self.timezone: str = "Asia/Seoul"
        self.daily_time: str = "09:00"
        
        self._load_config()
    
    def _load_config(self):
        config_file = "config.json"
        
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                self.bot_token = config_data.get("BOT_TOKEN", os.getenv("BOT_TOKEN", ""))
                self.llm_provider = config_data.get("LLM_PROVIDER", os.getenv("LLM_PROVIDER", "gemini"))
                self.llm_api_key = config_data.get("LLM_API_KEY", os.getenv("LLM_API_KEY", ""))
                self.admin_ids = config_data.get("ADMIN_IDS", [])
                self.timezone = config_data.get("TIMEZONE", "Asia/Seoul")
                self.daily_time = config_data.get("DAILY_TIME", "09:00")
        else:
            self.bot_token = os.getenv("BOT_TOKEN", "")
            self.llm_provider = os.getenv("LLM_PROVIDER", "gemini")
            self.llm_api_key = os.getenv("LLM_API_KEY", "")
            admin_ids_str = os.getenv("ADMIN_IDS", "")
            self.admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
            self.timezone = os.getenv("TIMEZONE", "Asia/Seoul")
            self.daily_time = os.getenv("DAILY_TIME", "09:00")
    
    def validate(self) -> tuple[bool, Optional[str]]:
        if not self.bot_token:
            return False, "BOT_TOKEN is required"
        if not self.llm_api_key:
            return False, "LLM_API_KEY is required"
        if self.llm_provider not in ["openai", "claude", "gemini"]:
            return False, f"Unsupported LLM_PROVIDER: {self.llm_provider}"
        return True, None

config = Config()