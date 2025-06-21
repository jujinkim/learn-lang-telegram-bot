import aiohttp
import json
from typing import Optional
from config import config

class LLMProvider:
    async def evaluate_translation(self, japanese: str, user_translation: str, correct_translation: str) -> str:
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    async def evaluate_translation(self, japanese: str, user_translation: str, correct_translation: str) -> str:
        prompt = f"""다음 일본어 번역을 평가해주세요:
일본어: {japanese}
사용자 번역: {user_translation}
정답 번역: {correct_translation}

0-100점으로 점수를 매기고, 한국어로 짧은 피드백을 제공해주세요.
형식: 점수: X점
피드백: (피드백 내용)"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "당신은 일본어 번역을 평가하는 선생님입니다."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 200
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        return "평가 중 오류가 발생했습니다."
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "평가 중 오류가 발생했습니다."

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
    
    async def evaluate_translation(self, japanese: str, user_translation: str, correct_translation: str) -> str:
        prompt = f"""다음 일본어 번역을 평가해주세요:
일본어: {japanese}
사용자 번역: {user_translation}
정답 번역: {correct_translation}

0-100점으로 점수를 매기고, 한국어로 짧은 피드백을 제공해주세요.
형식: 점수: X점
피드백: (피드백 내용)"""
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "claude-3-sonnet-20240229",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 200
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["content"][0]["text"]
                    else:
                        return "평가 중 오류가 발생했습니다."
        except Exception as e:
            print(f"Claude API error: {e}")
            return "평가 중 오류가 발생했습니다."

class LLMManager:
    def __init__(self):
        self.provider = self._create_provider()
    
    def _create_provider(self) -> Optional[LLMProvider]:
        if config.llm_provider == "openai":
            return OpenAIProvider(config.llm_api_key)
        elif config.llm_provider == "claude":
            return ClaudeProvider(config.llm_api_key)
        else:
            return None
    
    async def evaluate_translation(self, japanese: str, user_translation: str, correct_translation: str) -> str:
        if self.provider:
            return await self.provider.evaluate_translation(japanese, user_translation, correct_translation)
        return "LLM 제공자가 설정되지 않았습니다."

llm_manager = LLMManager()