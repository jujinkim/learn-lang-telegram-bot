import logging
import asyncio
from datetime import time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PicklePersistence
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import config
from handlers import (
    get_conversation_handler,
    push_command,
    button_callback,
    send_daily_practice
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class JapaneseLearningBot:
    def __init__(self):
        self.application = None
        self.scheduler = AsyncIOScheduler()
        self.user_ids = set()
    
    async def error_handler(self, update: Update, context):
        logger.error(f"Update {update} caused error {context.error}")
    
    async def daily_broadcast(self):
        if not self.application:
            return
        
        for user_id in self.user_ids:
            try:
                await send_daily_practice(self.application.context_types.context, user_id)
            except Exception as e:
                logger.error(f"Failed to send daily practice to user {user_id}: {e}")
    
    def track_user(self, update: Update, context):
        if update.effective_user:
            self.user_ids.add(update.effective_user.id)
    
    async def post_init(self, application: Application):
        hour, minute = config.daily_time.split(":")
        
        trigger = CronTrigger(
            hour=int(hour),
            minute=int(minute),
            timezone=pytz.timezone(config.timezone)
        )
        
        self.scheduler.add_job(
            self.daily_broadcast,
            trigger=trigger,
            id="daily_broadcast",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler started. Daily broadcast at {config.daily_time} {config.timezone}")
    
    def run(self):
        is_valid, error_msg = config.validate()
        if not is_valid:
            logger.error(f"Configuration error: {error_msg}")
            return
        
        persistence = PicklePersistence(filepath="bot_data.pickle")
        
        self.application = (
            Application.builder()
            .token(config.bot_token)
            .persistence(persistence)
            .post_init(self.post_init)
            .build()
        )
        
        conv_handler = get_conversation_handler()
        self.application.add_handler(conv_handler)
        
        self.application.add_handler(CommandHandler("push", push_command))
        
        self.application.add_handler(
            CallbackQueryHandler(button_callback, pattern="^(show_|replay_|save_|quiz_|change_level)")
        )
        
        self.application.add_error_handler(self.error_handler)
        
        for handler in self.application.handlers[0]:
            handler.callback = lambda update, context: (
                handler.callback(update, context),
                self.track_user(update, context)
            )[-1]
        
        logger.info("Bot started!")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    bot = JapaneseLearningBot()
    bot.run()

if __name__ == "__main__":
    main()