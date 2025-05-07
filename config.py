import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '********************')
    CHANNEL_ID = os.getenv('CHANNEL_ID', '************')
    TIMEOUT = int(os.getenv('TIMEOUT', 60))
    UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 3600))