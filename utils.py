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
        self.realtime_generation = True  # Enable aggressive real-time generation
    
    def _load_conversations(self) -> List[Dict]:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("conversations", [])
        except FileNotFoundError:
            return []
    
    def load_data(self):
        """Reload conversations from file"""
        self.conversations = self._load_conversations()
    
    async def get_conversation_by_level(self, level: str) -> Optional[Dict]:
        """Aggressive real-time generation to avoid repetition"""
        
        # Check stored conversation count for this level
        level_conversations = [c for c in self.conversations if c.get("level") == level]
        stored_count = len(level_conversations)
        
        # Aggressive real-time generation logic:
        # - Always try real-time if < 10 stored conversations for this level
        # - 80% chance for real-time even with stored conversations (to avoid repetition)
        should_generate_realtime = (
            self.realtime_generation and 
            (stored_count < 10 or random.random() < 0.8)
        )
        
        # Try real-time generation first
        if should_generate_realtime:
            try:
                from llm import llm_manager
                
                # Check if LLM manager is properly configured
                if not llm_manager.provider:
                    print(f"⚠️ LLM provider not configured, falling back to stored conversations")
                    self.realtime_generation = False  # Disable to avoid repeated failures
                else:
                    # Generate a single fresh conversation
                    themes = ["daily_life", "restaurant", "business", "travel", "shopping", "emergency", "education", "work"]
                    theme = random.choice(themes)
                    
                    print(f"🔄 Generating real-time conversation: {level} {theme}")
                    conversations = await llm_manager.generate_conversations(level, theme, 1)
                    
                    if conversations and len(conversations) > 0:
                        conv = conversations[0]
                        # Add temporary ID and level
                        conv["id"] = random.randint(100000, 999999)  # Temp ID for real-time
                        conv["level"] = level
                        conv["is_realtime"] = True
                        
                        print(f"✅ Real-time generation successful")
                        
                        # Optionally save to database for future use
                        await self._save_generated_conversation(conv)
                        
                        return conv
                    else:
                        print(f"❌ Real-time generation failed: empty response, falling back to stored")
                    
            except Exception as e:
                print(f"⚠️ Real-time generation error: {type(e).__name__}: {e}, falling back to stored")
        
        # Fallback to stored conversations (level_conversations already calculated above)
        if level_conversations:
            conv = random.choice(level_conversations).copy()  # Copy to avoid modifying original
            conv["is_realtime"] = False
            print(f"📚 Using stored conversation ID {conv['id']} (stored_count: {stored_count})")
            return conv
            
        print(f"❌ {level} 레벨에 사용 가능한 대화가 없습니다")
        return None
    
    async def _save_generated_conversation(self, conversation: Dict):
        """Optionally save generated conversations to build database"""
        try:
            # Remove temporary fields
            conv_to_save = conversation.copy()
            conv_to_save.pop("is_realtime", None)
            
            # Generate proper ID
            max_id = max([c.get("id", 0) for c in self.conversations]) if self.conversations else 0
            conv_to_save["id"] = max_id + 1
            
            # Add to memory
            self.conversations.append(conv_to_save)
            
            # Save to file
            data = {"conversations": self.conversations}
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"💾 Saved conversation to database (ID: {conv_to_save['id']})")
        except Exception as e:
            print(f"⚠️ Failed to save conversation: {e}")
    
    def get_conversation_by_id(self, conv_id: int) -> Optional[Dict]:
        for conv in self.conversations:
            if conv["id"] == conv_id:
                return conv
        return None
    
    def toggle_realtime_generation(self, enabled: bool = None):
        """Toggle or set real-time generation mode"""
        if enabled is None:
            self.realtime_generation = not self.realtime_generation
        else:
            self.realtime_generation = enabled
        return self.realtime_generation

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
        try:
            print(f"💾 Attempting to save conversation to wordbook for user {user_id}")
            print(f"💾 Conversation data: {conversation}")
            
            # Ensure wordbook directory exists
            os.makedirs(WORDBOOK_DIR, exist_ok=True)
            
            wordbook = await WordbookManager.load_wordbook(user_id)
            print(f"💾 Current wordbook has {len(wordbook)} items")
            
            entry = {
                "id": conversation["id"],
                "level": conversation["level"],
                "jp": conversation["jp"],
                "kr": conversation["kr"],
                "saved_at": datetime.now().isoformat()
            }
            
            # Check for duplicate based on ID
            existing_item = any(item["id"] == conversation["id"] for item in wordbook)
            if existing_item:
                print(f"💾 Item with ID {conversation['id']} already exists in wordbook")
                return False
            
            # Add new entry
            wordbook.append(entry)
            print(f"💾 Added new entry, wordbook now has {len(wordbook)} items")
            
            # Save to file
            filepath = os.path.join(WORDBOOK_DIR, f"{user_id}.json")
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(wordbook, ensure_ascii=False, indent=2))
            
            print(f"✅ Successfully saved to wordbook: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving to wordbook for user {user_id}: {type(e).__name__}: {e}")
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
        quiz_data = conversation.copy()
        quiz_data["quiz_start_time"] = datetime.now().isoformat()
        context.user_data["quiz_data"] = quiz_data
    
    @staticmethod
    def clear_quiz_data(context):
        if "quiz_data" in context.user_data:
            del context.user_data["quiz_data"]
    
    @staticmethod
    def get_daily_conversation(context) -> Optional[Dict]:
        return context.user_data.get("daily_conversation")
    
    @staticmethod
    def set_daily_conversation(context, conversation: Dict):
        if context is not None:
            context.user_data["daily_conversation"] = conversation

data_manager = DataManager()
wordbook_manager = WordbookManager()
audio_generator = AudioGenerator()
user_data_manager = UserDataManager()