#!/usr/bin/env python3
"""
Batch conversation generation script for Japanese language learning bot.
This script generates thousands of conversations using LLM and saves them to data.json.
"""

import asyncio
import json
from llm import llm_manager
from utils import data_manager

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

# How many conversations to generate per theme per level
CONVERSATIONS_PER_THEME_LEVEL = 25  # 25 * 8 themes * 5 levels = 1000 conversations

async def generate_conversations_batch():
    """Generate conversations in batches for all themes and levels."""
    print("🚀 Starting batch conversation generation...")
    
    # Load existing data
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            conversations = existing_data.get("conversations", [])
            next_id = max([c["id"] for c in conversations]) + 1 if conversations else 1
    except FileNotFoundError:
        conversations = []
        next_id = 1
    
    total_to_generate = len(THEMES) * len(LEVELS) * CONVERSATIONS_PER_THEME_LEVEL
    print(f"📊 Target: {total_to_generate} new conversations")
    print(f"📊 Current conversations: {len(conversations)}")
    
    generated_count = 0
    
    for level in LEVELS:
        print(f"\n🎯 Processing level {level}...")
        
        for theme in THEMES:
            print(f"  📝 Generating {CONVERSATIONS_PER_THEME_LEVEL} conversations for {theme}...")
            
            try:
                # Generate conversations for this theme/level combination
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
                    
                    print(f"  ✅ Generated {len(new_conversations)} conversations for {level} {theme}")
                else:
                    print(f"  ❌ Failed to generate conversations for {level} {theme}")
                
                # Save progress periodically
                if generated_count % 100 == 0:
                    save_data(conversations)
                    print(f"  💾 Saved progress: {generated_count}/{total_to_generate}")
                
            except Exception as e:
                print(f"  ❌ Error generating {level} {theme}: {e}")
                continue
    
    # Final save
    save_data(conversations)
    
    print(f"\n🎉 Generation complete!")
    print(f"📊 Total conversations generated: {generated_count}")
    print(f"📊 Total conversations in database: {len(conversations)}")
    print(f"💾 Data saved to data.json")

def save_data(conversations):
    """Save conversations to data.json file."""
    data = {
        "conversations": conversations
    }
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def generate_sample():
    """Generate a small sample to test the system."""
    print("🧪 Generating sample conversations...")
    
    sample_conversations = await llm_manager.generate_conversations(
        level="N5",
        theme="daily_life", 
        count=5
    )
    
    if sample_conversations:
        print("✅ Sample generation successful!")
        for i, conv in enumerate(sample_conversations, 1):
            print(f"{i}. {conv['jp']} → {conv['kr']}")
    else:
        print("❌ Sample generation failed!")
    
    return sample_conversations

async def main():
    """Main function with menu system."""
    print("🤖 Japanese Conversation Generator")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Generate sample (5 conversations)")
        print("2. Generate full batch (1000+ conversations)")
        print("3. Check current data stats")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            await generate_sample()
        elif choice == "2":
            confirm = input("This will generate 1000+ conversations. Continue? (y/N): ").strip().lower()
            if confirm == 'y':
                await generate_conversations_batch()
            else:
                print("Cancelled.")
        elif choice == "3":
            try:
                with open("data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    conversations = data.get("conversations", [])
                    
                    print(f"\n📊 Current Statistics:")
                    print(f"Total conversations: {len(conversations)}")
                    
                    # Count by level
                    level_counts = {}
                    for conv in conversations:
                        level = conv.get("level", "Unknown")
                        level_counts[level] = level_counts.get(level, 0) + 1
                    
                    for level in ["N5", "N4", "N3", "N2", "N1"]:
                        count = level_counts.get(level, 0)
                        print(f"{level}: {count} conversations")
                        
            except FileNotFoundError:
                print("📊 No data.json found. Run generation first.")
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())