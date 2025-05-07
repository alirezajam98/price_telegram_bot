import logging
from bot.bot import TelegramPriceBot
from utils.logger import setup_logging

def main():
    setup_logging()
    bot = TelegramPriceBot()
    bot.run()

if __name__ == "__main__":
    main()