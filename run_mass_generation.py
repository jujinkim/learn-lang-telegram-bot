#!/usr/bin/env python3
"""
Direct mass conversation generation - no interaction needed.
"""

import asyncio
import json
from llm import llm_manager

# Configuration
THEMES = [
    "daily_life",
    "restaurant", 
    "business",
    "travel",
    "shopping",
    "emergency",
    "education",
    "work"
]

LEVELS = ["N5", "N4", "N3", "N2", "N1"]
CONVERSATIONS_PER_THEME_LEVEL = 25  # 25 * 8 themes * 5 levels = 1000 conversations

async def mass_generate():
    """Generate conversations for all themes and levels."""
    print("🚀 Starting MASS conversation generation...")
    print("🎯 Target: 1000+ conversations")
    print("⚡ Going full throttle - no stopping!")
    
    # Load existing data
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            conversations = existing_data.get("conversations", [])
            next_id = max([c["id"] for c in conversations]) + 1 if conversations else 1
    except FileNotFoundError:
        conversations = []
        next_id = 1
    
    print(f"📊 Starting with {len(conversations)} existing conversations")
    
    generated_count = 0
    total_target = len(THEMES) * len(LEVELS) * CONVERSATIONS_PER_THEME_LEVEL
    
    for level in LEVELS:
        print(f"\n🎯 LEVEL {level} - LET'S GO!")
        
        for theme in THEMES:
            print(f"  🔥 Generating {CONVERSATIONS_PER_THEME_LEVEL} for {theme}...")
            
            try:
                # Generate conversations
                new_conversations = await llm_manager.generate_conversations(
                    level=level,
                    theme=theme,
                    count=CONVERSATIONS_PER_THEME_LEVEL
                )
                
                if new_conversations:
                    # Add IDs and level to each conversation
                    for conv in new_conversations:
                        conv["id"] = next_id
                        conv["level"] = level
                        conversations.append(conv)
                        next_id += 1
                        generated_count += 1
                    
                    progress = (generated_count / total_target) * 100
                    print(f"  ✅ SUCCESS! Generated {len(new_conversations)} | Progress: {generated_count}/{total_target} ({progress:.1f}%)")
                else:
                    print(f"  ❌ FAILED for {level} {theme}")
                
                # Save every 50 conversations
                if generated_count % 50 == 0:
                    save_data(conversations)
                    print(f"  💾 SAVED CHECKPOINT: {generated_count} conversations")
                
            except Exception as e:
                print(f"  💥 ERROR {level} {theme}: {e}")
                continue
    
    # Final save
    save_data(conversations)
    
    print(f"\n🎉🎉🎉 MASS GENERATION COMPLETE! 🎉🎉🎉")
    print(f"📊 Generated: {generated_count} new conversations")
    print(f"📊 Total in database: {len(conversations)} conversations")
    print(f"💾 Saved to data.json")
    print(f"🚀 Your bot now has MASSIVE conversation power!")

def save_data(conversations):
    """Save conversations to data.json file."""
    data = {
        "conversations": conversations
    }
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(mass_generate())