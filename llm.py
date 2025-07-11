import aiohttp
import json
from typing import Optional
from config import config
import google.generativeai as genai
import re

def is_hiragana_only(text: str) -> bool:
    """Check if text contains only hiragana, spaces, and common punctuation"""
    # Allow hiragana (ぁ-ん), katakana (ァ-ヶ), spaces, and common Japanese punctuation
    allowed_pattern = r'^[\u3040-\u309F\u30A0-\u30FF\s\u3000、。！？～ー]+$'
    return bool(re.match(allowed_pattern, text))

class LLMProvider:
    async def evaluate_translation(self, source_text: str, user_translation: str, correct_translation: str, source_lang: str = "일본어") -> str:
        raise NotImplementedError
    
    async def generate_conversations(self, level: str, theme: str, count: int = 10) -> list:
        raise NotImplementedError
    
    async def generate_furigana(self, japanese_text: str) -> str:
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    async def evaluate_translation(self, source_text: str, user_translation: str, correct_translation: str, source_lang: str = "일본어") -> str:
        prompt = f"""Evaluate this translation:
Source ({source_lang}): {source_text}
User translation: {user_translation}
Correct translation: {correct_translation}

Scoring:
- Correct meaning, different style: 4-5 stars, feedback "좋아요" or "맞아요"
- Correct but unnatural: 3 stars
- Partially correct: 1-2 stars

Format:
Stars: ⭐⭐⭐⭐⭐ (1-5)
Feedback: 1-2 Korean words only (e.g. "좋아요", "맞아요", "어색함", "틀림", "애매함")"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "당신은 언어 번역을 평가하는 선생님입니다."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 150
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
    
    async def generate_conversations(self, level: str, theme: str, count: int = 10) -> list:
        level_descriptions = {
            "N5": "가장 기본적인 일본어 (기본 인사, 숫자, 간단한 질문)",
            "N4": "초급 일본어 (일상 대화, 서비스 상황, 간단한 요청)",
            "N3": "중급 일본어 (정중한 표현, 비즈니스 기초, 복잡한 문장)",
            "N2": "상급 일본어 (정식 비즈니스 표현, 복잡한 경어)",
            "N1": "최고급 일본어 (고급 경어, 공식적인 표현, 복잡한 문법)"
        }
        
        theme_descriptions = {
            "daily_life": "일상생활 (인사, 식사, 쇼핑, 교통)",
            "restaurant": "식당 (주문, 예약, 계산, 서비스)",
            "business": "비즈니스 (회의, 이메일, 전화, 프레젠테이션)",
            "travel": "여행 (호텔, 공항, 관광, 길 찾기)",
            "shopping": "쇼핑 (가격 문의, 교환/환불, 결제)",
            "emergency": "응급상황 (병원, 경찰, 도움 요청)",
            "education": "교육 (학교, 수업, 시험, 학습)",
            "work": "직장 (면접, 업무, 동료, 상사)"
        }
        
        prompt = f"""일본어-한국어 학습용 대화 쌍을 {count}개 생성해주세요.

조건:
- JLPT {level} 수준: {level_descriptions.get(level, '')}
- 주제: {theme} - {theme_descriptions.get(theme, theme)}
- 각 대화는 일본어 문장과 자연스러운 한국어 번역으로 구성
- 실제 대화에서 자주 사용되는 실용적인 표현
- 문법과 어휘가 {level} 수준에 적합해야 함

출력 형식 (JSON):
[
  {{"jp": "일본어 문장", "kr": "한국어 번역"}}
]

{count}개의 서로 다른 대화를 생성해주세요."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "당신은 일본어 교육 전문가입니다. JLPT 수준에 맞는 정확한 일본어-한국어 대화 쌍을 생성합니다."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        
                        # Extract JSON from the response
                        import re
                        json_match = re.search(r'\[.*\]', content, re.DOTALL)
                        if json_match:
                            conversations = json.loads(json_match.group())
                            return conversations
                        else:
                            print("Failed to extract JSON from OpenAI response")
                            return []
                    else:
                        print(f"OpenAI API error: {response.status}")
                        return []
        except Exception as e:
            print(f"OpenAI conversation generation error: {e}")
            return []
    
    async def generate_furigana(self, japanese_text: str) -> str:
        prompt = f"""Convert this Japanese text to hiragana reading (furigana):

Japanese: {japanese_text}

Rules:
- Convert ALL kanji to hiragana
- Keep existing hiragana as-is
- Add spaces between words for readability
- Separate particles (は, を, に, で, etc.) with spaces
- Output ONLY the hiragana reading, nothing else

Examples:
Input: 今日は良い天気ですね
Output: きょう は よい てんき です ね

Input: 私は学校に行きます
Output: わたし は がっこう に いき ます

Hiragana reading:"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "당신은 일본어 후리가나 생성 전문가입니다. 정확한 히라가나 읽기를 제공합니다."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 300
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"].strip()
                        # Extract just the hiragana line
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and is_hiragana_only(line):
                                return line
                        # If no pure hiragana line found, return empty string
                        return ""
                    else:
                        return ""
        except Exception as e:
            print(f"OpenAI furigana error: {e}")
            return ""

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
    
    async def evaluate_translation(self, source_text: str, user_translation: str, correct_translation: str, source_lang: str = "일본어") -> str:
        prompt = f"""Evaluate this translation:
Source ({source_lang}): {source_text}
User translation: {user_translation}
Correct translation: {correct_translation}

Scoring:
- Correct meaning, different style: 4-5 stars, feedback "좋아요" or "맞아요"
- Correct but unnatural: 3 stars
- Partially correct: 1-2 stars

Format:
Stars: ⭐⭐⭐⭐⭐ (1-5)
Feedback: 1-2 Korean words only (e.g. "좋아요", "맞아요", "어색함", "틀림", "애매함")"""
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "claude-3-5-haiku-20241022",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 150
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
    
    async def generate_conversations(self, level: str, theme: str, count: int = 10) -> list:
        level_descriptions = {
            "N5": "가장 기본적인 일본어 (기본 인사, 숫자, 간단한 질문)",
            "N4": "초급 일본어 (일상 대화, 서비스 상황, 간단한 요청)",
            "N3": "중급 일본어 (정중한 표현, 비즈니스 기초, 복잡한 문장)",
            "N2": "상급 일본어 (정식 비즈니스 표현, 복잡한 경어)",
            "N1": "최고급 일본어 (고급 경어, 공식적인 표현, 복잡한 문법)"
        }
        
        theme_descriptions = {
            "daily_life": "일상생활 (인사, 식사, 쇼핑, 교통)",
            "restaurant": "식당 (주문, 예약, 계산, 서비스)",
            "business": "비즈니스 (회의, 이메일, 전화, 프레젠테이션)",
            "travel": "여행 (호텔, 공항, 관광, 길 찾기)",
            "shopping": "쇼핑 (가격 문의, 교환/환불, 결제)",
            "emergency": "응급상황 (병원, 경찰, 도움 요청)",
            "education": "교육 (학교, 수업, 시험, 학습)",
            "work": "직장 (면접, 업무, 동료, 상사)"
        }
        
        prompt = f"""일본어-한국어 학습용 대화 쌍을 {count}개 생성해주세요.

조건:
- JLPT {level} 수준: {level_descriptions.get(level, '')}
- 주제: {theme} - {theme_descriptions.get(theme, theme)}
- 각 대화는 일본어 문장과 자연스러운 한국어 번역으로 구성
- 실제 대화에서 자주 사용되는 실용적인 표현
- 문법과 어휘가 {level} 수준에 적합해야 함

출력 형식 (JSON):
[
  {{"jp": "일본어 문장", "kr": "한국어 번역"}}
]

{count}개의 서로 다른 대화를 생성해주세요."""

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "claude-3-5-haiku-20241022",
            "messages": [
                {
                    "role": "user",
                    "content": f"당신은 일본어 교육 전문가입니다. JLPT 수준에 맞는 정확한 일본어-한국어 대화 쌍을 생성합니다.\n\n{prompt}"
                }
            ],
            "max_tokens": 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["content"][0]["text"]
                        
                        # Extract JSON from the response
                        import re
                        json_match = re.search(r'\[.*\]', content, re.DOTALL)
                        if json_match:
                            conversations = json.loads(json_match.group())
                            return conversations
                        else:
                            print("Failed to extract JSON from Claude response")
                            return []
                    else:
                        print(f"Claude API error: {response.status}")
                        return []
        except Exception as e:
            print(f"Claude conversation generation error: {e}")
            return []
    
    async def generate_furigana(self, japanese_text: str) -> str:
        prompt = f"""Convert this Japanese text to hiragana reading (furigana):

Japanese: {japanese_text}

Rules:
- Convert ALL kanji to hiragana
- Keep existing hiragana as-is
- Add spaces between words for readability
- Separate particles (は, を, に, で, etc.) with spaces
- Output ONLY the hiragana reading, nothing else

Examples:
Input: 今日は良い天気ですね
Output: きょう は よい てんき です ね

Input: 私は学校に行きます
Output: わたし は がっこう に いき ます

Hiragana reading:"""
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "claude-3-5-haiku-20241022",
            "messages": [
                {
                    "role": "user",
                    "content": f"당신은 일본어 후리가나 생성 전문가입니다. 정확한 히라가나 읽기를 제공합니다.\n\n{prompt}"
                }
            ],
            "max_tokens": 300
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["content"][0]["text"].strip()
                        # Extract just the hiragana line
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and is_hiragana_only(line):
                                return line
                        # If no pure hiragana line found, return empty string
                        return ""
                    else:
                        return ""
        except Exception as e:
            print(f"Claude furigana error: {e}")
            return ""

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def evaluate_translation(self, source_text: str, user_translation: str, correct_translation: str, source_lang: str = "일본어") -> str:
        prompt = f"""Evaluate this translation:
Source ({source_lang}): {source_text}
User translation: {user_translation}
Correct translation: {correct_translation}

Scoring:
- Correct meaning, different style: 4-5 stars, feedback "좋아요" or "맞아요"
- Correct but unnatural: 3 stars
- Partially correct: 1-2 stars

Format:
Stars: ⭐⭐⭐⭐⭐ (1-5)
Feedback: 1-2 Korean words only (e.g. "좋아요", "맞아요", "어색함", "틀림", "애매함")"""
        
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
            return "평가 중 오류가 발생했습니다."
    
    async def generate_conversations(self, level: str, theme: str, count: int = 10) -> list:
        level_descriptions = {
            "N5": "가장 기본적인 일본어 (기본 인사, 숫자, 간단한 질문)",
            "N4": "초급 일본어 (일상 대화, 서비스 상황, 간단한 요청)",
            "N3": "중급 일본어 (정중한 표현, 비즈니스 기초, 복잡한 문장)",
            "N2": "상급 일본어 (정식 비즈니스 표현, 복잡한 경어)",
            "N1": "최고급 일본어 (고급 경어, 공식적인 표현, 복잡한 문법)"
        }
        
        theme_descriptions = {
            "daily_life": "일상생활 (인사, 식사, 쇼핑, 교통)",
            "restaurant": "식당 (주문, 예약, 계산, 서비스)",
            "business": "비즈니스 (회의, 이메일, 전화, 프레젠테이션)",
            "travel": "여행 (호텔, 공항, 관광, 길 찾기)",
            "shopping": "쇼핑 (가격 문의, 교환/환불, 결제)",
            "emergency": "응급상황 (병원, 경찰, 도움 요청)",
            "education": "교육 (학교, 수업, 시험, 학습)",
            "work": "직장 (면접, 업무, 동료, 상사)"
        }
        
        prompt = f"""일본어-한국어 학습용 대화 쌍을 {count}개 생성해주세요.

조건:
- JLPT {level} 수준: {level_descriptions.get(level, '')}
- 주제: {theme} - {theme_descriptions.get(theme, theme)}
- 각 대화는 일본어 문장과 자연스러운 한국어 번역으로 구성
- 실제 대화에서 자주 사용되는 실용적인 표현
- 문법과 어휘가 {level} 수준에 적합해야 함

출력 형식 (JSON):
[
  {{"jp": "일본어 문장", "kr": "한국어 번역"}}
]

{count}개의 서로 다른 대화를 생성해주세요."""

        try:
            response = await self.model.generate_content_async(prompt)
            content = response.text
            
            # Extract JSON from the response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                conversations = json.loads(json_match.group())
                return conversations
            else:
                print("Failed to extract JSON from Gemini response")
                return []
        except Exception as e:
            print(f"Gemini conversation generation error: {e}")
            return []
    
    async def generate_furigana(self, japanese_text: str) -> str:
        prompt = f"""Convert this Japanese text to hiragana reading (furigana):

Japanese: {japanese_text}

Rules:
- Convert ALL kanji to hiragana
- Keep existing hiragana as-is
- Add spaces between words for readability
- Separate particles (は, を, に, で, etc.) with spaces
- Output ONLY the hiragana reading, nothing else

Examples:
Input: 今日は良い天気ですね
Output: きょう は よい てんき です ね

Input: 私は学校に行きます
Output: わたし は がっこう に いき ます

Hiragana reading:"""
        
        try:
            response = await self.model.generate_content_async(prompt)
            content = response.text.strip()
            # Extract just the hiragana line
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and is_hiragana_only(line):
                    return line
            # If no pure hiragana line found, return empty string
            return ""
        except Exception as e:
            print(f"Gemini furigana error: {e}")
            return ""

class LLMManager:
    def __init__(self):
        self.provider = self._create_provider()
    
    def _create_provider(self) -> Optional[LLMProvider]:
        if config.llm_provider == "openai":
            return OpenAIProvider(config.llm_api_key)
        elif config.llm_provider == "claude":
            return ClaudeProvider(config.llm_api_key)
        elif config.llm_provider == "gemini":
            return GeminiProvider(config.llm_api_key)
        else:
            return None
    
    async def evaluate_translation(self, source_text: str, user_translation: str, correct_translation: str, source_lang: str = "일본어") -> str:
        if self.provider:
            return await self.provider.evaluate_translation(source_text, user_translation, correct_translation, source_lang)
        return "LLM 제공자가 설정되지 않았습니다."
    
    async def generate_conversations(self, level: str, theme: str, count: int = 10) -> list:
        if self.provider:
            return await self.provider.generate_conversations(level, theme, count)
        return []
    
    async def generate_furigana(self, japanese_text: str) -> str:
        if self.provider:
            return await self.provider.generate_furigana(japanese_text)
        return ""

llm_manager = LLMManager()