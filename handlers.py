from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from utils import data_manager, wordbook_manager, audio_generator, user_data_manager
from llm import llm_manager
from config import config
import os
import asyncio

SELECTING_LEVEL, QUIZ_MODE = range(2)

def get_practice_keyboard(conversation):
    """Generate the standard practice keyboard layout"""
    return [
        [InlineKeyboardButton("🇯🇵 일본어 보기", callback_data=f"show_jp_{conversation['id']}")],
        [InlineKeyboardButton("🇰🇷 한국어 뜻 보기", callback_data=f"show_kr_{conversation['id']}")],
        [InlineKeyboardButton("🔊 일본어 듣기", callback_data=f"listen_{conversation['id']}")],
        [InlineKeyboardButton("📝 단어장에 저장", callback_data=f"save_{conversation['id']}")],
        [InlineKeyboardButton("🎯 퀴즈 모드", callback_data=f"quiz_{conversation['id']}")],
        [InlineKeyboardButton("⚙️ 레벨 변경", callback_data="change_level")]
    ]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    welcome_message = (
        f"안녕하세요 {user.first_name}님! 👋\n\n"
        "저는 언어 학습을 도와드리는 봇입니다.\n"
        "현재 일본어를 지원하며, 곧 더 많은 언어가 추가될 예정입니다.\n\n"
        "오전 9시부터 오후 11시까지 매시간 학습 문장을 보내드려요.\n"
        "먼저 일본어 레벨을 선택해주세요:"
    )
    
    keyboard = [
        [InlineKeyboardButton("N5 (초급)", callback_data="level_N5")],
        [InlineKeyboardButton("N4 (초중급)", callback_data="level_N4")],
        [InlineKeyboardButton("N3 (중급)", callback_data="level_N3")],
        [InlineKeyboardButton("N2 (중상급)", callback_data="level_N2")],
        [InlineKeyboardButton("N1 (상급)", callback_data="level_N1")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
    return SELECTING_LEVEL

async def level_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    level = query.data.replace("level_", "")
    user_data_manager.set_user_level(context, level)
    
    await query.edit_message_text(
        f"일본어 레벨 {level}을 선택하셨습니다! ✅\n\n"
        "이제 매일 아침 9시에 학습 문장을 받아보실 수 있습니다.\n"
        "바로 연습을 시작하려면 /push 명령어를 사용해주세요."
    )
    
    return ConversationHandler.END

async def send_daily_practice_to_user(bot, user_id: int, level: str = "N3"):
    conversation = await data_manager.get_conversation_by_level(level)
    
    if not conversation:
        await bot.send_message(
            chat_id=user_id,
            text=f"죄송합니다. {level} 레벨의 문장을 찾을 수 없습니다."
        )
        return
    
    # Store conversation without context for button usage
    # Note: This is a special case for broadcast where we don't have context
    # The conversation will be stored properly when accessed via buttons
    
    keyboard = get_practice_keyboard(conversation)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Generate status indicator
    realtime_indicator = "🔄 실시간 생성" if conversation.get("is_realtime", False) else "📚 저장된 대화"
    
    # Generate furigana for Japanese text
    furigana = await llm_manager.generate_furigana(conversation['jp'])
    
    message_text = (
        f"🌸 오늘의 학습 - 일본어 ({level})\n"
        f"{realtime_indicator}\n\n"
        f"🇯🇵 {conversation['jp']}\n"
    )
    
    if furigana:
        message_text += f"📝 {furigana}\n\n"
    else:
        message_text += "\n"
    
    message_text += "버튼을 눌러 한국어 뜻을 보거나 음성을 들어보세요!"
    
    await bot.send_message(
        chat_id=user_id,
        text=message_text,
        reply_markup=reply_markup
    )

async def send_daily_practice(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    level = user_data_manager.get_user_level(context)
    conversation = await data_manager.get_conversation_by_level(level)
    
    if not conversation:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"죄송합니다. {level} 레벨의 문장을 찾을 수 없습니다."
        )
        return
    
    user_data_manager.set_daily_conversation(context, conversation)
    
    keyboard = get_practice_keyboard(conversation)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Generate status indicator
    realtime_indicator = "🔄 실시간 생성" if conversation.get("is_realtime", False) else "📚 저장된 대화"
    
    # Generate furigana for Japanese text
    furigana = await llm_manager.generate_furigana(conversation['jp'])
    
    message_text = (
        f"🌸 오늘의 학습 - 일본어 ({level})\n"
        f"{realtime_indicator}\n\n"
        f"🇯🇵 {conversation['jp']}\n"
    )
    
    if furigana:
        message_text += f"📝 {furigana}\n\n"
    else:
        message_text += "\n"
    
    message_text += "버튼을 눌러 한국어 뜻을 보거나 음성을 들어보세요!"
    
    await context.bot.send_message(
        chat_id=user_id,
        text=message_text,
        reply_markup=reply_markup
    )

async def push_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in config.admin_ids and len(config.admin_ids) > 0:
        await update.message.reply_text("권한이 없습니다.")
        return
    
    await send_daily_practice(context, user_id)

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to generate new conversations"""
    user_id = str(update.effective_user.id)
    admin_ids = config.admin_ids.split(',') if config.admin_ids else []
    
    if user_id not in admin_ids:
        await update.message.reply_text("권한이 없습니다.")
        return
    
    # Parse arguments: /generate <level> <theme> <count>
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "사용법: /generate <level> <theme> <count>\n"
            "예: /generate N5 daily_life 10\n\n"
            "Levels: N5, N4, N3, N2, N1\n"
            "Themes: daily_life, restaurant, business, travel, shopping, emergency, education, work"
        )
        return
    
    level = args[0].upper()
    theme = args[1].lower()
    try:
        count = int(args[2])
    except ValueError:
        await update.message.reply_text("Count는 숫자여야 합니다.")
        return
    
    if level not in ["N5", "N4", "N3", "N2", "N1"]:
        await update.message.reply_text("유효하지 않은 레벨입니다. N5, N4, N3, N2, N1 중 선택하세요.")
        return
    
    if count > 50:
        await update.message.reply_text("한 번에 최대 50개까지만 생성할 수 있습니다.")
        return
    
    await update.message.reply_text(f"🤖 {level} {theme} 주제로 {count}개 대화를 생성 중입니다...")
    
    try:
        # Generate conversations
        conversations = await llm_manager.generate_conversations(level, theme, count)
        
        if conversations:
            # Add to data.json
            import json
            try:
                with open("data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = {"conversations": []}
            
            existing_conversations = data.get("conversations", [])
            next_id = max([c["id"] for c in existing_conversations]) + 1 if existing_conversations else 1
            
            # Add IDs and level to new conversations
            for conv in conversations:
                conv["id"] = next_id
                conv["level"] = level
                existing_conversations.append(conv)
                next_id += 1
            
            # Save back to file
            data["conversations"] = existing_conversations
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Reload data manager
            data_manager.load_data()
            
            await update.message.reply_text(
                f"✅ {len(conversations)}개 대화가 성공적으로 생성되었습니다!\n"
                f"총 대화 수: {len(existing_conversations)}개"
            )
            
            # Show sample
            if conversations:
                sample = conversations[0]
                await update.message.reply_text(
                    f"생성된 샘플:\n🇯🇵 {sample['jp']}\n🇰🇷 {sample['kr']}"
                )
        else:
            await update.message.reply_text("❌ 대화 생성에 실패했습니다.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ 오류가 발생했습니다: {str(e)}")
        print(f"Generate command error: {e}")

async def toggle_realtime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to toggle real-time generation mode"""
    user_id = str(update.effective_user.id)
    admin_ids = config.admin_ids.split(',') if config.admin_ids else []
    
    if user_id not in admin_ids:
        await update.message.reply_text("권한이 없습니다.")
        return
    
    # Toggle mode
    current_mode = data_manager.toggle_realtime_generation()
    mode_text = "활성화" if current_mode else "비활성화"
    
    await update.message.reply_text(
        f"🔄 실시간 생성 모드: {mode_text}\n\n"
        f"{'✅ 새로운 대화를 실시간으로 생성합니다' if current_mode else '📚 저장된 대화에서 선택합니다'}"
    )

async def test_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to test the broadcast function"""
    user_id = str(update.effective_user.id)
    admin_ids = config.admin_ids.split(',') if config.admin_ids else []
    
    if user_id not in admin_ids:
        await update.message.reply_text("권한이 없습니다.")
        return
    
    await update.message.reply_text("🧪 브로드캐스트 테스트를 시작합니다...")
    
    # Manually trigger broadcast logic
    app = context.application
    persistence = app.persistence
    if persistence:
        user_data = await persistence.get_user_data()
        if user_data:
            for uid in user_data:
                try:
                    user_info = user_data[uid]
                    if user_info and hasattr(user_info, 'get'):
                        level = user_info.get('level', 'N3')
                    else:
                        level = 'N3'
                    await send_daily_practice_to_user(app.bot, uid, level)
                except Exception as e:
                    await update.message.reply_text(f"❌ 사용자 {uid} 전송 실패: {e}")
                    return
            await update.message.reply_text("✅ 브로드캐스트 테스트 완료!")
        else:
            await update.message.reply_text("❌ 사용자 데이터가 없습니다.")
    else:
        await update.message.reply_text("❌ 지속성 데이터에 접근할 수 없습니다.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "new_quiz":
        # Start a new quiz with a random conversation
        level = user_data_manager.get_user_level(context)
        
        # Send waiting message as a new message
        waiting_msg = await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="새로운 퀴즈를 준비 중입니다... ⏳"
        )
        
        new_conversation = await data_manager.get_conversation_by_level(level)
        
        if not new_conversation:
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=waiting_msg.message_id,
                text="죄송합니다. 새로운 퀴즈를 찾을 수 없습니다."
            )
            return
        
        user_data_manager.set_quiz_data(context, new_conversation)
        
        # Create quiz keyboard with back button
        quiz_keyboard = [[InlineKeyboardButton("🔙 돌아가기", callback_data="back_to_menu")]]
        quiz_markup = InlineKeyboardMarkup(quiz_keyboard)
        
        # Replace waiting message with quiz
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=waiting_msg.message_id,
            text=f"🎯 퀴즈 모드\n\n다음 일본어를 한국어로 번역해주세요:\n\n🇯🇵 {new_conversation['jp']}\n\n번역을 입력해주세요:",
            reply_markup=quiz_markup
        )
        return
    
    if data == "change_level":
        keyboard = [
            [InlineKeyboardButton("N5 (초급)", callback_data="level_N5")],
            [InlineKeyboardButton("N4 (초중급)", callback_data="level_N4")],
            [InlineKeyboardButton("N3 (중급)", callback_data="level_N3")],
            [InlineKeyboardButton("N2 (중상급)", callback_data="level_N2")],
            [InlineKeyboardButton("N1 (상급)", callback_data="level_N1")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("새로운 레벨을 선택해주세요:", reply_markup=reply_markup)
        return
    
    if data.startswith("level_"):
        level = data.replace("level_", "")
        user_data_manager.set_user_level(context, level)
        await query.edit_message_text(f"레벨이 {level}로 변경되었습니다! ✅")
        return
    
    if data == "back_to_menu":
        daily_conv = user_data_manager.get_daily_conversation(context)
        if daily_conv:
            await send_daily_practice(context, query.from_user.id)
        else:
            await query.edit_message_text("메뉴로 돌아갑니다. /push 명령어로 새로운 연습을 시작하세요.")
        return
    
    parts = data.split("_")
    action = parts[0]
    
    if action == "show":
        lang = parts[1]  # jp or kr
        conv_id = int(parts[2]) if len(parts) > 2 else None
        
        # First check if it's the current daily conversation (for real-time generated ones)
        daily_conversation = user_data_manager.get_daily_conversation(context)
        if daily_conversation and daily_conversation.get('id') == conv_id:
            conversation = daily_conversation
        else:
            # Fall back to stored conversations
            conversation = data_manager.get_conversation_by_id(conv_id)
        
        if not conversation:
            await query.edit_message_text("문장을 찾을 수 없습니다.")
            return
        
        # Create keyboard with back button
        keyboard = get_practice_keyboard(conversation)
        keyboard.append([InlineKeyboardButton("🔙 돌아가기", callback_data=f"back_{conversation['id']}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
            
        if lang == "jp":
            # Generate furigana for Japanese text
            furigana = await llm_manager.generate_furigana(conversation['jp'])
            
            jp_text = f"🇯🇵 일본어: {conversation['jp']}"
            if furigana:
                jp_text += f"\n📝 읽기: {furigana}"
            
            await query.edit_message_text(
                text=jp_text,
                reply_markup=reply_markup
            )
        elif lang == "kr":
            await query.edit_message_text(
                text=f"🇰🇷 한국어: {conversation['kr']}",
                reply_markup=reply_markup
            )
        return
    
    # For all other actions (replay, save, quiz)
    conv_id = int(parts[1]) if len(parts) > 1 else None
    
    # First check if it's the current daily conversation (for real-time generated ones)
    daily_conversation = user_data_manager.get_daily_conversation(context)
    if daily_conversation and daily_conversation.get('id') == conv_id:
        conversation = daily_conversation
    else:
        # Fall back to stored conversations
        conversation = data_manager.get_conversation_by_id(conv_id)
    
    if not conversation:
        await query.edit_message_text("문장을 찾을 수 없습니다.")
        return
    
    if action == "listen" or action == "replay":
        # Generate audio on-demand
        await query.answer("음성을 생성하고 있습니다... ⏳")
        
        audio_file = await audio_generator.generate_audio(conversation["jp"], conversation["id"])
        if audio_file and os.path.exists(audio_file):
            with open(audio_file, 'rb') as audio:
                caption = "🔊 일본어 듣기" if action == "listen" else "🔁 다시 듣기"
                await context.bot.send_audio(
                    chat_id=query.from_user.id,
                    audio=audio,
                    caption=caption
                )
        else:
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="⚠️ 음성 파일 생성 중 오류가 발생했습니다."
            )
    
    elif action == "save":
        saved = await wordbook_manager.save_to_wordbook(query.from_user.id, conversation)
        if saved:
            await query.answer("단어장에 저장되었습니다! 📝", show_alert=True)
        else:
            await query.answer("이미 단어장에 있습니다.", show_alert=True)
    
    elif action == "quiz":
        user_data_manager.set_quiz_data(context, conversation)
        
        # Create quiz keyboard with back button
        quiz_keyboard = [[InlineKeyboardButton("🔙 돌아가기", callback_data=f"back_{conversation['id']}")]]
        quiz_markup = InlineKeyboardMarkup(quiz_keyboard)
        
        await query.edit_message_text(
            text=f"🎯 퀴즈 모드\n\n다음 일본어를 한국어로 번역해주세요:\n\n🇯🇵 {conversation['jp']}\n\n번역을 입력해주세요:",
            reply_markup=quiz_markup
        )
        # Don't return QUIZ_MODE here since this is not part of ConversationHandler
    
    elif action == "back":
        # Return to original practice view
        level = user_data_manager.get_user_level(context)
        keyboard = get_practice_keyboard(conversation)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Try to return to the original message format
        try:
            # First try editing as a regular message
            realtime_indicator = "🔄 실시간 생성" if conversation.get("is_realtime", False) else "📚 저장된 대화"
            
            # Generate furigana for Japanese text
            furigana = await llm_manager.generate_furigana(conversation['jp'])
            
            message_text = (
                f"🌸 오늘의 학습 - 일본어 ({level})\n"
                f"{realtime_indicator}\n\n"
                f"🇯🇵 {conversation['jp']}\n"
            )
            
            if furigana:
                message_text += f"📝 {furigana}\n\n"
            else:
                message_text += "\n"
            
            message_text += "버튼을 눌러 한국어 뜻을 보거나 음성을 들어보세요!"
            
            await query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup
            )
        except Exception as e:
            # If editing fails, just show a simple message
            await query.edit_message_text(
                text="메뉴로 돌아갑니다. /push 명령어로 새로운 연습을 시작하세요.",
                reply_markup=reply_markup
            )

async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_translation = update.message.text
    quiz_data = user_data_manager.get_quiz_data(context)
    
    if not quiz_data:
        await update.message.reply_text("퀴즈 데이터를 찾을 수 없습니다. 다시 시작해주세요.")
        return ConversationHandler.END
    
    await update.message.reply_text("평가 중입니다... ⏳")
    
    evaluation = await llm_manager.evaluate_translation(
        quiz_data["jp"],
        user_translation,
        quiz_data["kr"],
        "일본어"
    )
    
    result_message = (
        f"📊 평가 결과\n\n"
        f"일본어: {quiz_data['jp']}\n"
        f"정답: {quiz_data['kr']}\n"
        f"당신의 답: {user_translation}\n\n"
        f"{evaluation}"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 돌아가기", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(result_message, reply_markup=reply_markup)
    
    user_data_manager.clear_quiz_data(context)
    return ConversationHandler.END

async def quiz_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages when user is in quiz mode"""
    quiz_data = user_data_manager.get_quiz_data(context)
    
    if not quiz_data:
        return  # Not in quiz mode, ignore
    
    # Check if the message looks like a command or special input
    user_translation = update.message.text
    if user_translation.startswith('/') or len(user_translation) > 500:
        return  # Ignore commands and very long messages
    
    # Check if this is a valid quiz response timing (within 5 minutes of quiz start)
    # This prevents stale quiz data from interfering with normal conversation
    from datetime import datetime, timedelta
    if "quiz_start_time" in quiz_data:
        quiz_start = datetime.fromisoformat(quiz_data["quiz_start_time"])
        if datetime.now() - quiz_start > timedelta(minutes=5):
            user_data_manager.clear_quiz_data(context)
            await update.message.reply_text("퀴즈 시간이 초과되었습니다. 다시 시작해주세요.")
            return
    
    await update.message.reply_text("평가 중입니다... ⏳")
    
    # Get evaluation and furigana concurrently
    evaluation_task = llm_manager.evaluate_translation(
        quiz_data["jp"],
        user_translation,
        quiz_data["kr"],
        "일본어"
    )
    furigana_task = llm_manager.generate_furigana(quiz_data["jp"])
    
    evaluation, furigana = await asyncio.gather(evaluation_task, furigana_task)
    
    result_message = (
        f"📊 평가 결과\n\n"
        f"일본어: {quiz_data['jp']}\n"
    )
    
    if furigana:
        result_message += f"읽기: {furigana}\n"
    
    result_message += (
        f"정답: {quiz_data['kr']}\n"
        f"당신의 답: {user_translation}\n\n"
        f"{evaluation}"
    )
    
    # Create quiz result specific keyboard
    keyboard = [
        [InlineKeyboardButton("🎯 다른 퀴즈", callback_data="new_quiz")],
        [InlineKeyboardButton("🔁 다시 듣기", callback_data=f"replay_{quiz_data['id']}")],
        [InlineKeyboardButton("📝 단어장에 저장", callback_data=f"save_{quiz_data['id']}")],
        [InlineKeyboardButton("🔙 메뉴로 돌아가기", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(result_message, reply_markup=reply_markup)
    
    user_data_manager.clear_quiz_data(context)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    daily_conv = user_data_manager.get_daily_conversation(context)
    if daily_conv:
        await send_daily_practice(context, query.from_user.id)
    else:
        await query.edit_message_text("메뉴로 돌아갑니다. /push 명령어로 새로운 연습을 시작하세요.")

def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_LEVEL: [CallbackQueryHandler(level_selection, pattern="^level_")],
            QUIZ_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_answer)]
        },
        fallbacks=[CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$")]
    )