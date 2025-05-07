import pytest
from services.scraper import TgjuScraper
from bs4 import BeautifulSoup

@pytest.mark.asyncio
async def test_get_market_data():
    scraper = TgjuScraper()
    data = await scraper.get_market_data()
    assert data is not None
    assert isinstance(data, dict)
    assert 'dollar' in data