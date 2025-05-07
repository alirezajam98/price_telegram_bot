import logging
import httpx
from telegram.ext import Application, ContextTypes, ApplicationBuilder
from telegram import Update
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from services.scraper import TgjuScraper
from services.formatter import PriceFormatter
from utils.date_utils import get_jalali_date
from utils.logger import setup_logging
from config import Config

logger = logging.getLogger(__name__)


class TelegramPriceBot:
    def __init__(self):
        setup_logging()
        self.config = Config()
        self.scraper = TgjuScraper()
        self.formatter = PriceFormatter()

        # تنظیمات پیشرفته HTTP با پارامترهای بهینه شده
        self.app = self._configure_application()
        self.app.bot_data['bot_instance'] = self

    def _configure_application(self):
        """تنظیمات پیشرفته برای ارتباط با سرورهای تلگرام"""
        return (
            ApplicationBuilder()
            .token(self.config.TELEGRAM_TOKEN)
            .pool_timeout(self.config.TIMEOUT)
            .connect_timeout(self.config.TIMEOUT)
            .read_timeout(self.config.TIMEOUT)
            .http_version("2")
            .get_updates_http_version("2")
            .build()
        )

    @retry(
        stop=stop_after_attempt(Config.RETRY_COUNT),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=(
                retry_if_exception_type(httpx.ConnectTimeout) |
                retry_if_exception_type(httpx.ReadTimeout) |
                retry_if_exception_type(httpx.NetworkError)
        ),
        reraise=True
    )
    async def send_price_to_channel(self, context: ContextTypes.DEFAULT_TYPE):
        """ارسال پیام به کانال با مدیریت خطاهای پیشرفته"""
        try:
            if not await self._check_network_connection():
                raise httpx.NetworkError("No internet connection available")

            logger.info("در حال دریافت داده‌های بازار...")
            data = await self.scraper.get_tgju_data()

            if not data:
                logger.error("داده‌ای برای ارسال دریافت نشد")
                await self._send_error(context, "⚠️ خطا در دریافت اطلاعات بازار")
                return

            message = self._prepare_message(data)
            await self._send_telegram_message(context, message)

        except Exception as e:
            logger.error(f"خطای غیرمنتظره در ارسال پیام: {type(e).__name__} - {str(e)}")
            await self._handle_http_errors(context, e)
            raise

    async def _send_telegram_message(self, context: ContextTypes.DEFAULT_TYPE, message: str):
        """ارسال پیام به تلگرام با تنظیمات بهینه"""
        try:
            await context.bot.send_message(
                chat_id=self.config.CHANNEL_ID,
                text=message,
                parse_mode='Markdown',
                read_timeout=self.config.TIMEOUT,
                write_timeout=self.config.TIMEOUT,
                connect_timeout=self.config.TIMEOUT,
                api_kwargs={
                    'retry_timeout': self.config.TIMEOUT,
                    'http_version': '2'
                }
            )
            logger.info("پیام با موفقیت ارسال شد")
        except Exception as e:
            logger.error(f"خطا در ارسال پیام: {e}")
            raise

    def _prepare_message(self, data: dict) -> str:
        """آماده‌سازی متن پیام"""
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

    async def _handle_http_errors(self, context: ContextTypes.DEFAULT_TYPE, error: Exception):
        """مدیریت خطاهای HTTP"""
        error_messages = {
            httpx.ConnectTimeout: "⏳ اتصال به سرور تلگرام زمان‌گذشت",
            httpx.ReadTimeout: "⌛️ سرور تلگرام پاسخ نداد",
            httpx.NetworkError: "🔌 مشکل در اتصال به اینترنت",
            httpx.HTTPStatusError: f"⚠️ خطای سرور (کد {error.response.status_code})"
        }

        for error_type, message in error_messages.items():
            if isinstance(error, error_type):
                await self._send_error(context, message)
                return

        await self._send_error(context, "⚠️ خطای ناشناخته در ارتباط با تلگرام")

    async def _send_error(self, context: ContextTypes.DEFAULT_TYPE, message: str):
        """ارسال پیام خطا"""
        try:
            await context.bot.send_message(
                chat_id=self.config.CHANNEL_ID,
                text=message,
                read_timeout=self.config.TIMEOUT,
                write_timeout=self.config.TIMEOUT,
                connect_timeout=self.config.TIMEOUT
            )
        except Exception as e:
            logger.error(f"خطا در ارسال پیام خطا: {e}")

    async def _check_network_connection(self) -> bool:
        """بررسی اتصال به اینترنت"""
        try:
            async with httpx.AsyncClient() as client:
                await client.get("https://api.telegram.org", timeout=5)
            return True
        except Exception:
            return False

    def run(self):
        """راه‌اندازی ربات"""
        from bot.handlers import setup_handlers
        setup_handlers(self)

        self.app.job_queue.run_repeating(
            self.send_price_to_channel,
            interval=self.config.UPDATE_INTERVAL,
            first=10
        )

        logger.info("ربات در حال راه‌اندازی...")
        self.app.run_polling(
            close_loop=False,
            stop_signals=None,
            drop_pending_updates=True
        )