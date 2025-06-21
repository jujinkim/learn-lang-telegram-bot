import json
import os
import random
from typing import List, Dict, Optional
from gtts import gTTS
import aiofiles
import aiohttp
from datetime import datetime

DATA_FILE = "data.json"
WORDBOOK_DIR = "wordbooks"
AUDIO_DIR = "audio_cache"

os.makedirs(WORDBOOK_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

class DataManager:
    def __init__(self):
        self.conversations = self._load_conversations()
    
    def _load_conversations(self) -> List[Dict]:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_conversation_by_level(self, level: str) -> Optional[Dict]:
        level_conversations = [c for c in self.conversations if c["level"] == level]
        if level_conversations:
            return random.choice(level_conversations)
        return None
    
    def get_conversation_by_id(self, conv_id: int) -> Optional[Dict]:
        for conv in self.conversations:
            if conv["id"] == conv_id:
                return conv
        return None

class WordbookManager:
    @staticmethod
    async def load_wordbook(user_id: int) -> List[Dict]:
        filepath = os.path.join(WORDBOOK_DIR, f"{user_id}.json")
        if os.path.exists(filepath):
            async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content)
        return []
    
    @staticmethod
    async def save_to_wordbook(user_id: int, conversation: Dict):
        wordbook = await WordbookManager.load_wordbook(user_id)
        
        entry = {
            "id": conversation["id"],
            "level": conversation["level"],
            "jp": conversation["jp"],
            "kr": conversation["kr"],
            "saved_at": datetime.now().isoformat()
        }
        
        if not any(item["id"] == conversation["id"] for item in wordbook):
            wordbook.append(entry)
            
            filepath = os.path.join(WORDBOOK_DIR, f"{user_id}.json")
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(wordbook, ensure_ascii=False, indent=2))
            return True
        return False
    
    @staticmethod
    async def remove_from_wordbook(user_id: int, conv_id: int) -> bool:
        wordbook = await WordbookManager.load_wordbook(user_id)
        original_length = len(wordbook)
        wordbook = [item for item in wordbook if item["id"] != conv_id]
        
        if len(wordbook) < original_length:
            filepath = os.path.join(WORDBOOK_DIR, f"{user_id}.json")
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(wordbook, ensure_ascii=False, indent=2))
            return True
        return False

class AudioGenerator:
    @staticmethod
    async def generate_audio(text: str, conv_id: int) -> str:
        audio_file = os.path.join(AUDIO_DIR, f"conv_{conv_id}.mp3")
        
        if os.path.exists(audio_file):
            return audio_file
        
        try:
            tts = gTTS(text=text, lang='ja', slow=False)
            tts.save(audio_file)
            return audio_file
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None

class UserDataManager:
    @staticmethod
    def get_user_level(context) -> str:
        return context.user_data.get("level", "N3")
    
    @staticmethod
    def set_user_level(context, level: str):
        context.user_data["level"] = level
    
    @staticmethod
    def get_quiz_data(context) -> Optional[Dict]:
        return context.user_data.get("quiz_data")
    
    @staticmethod
    def set_quiz_data(context, conversation: Dict):
        context.user_data["quiz_data"] = conversation
    
    @staticmethod
    def clear_quiz_data(context):
        if "quiz_data" in context.user_data:
            del context.user_data["quiz_data"]
    
    @staticmethod
    def get_daily_conversation(context) -> Optional[Dict]:
        return context.user_data.get("daily_conversation")
    
    @staticmethod
    def set_daily_conversation(context, conversation: Dict):
        context.user_data["daily_conversation"] = conversation

data_manager = DataManager()
wordbook_manager = WordbookManager()
audio_generator = AudioGenerator()
user_data_manager = UserDataManager()