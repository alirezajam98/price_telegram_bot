from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import logging

logger = logging.getLogger(__name__)


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /price command"""
    try:
        user_id = update.effective_user.id
        logger.info(f"Price command received from user {user_id}")

        # دریافت instance ربات از context
        bot = context.bot_data['bot_instance']

        processing_message = await update.message.reply_text("در حال دریافت اطلاعات بازار...")

        # فراخوانی متد از طریق instance ربات
        await context.application.job_queue.run_once(
            lambda ctx: bot.send_price_to_channel(ctx),
            when=0,
            chat_id=update.effective_chat.id
        )
        await processing_message.edit_text("✅ اطلاعات بازار با موفقیت به کانال ارسال شد.")

    except Exception as e:
        logger.error(f"Error in price_command: {e}")
        await update.message.reply_text(f"❌ خطا در دریافت اطلاعات بازار: {str(e)}")


def setup_handlers(bot):
    """Setup bot handlers"""
    bot.app.add_handler(CommandHandler("price", price_command))
    bot.app.bot_data['bot_instance'] = bot  # ذخیره instance ربات
