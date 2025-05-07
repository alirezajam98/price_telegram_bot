import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # تنظیمات اصلی
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '7840563922:AAEcEOi_zLFcPxbS8Ms412SWoNoQD33pEaQ')
    CHANNEL_ID = os.getenv('CHANNEL_ID', '@coine_dollar')
    TIMEOUT = int(os.getenv('TIMEOUT', 30))  # 30 ثانیه

    # تنظیمات جدید برای تلاش مجدد
    RETRY_COUNT = int(os.getenv('RETRY_COUNT', 3))  # اضافه کردن این خط
    UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 3600))