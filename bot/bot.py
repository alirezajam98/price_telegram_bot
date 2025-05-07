import logging
from telegram.ext import Application, ContextTypes
from services.scraper import TgjuScraper
from services.formatter import PriceFormatter
from utils.date_utils import get_jalali_date
from config import Config

logger = logging.getLogger(__name__)


class TelegramPriceBot:
    def __init__(self):
        self.config = Config()
        self.scraper = TgjuScraper()
        self.formatter = PriceFormatter()
        self.app = Application.builder().token(self.config.TELEGRAM_TOKEN).build()

        # ذخیره instance در bot_data
        self.app.bot_data['bot_instance'] = self

    async def send_price_to_channel(self, context: ContextTypes.DEFAULT_TYPE):
        """Send price update to channel"""
        try:
            logger.info("Starting to fetch data for channel")
            data = await self.scraper.get_tgju_data()

            if not data:
                logger.error("No data received for channel")
                await self._send_error(context, "⚠️ خطا در دریافت اطلاعات بازار.")
                return

            message = self._prepare_message(data)
            await context.bot.send_message(
                chat_id=self.config.CHANNEL_ID,
                text=message,
                parse_mode='Markdown',
                read_timeout=self.config.TIMEOUT,
                write_timeout=self.config.TIMEOUT,
                connect_timeout=self.config.TIMEOUT
            )
            logger.info("Message successfully sent to channel")

        except Exception as e:
            logger.error(f"Error sending to channel: {e}")
            await self._send_error(context, f"⚠️ خطا در ارسال اطلاعات بازار: {str(e)}")

    def _prepare_message(self, data: dict) -> str:
        """Prepare formatted message"""
        message_lines = [
            f"📊 *قیمت‌های لحظه‌ای بازار*",
            f"🕒 {get_jalali_date()}",
            "\n━━━━━━━━✨*وضعیت بازار*✨━━━━━━━━\n"
        ]

        for key in ['coin', 'dollar', 'tether', 'gold', 'ons']:
            item = data.get(key)
            if not item:
                continue

            emoji = '🔴' if item['trend'] == 'low' else '🟢' if item['trend'] == 'high' else '⚪️'
            percent, amount = self.formatter.extract_change_values(item['change'])
            is_ons = (key == 'ons')

            price = item['price'] if is_ons else self.formatter.convert_to_toman(item['price'])
            amount = amount if is_ons else self.formatter.convert_to_toman(amount) if amount != "0" else "0"
            currency = 'دلار' if is_ons else 'تومان'

            message_lines.append(
                f"{emoji} *{item['name']}*: {price} {currency}\nتغییر: {percent} ({amount} {currency})\n"
            )

        return "\n".join(message_lines)

    async def _send_error(self, context: ContextTypes.DEFAULT_TYPE, message: str):
        """Send error message to channel"""
        try:
            await context.bot.send_message(
                chat_id=self.config.CHANNEL_ID,
                text=message,
                read_timeout=self.config.TIMEOUT,
                write_timeout=self.config.TIMEOUT,
                connect_timeout=self.config.TIMEOUT
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

    def run(self):
        """Run the bot"""
        from bot.handlers import setup_handlers
        setup_handlers(self)

        self.app.job_queue.run_repeating(
            self.send_price_to_channel,
            interval=self.config.UPDATE_INTERVAL,
            first=10
        )
        self.app.run_polling()
