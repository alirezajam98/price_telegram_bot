import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class PriceFormatter:
    @staticmethod
    def format_price(price_text: str, is_rial: bool = True) -> str:
        """Format price text"""
        try:
            if price_text is None:
                return "نامشخص"

            clean_price = ''.join(c for c in price_text if c.isdigit() or c == '.' or c == ',')
            clean_price = clean_price.replace(',', '')

            if '.' in clean_price:
                formatted = f"{float(clean_price):,.2f}"
            else:
                formatted = f"{int(clean_price):,}"

            return f"{formatted} ریال" if is_rial else formatted
        except Exception as e:
            logger.error(f"Price format error: {e}")
            return price_text

    @staticmethod
    def extract_change_values(change_text: str) -> Tuple[str, str]:
        """Extract percentage and amount from change text"""
        try:
            if change_text is None:
                return "0%", "0"

            change_text = change_text.strip()
            patterns = [
                r'\(([+-]?[\d.]+)%\)\s*([+-]?[\d,.]+)',
                r'([+-]?[\d,.]+)\s*\(([+-]?[\d.]+)%\)',
                r'([+-]?[\d.]+)%',
                r'([+-]?[\d,.]+)'
            ]

            for pattern in patterns:
                match = re.search(pattern, change_text)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        return f"{groups[0]}%", groups[1].replace(',', '')
                    return f"{groups[0]}%", "0" if '%' in groups[0] else groups[0].replace(',', '')

            return "0%", "0"
        except Exception as e:
            logger.error(f"Change extraction error: {e}")
            return "0%", "0"

    @staticmethod
    def convert_to_toman(price_str: str) -> str:
        """Convert price from Rial to Toman"""
        try:
            if isinstance(price_str, (str, int, float)):
                if isinstance(price_str, str):
                    price_num = int(''.join(c for c in price_str if c.isdigit()))
                else:
                    price_num = int(price_str)

                toman_value = price_num // 10
                return "{:,}".format(toman_value)
            return str(price_str)
        except Exception as e:
            logger.error(f"Toman conversion error: {e}")
            return str(price_str)