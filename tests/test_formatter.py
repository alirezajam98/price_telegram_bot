import logging
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# تنظیمات ربات
TELEGRAM_TOKEN = '***********************'
CHANNEL_ID = '****************'  # آیدی کانال شما
# تنظیمات تایم‌اوت
TIMEOUT = 60  # زمان تایم‌اوت برای درخواست‌های تلگرام (ثانیه)

# لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def format_price(price_text, is_rial=True):
    """فرمت عددی قیمت و اضافه کردن ریال (به جز انس)"""
    try:
        if price_text is None:
            return "نامشخص"

        # حذف کاراکترهای غیرعددی بجز اعشار
        clean_price = ''.join(c for c in price_text if c.isdigit() or c == '.' or c == ',')
        clean_price = clean_price.replace(',', '')

        # تبدیل به عدد و فرمت‌دهی
        if '.' in clean_price:
            formatted = f"{float(clean_price):,.2f}"
        else:
            formatted = f"{int(clean_price):,}"

        return f"{formatted} ریال" if is_rial else formatted
    except Exception as e:
        logger.error(f"خطا در تبدیل قیمت {price_text}: {e}")
        return price_text


import re


def extract_change_values(change_text, is_ons=False):
    """استخراج درصد و مقدار تغییر از متن"""
    try:
        if change_text is None:
            return "0%", "0"

        # حذف فاصله‌های اضافی
        change_text = change_text.strip()
        logger.info(f"استخراج تغییرات از متن: {change_text}")

        # الگوی معمول: درصد در پرانتز، سپس مقدار تغییر
        # مثال: (1.37%) 8,520
        pattern1 = r'\(([+-]?[\d.]+)%\)\s*([+-]?[\d,.]+)'

        # الگوی دیگر: مقدار تغییر، سپس درصد در پرانتز
        # مثال: 8,520 (1.37%)
        pattern2 = r'([+-]?[\d,.]+)\s*\(([+-]?[\d.]+)%\)'

        # بررسی الگوی اول
        match1 = re.search(pattern1, change_text)
        if match1:
            percent = f"{match1.group(1)}%"
            amount = match1.group(2).replace(',', '')
            logger.info(f"الگوی 1 پیدا شد: درصد={percent}, مقدار={amount}")
            return percent, amount

        # بررسی الگوی دوم
        match2 = re.search(pattern2, change_text)
        if match2:
            amount = match2.group(1).replace(',', '')
            percent = f"{match2.group(2)}%"
            logger.info(f"الگوی 2 پیدا شد: درصد={percent}, مقدار={amount}")
            return percent, amount

        # بررسی فقط برای درصد
        percent_pattern = r'([+-]?[\d.]+)%'
        percent_match = re.search(percent_pattern, change_text)
        if percent_match:
            logger.info(f"فقط درصد پیدا شد: {percent_match.group(1)}%")
            return f"{percent_match.group(1)}%", "0"

        # بررسی فقط برای مقدار عددی
        amount_pattern = r'([+-]?[\d,.]+)'
        amount_match = re.search(amount_pattern, change_text)
        if amount_match:
            logger.info(f"فقط مقدار پیدا شد: {amount_match.group(1)}")
            return "0%", amount_match.group(1).replace(',', '')

        logger.warning(f"هیچ الگویی پیدا نشد برای: {change_text}")
        return "0%", "0"
    except Exception as e:
        logger.error(f"خطا در استخراج تغییرات از {change_text}: {e}")
        return "0%", "0"


def convert_to_toman(price_str):
    """تبدیل قیمت از ریال به تومان"""
    try:
        if isinstance(price_str, (str, int, float)):
            # اگر رشته است، کاماها را حذف کرده و به عدد تبدیل می‌کنیم
            if isinstance(price_str, str):
                price_num = int(''.join(c for c in price_str if c.isdigit()))
            else:
                price_num = int(price_str)

            # تبدیل به تومان (تقسیم بر 10)
            toman_value = price_num // 10
            return "{:,}".format(toman_value)
        return str(price_str)
    except Exception as e:
        logger.error(f"خطا در تبدیل به تومان {price_str}: {e}")
        return str(price_str)


async def get_tgju_data():
    """گرفتن داده از سایت tgju با Playwright (async)"""
    url = "https://www.tgju.org"
    try:
        logger.info("شروع دریافت داده‌ها از tgju")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            logger.info(f"رفتن به آدرس {url}")
            await page.goto(url, timeout=30000)

            # منتظر بارگذاری کامل صفحه می‌مانیم
            logger.info("منتظر بارگذاری صفحه...")
            await page.wait_for_selector('li[id^="l-"]', timeout=10000)
            await page.wait_for_timeout(5000)

            # اسکرین‌شات بگیریم تا بفهمیم آیا صفحه درست لود شده یا نه
            await page.screenshot(path='tgju_page.png')
            logger.info("اسکرین‌شات از صفحه گرفته شد (tgju_page.png)")

            html = await page.content()
            logger.info(f"HTML دریافت شد (طول: {len(html)})")
            await browser.close()

        soup = BeautifulSoup(html, "html.parser")

        elements = {
            'coin': ('sekee', 'سکه'),
            'dollar': ('price_dollar_rl', 'دلار'),
            'gold': ('geram18', 'طلا'),
            'ons': ('ons', 'انس'),
            'tether': ('crypto-tether-irr', 'تتر')
        }

        data = {}
        for key, (element_id, name) in elements.items():
            logger.info(f"در حال پردازش {name} با ID: {element_id}")
            element = soup.find('li', {'id': f'l-{element_id}'})

            if element:
                li_classes = element.get('class', [])

                # چاپ کل المان برای دیباگ
                logger.info(f"المان {name} یافت شد: {element}")

                # پیدا کردن عناصر قیمت و تغییر
                price_element = element.find('span', class_='info-price')
                change_element = element.find('span', class_='info-change')

                # نمایش کامل عناصر قیمت و تغییر برای دیباگ
                logger.info(f"عنصر قیمت: {price_element}")
                logger.info(f"عنصر تغییر: {change_element}")

                price_text = price_element.text.strip() if price_element else "0"
                change_text = change_element.text.strip() if change_element else "(0%)"

                # نمایش متن دقیق عناصر
                logger.info(f"متن قیمت: '{price_text}'")
                logger.info(f"متن تغییر: '{change_text}'")

                # تعیین روند قیمت (صعودی یا نزولی)
                trend = 'low' if 'low' in li_classes else 'high' if 'high' in li_classes else 'neutral'

                logger.info(f"{name}: قیمت={price_text}, تغییر={change_text}, روند={trend}")

                # استخراج درصد و مقدار تغییر
                percent, amount = extract_change_values(change_text, is_ons=(key == 'ons'))
                logger.info(f"نتیجه استخراج تغییرات برای {name}: درصد={percent}, مقدار={amount}")

                # برای انس، قیمت به ریال/تومان نیست، پس تبدیل نمی‌کنیم
                final_price = price_text
                if key != 'ons':
                    final_price = convert_to_toman(price_text)
                    final_amount = amount
                    if amount != "0":
                        final_amount = convert_to_toman(amount)
                else:
                    final_amount = amount

                logger.info(f"قیمت نهایی: {final_price}, مقدار تغییر نهایی: {final_amount}")

                data[key] = {
                    'name': name,
                    'price': final_price,
                    'percent': percent,
                    'amount': final_amount,
                    'trend': trend
                }
                logger.info(f"اطلاعات {name} با موفقیت پردازش شد: {data[key]}")
            else:
                logger.warning(f"المان {name} با ID {element_id} یافت نشد")

        logger.info(f"همه داده‌ها با موفقیت پردازش شدند: {data}")
        return data

    except Exception as e:
        logger.error(f"❌ خطا در دریافت داده از tgju: {e}")
        return None


async def send_price_to_channel(context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام به کانال تلگرام"""
    try:
        logger.info("شروع دریافت داده‌ها برای ارسال به کانال")
        data = await get_tgju_data()

        if not data:
            logger.error("داده‌ای برای ارسال به کانال دریافت نشد")
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text="⚠️ خطا در دریافت اطلاعات بازار.",
                read_timeout=TIMEOUT,
                write_timeout=TIMEOUT,
                connect_timeout=TIMEOUT
            )
            return

        # دریافت تاریخ شمسی
        jalali_date = get_jalali_date()

        message_lines = [
            f"📊 *قیمت‌های لحظه‌ای بازار*",
            f"🕒 {jalali_date}",
            "\n━━━━━━━━✨*وضعیت بازار*✨━━━━━━━━\n"
        ]

        for key in ['coin', 'dollar', 'tether', 'gold', 'ons']:
            item = data.get(key)
            if item:
                # تعیین ایموجی بر اساس روند قیمت
                emoji = '🔴' if item['trend'] == 'low' else '🟢' if item['trend'] == 'high' else '⚪️'

                # تنظیم فرمت نمایش قیمت
                currency_suffix = 'دلار' if key == 'ons' else 'تومان'
                price_display = f"{item['price']} {currency_suffix}"

                # فرمت بندی مقدار تغییر
                if item['amount'] != "0":
                    amount_display = f"{item['amount']} {currency_suffix}"
                else:
                    amount_display = "0"

                # اضافه کردن خط اطلاعات
                message_lines.append(
                    f"{emoji} *{item['name']}*: {price_display} \n تغییر: {item['percent']} ({amount_display})\n"
                )

        # ارسال پیام به کانال
        logger.info(f"در حال ارسال پیام به کانال {CHANNEL_ID}")
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text="\n".join(message_lines),
            parse_mode='Markdown',
            read_timeout=TIMEOUT,
            write_timeout=TIMEOUT,
            connect_timeout=TIMEOUT
        )
        logger.info("پیام با موفقیت به کانال ارسال شد")

    except Exception as e:
        logger.error(f"خطا در ارسال پیام به کانال: {e}")
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"⚠️ خطا در ارسال اطلاعات بازار: {str(e)}",
                read_timeout=TIMEOUT,
                write_timeout=TIMEOUT,
                connect_timeout=TIMEOUT
            )
        except:
            logger.error("خطا در ارسال پیام خطا به کانال")


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /price برای دریافت دستی"""
    try:
        user_id = update.effective_user.id
        logger.info(f"دستور price از کاربر {user_id} دریافت شد")

        # ارسال پیام در حال پردازش
        processing_message = await update.message.reply_text("در حال دریافت اطلاعات بازار...")

        # دریافت و ارسال داده‌ها به کانال
        await send_price_to_channel(context)

        # اطلاع به کاربر
        await processing_message.edit_text("✅ اطلاعات بازار با موفقیت به کانال ارسال شد.")

    except Exception as e:
        logger.error(f"خطا در اجرای دستور price: {e}")
        await update.message.reply_text(f"❌ خطا در دریافت اطلاعات بازار: {str(e)}")


# مدیریت تاریخ شمسی
try:
    from jdatetime import datetime as jdatetime

    logger.info("ماژول jdatetime با موفقیت وارد شد")
except ImportError:
    logger.info("در حال نصب ماژول jdatetime...")
    import subprocess

    subprocess.run(['pip', 'install', 'jdatetime'], check=True)
    from jdatetime import datetime as jdatetime

    logger.info("ماژول jdatetime با موفقیت نصب و وارد شد")


def get_jalali_date():
    """دریافت تاریخ شمسی"""
    try:
        now = jdatetime.now()
        months = [
            'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
            'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
        ]
        return f"{now.hour:02}:{now.minute:02} - {now.day} {months[now.month - 1]} {now.year}"
    except Exception as e:
        logger.error(f"خطا در دریافت تاریخ شمسی: {e}")
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """تابع اصلی برنامه"""
    try:
        logger.info("شروع اجرای برنامه")
        # ساخت نمونه از Application
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # افزودن دستور /price
        application.add_handler(CommandHandler("price", price_command))

        # تنظیم ارسال خودکار هر یک ساعت
        job_queue = application.job_queue
        job_queue.run_repeating(send_price_to_channel, interval=3600, first=10)
        logger.info("زمانبندی ارسال خودکار با موفقیت تنظیم شد")

        # شروع پولینگ
        logger.info("در حال شروع پولینگ تلگرام...")
        application.run_polling()

    except Exception as e:
        logger.critical(f"خطای بحرانی در اجرای برنامه: {e}")


if __name__ == "__main__":
    main()