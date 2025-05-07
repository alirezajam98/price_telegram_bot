import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TgjuScraper:
    async def get_tgju_data(self) -> Optional[Dict]:
        """Get data from TGJU website"""
        url = "https://www.tgju.org"
        try:
            logger.info("Starting data retrieval from tgju")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                logger.info(f"Navigating to {url}")
                await page.goto(url, timeout=30000)

                logger.info("Waiting for page to load...")
                await page.wait_for_selector('li[id^="l-"]', timeout=10000)
                await page.wait_for_timeout(5000)

                html = await page.content()
                logger.info(f"HTML received (length: {len(html)})")
                await browser.close()

            return self._parse_html(html)
        except Exception as e:
            logger.error(f"Error in get_tgju_data: {e}")
            return None

    def _parse_html(self, html: str) -> Dict:
        """Parse HTML and extract data"""
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
            element = soup.find('li', {'id': f'l-{element_id}'})
            if not element:
                continue

            li_classes = element.get('class', [])
            price_element = element.find('span', class_='info-price')
            change_element = element.find('span', class_='info-change')

            price_text = price_element.text.strip() if price_element else "0"
            change_text = change_element.text.strip() if change_element else "(0%)"
            trend = 'low' if 'low' in li_classes else 'high' if 'high' in li_classes else 'neutral'

            data[key] = {
                'name': name,
                'price': price_text,
                'change': change_text,
                'trend': trend
            }

        return data