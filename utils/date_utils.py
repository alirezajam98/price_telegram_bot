import logging
from jdatetime import datetime as jdatetime
from datetime import datetime

logger = logging.getLogger(__name__)


def get_jalali_date() -> str:
    """Get Jalali date string"""
    try:
        now = jdatetime.now()
        months = [
            'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
            'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
        ]
        return f"{now.hour:02}:{now.minute:02} - {now.day} {months[now.month - 1]} {now.year}"
    except Exception as e:
        logger.error(f"Error getting Jalali date: {e}")
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
