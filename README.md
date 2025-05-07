# 💸 ربات تلگرام قیمت لحظه‌ای بازار | tgju-price-bot

رباتی پیشرفته برای ارسال قیمت‌های لحظه‌ای بازار (دلار، طلا، سکه، تتر، انس) به کانال تلگرام از طریق وب‌سایت [tgju.org](https://www.tgju.org/).

---

## 📁 ساختار پروژه

tgju-price-bot/
├── main.py # نقطه ورود به برنامه
├── config.py # تنظیمات ربات (توکن، آیدی کانال، بازه زمانی آپدیت)
├── bot/
│ ├── bot.py # کلاس اصلی ربات تلگرام
│ └── handlers.py # مدیریت فرمان‌ها و پیام‌ها
├── services/
│ ├── scraper.py # استخراج داده از tgju
│ └── formatter.py # فرمت‌دهی پیام‌ها
├── utils/
│ ├── date_utils.py # ابزار تاریخ شمسی
│ └── logger.py # تنظیمات لاگ حرفه‌ای
├── tests/ # تست‌های واحد
│ ├── test_scraper.py
│ └── test_formatter.py
├── requirements.txt # کتابخانه‌های موردنیاز
└── README.md # مستندات پروژه

---

## ⚙️ نصب و راه‌اندازی

1. نصب پیش‌نیازها:

```bash
pip install -r requirements.txt
```
2. تنظیم مقادیر فایل config.py:
TELEGRAM_TOKEN = "توکن ربات شما"
CHANNEL_ID = "@your_channel"
UPDATE_INTERVAL = 600  # هر ۱۰ دقیقه
TIMEOUT = 15
RETRY_COUNT = 3
3. اجرای ربات:

```bash
python main.py
```
# 🔁 عملکرد ربات
اتصال پایدار به تلگرام با httpx و http2

واکشی و ارسال قیمت لحظه‌ای به صورت خودکار در بازه‌های زمانی مشخص

فرمت‌دهی پیشرفته پیام‌ها به همراه اموجی و واحد پول

مدیریت خطاهای شبکه (timeout, disconnect, ...) با tenacity

لاگ‌گیری کامل برای مانیتور وضعیت اجرا

# 🧪 تست‌گیری
```bash
pytest tests/
```
