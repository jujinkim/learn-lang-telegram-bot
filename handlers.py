from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from utils import data_manager, wordbook_manager, audio_generator, user_data_manager
from llm import llm_manager
from config import config
import os

SELECTING_LEVEL, QUIZ_MODE = range(2)

def get_practice_keyboard(conversation):
    """Generate the standard practice keyboard layout"""
    return [
        [InlineKeyboardButton("🇯🇵 일본어 보기", callback_data=f"show_jp_{conversation['id']}")],
        [InlineKeyboardButton("🇰🇷 한국어 뜻 보기", callback_data=f"show_kr_{conversation['id']}")],
        [InlineKeyboardButton("🔁 다시 듣기", callback_data=f"replay_{conversation['id']}")],
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
        "매일 아침 9시에 학습 문장을 음성과 함께 보내드려요.\n"
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
    conversation = data_manager.get_conversation_by_level(level)
    
    if not conversation:
        await bot.send_message(
            chat_id=user_id,
            text=f"죄송합니다. {level} 레벨의 문장을 찾을 수 없습니다."
        )
        return
    
    audio_file = await audio_generator.generate_audio(conversation["jp"], conversation["id"])
    
    keyboard = get_practice_keyboard(conversation)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = f"🌸 오늘의 학습 - 일본어 ({level})"
    
    if audio_file and os.path.exists(audio_file):
        with open(audio_file, 'rb') as audio:
            await bot.send_audio(
                chat_id=user_id,
                audio=audio,
                caption=caption,
                reply_markup=reply_markup
            )
    else:
        await bot.send_message(
            chat_id=user_id,
            text=caption + "\n\n⚠️ 음성 파일 생성 중 오류가 발생했습니다.",
            reply_markup=reply_markup
        )

async def send_daily_practice(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    level = user_data_manager.get_user_level(context)
    conversation = data_manager.get_conversation_by_level(level)
    
    if not conversation:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"죄송합니다. {level} 레벨의 문장을 찾을 수 없습니다."
        )
        return
    
    user_data_manager.set_daily_conversation(context, conversation)
    
    audio_file = await audio_generator.generate_audio(conversation["jp"], conversation["id"])
    
    keyboard = get_practice_keyboard(conversation)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = f"🌸 오늘의 학습 - 일본어 ({level})"
    
    if audio_file and os.path.exists(audio_file):
        with open(audio_file, 'rb') as audio:
            await context.bot.send_audio(
                chat_id=user_id,
                audio=audio,
                caption=caption,
                reply_markup=reply_markup
            )
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=caption + "\n\n⚠️ 음성 파일 생성 중 오류가 발생했습니다.",
            reply_markup=reply_markup
        )

async def push_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in config.admin_ids and len(config.admin_ids) > 0:
        await update.message.reply_text("권한이 없습니다.")
        return
    
    await send_daily_practice(context, user_id)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
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
    
    parts = data.split("_")
    action = parts[0]
    
    if action == "show":
        lang = parts[1]  # jp or kr
        conv_id = int(parts[2]) if len(parts) > 2 else None
        
        conversation = data_manager.get_conversation_by_id(conv_id)
        if not conversation:
            await query.edit_message_text("문장을 찾을 수 없습니다.")
            return
        
        # Create keyboard with back button
        keyboard = get_practice_keyboard(conversation)
        keyboard.append([InlineKeyboardButton("🔙 돌아가기", callback_data=f"back_{conversation['id']}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
            
        if lang == "jp":
            await query.edit_message_caption(
                caption=f"🇯🇵 일본어: {conversation['jp']}",
                reply_markup=reply_markup
            )
        elif lang == "kr":
            await query.edit_message_caption(
                caption=f"🇰🇷 한국어: {conversation['kr']}",
                reply_markup=reply_markup
            )
        return
    
    # For all other actions (replay, save, quiz)
    conv_id = int(parts[1]) if len(parts) > 1 else None
    
    conversation = data_manager.get_conversation_by_id(conv_id)
    if not conversation:
        await query.edit_message_text("문장을 찾을 수 없습니다.")
        return
    
    if action == "replay":
        audio_file = await audio_generator.generate_audio(conversation["jp"], conversation["id"])
        if audio_file and os.path.exists(audio_file):
            with open(audio_file, 'rb') as audio:
                await context.bot.send_audio(
                    chat_id=query.from_user.id,
                    audio=audio,
                    caption="🔁 다시 듣기"
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
        
        await query.edit_message_caption(
            caption=f"🎯 퀴즈 모드\n\n다음 일본어를 한국어로 번역해주세요:\n\n🇯🇵 {conversation['jp']}\n\n번역을 입력해주세요:",
            reply_markup=quiz_markup
        )
        return QUIZ_MODE
    
    elif action == "back":
        # Return to original practice view
        level = user_data_manager.get_user_level(context)
        keyboard = get_practice_keyboard(conversation)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_caption(
            caption=f"🌸 오늘의 학습 - 일본어 ({level})",
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