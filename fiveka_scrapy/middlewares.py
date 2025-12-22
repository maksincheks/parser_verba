import time
import random
import logging
from typing import Optional
from scrapy import signals
from scrapy.http import HtmlResponse, Request
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from undetected_chromedriver import Chrome
from undetected_chromedriver.options import ChromeOptions as Options

logger = logging.getLogger(__name__)


class FivekaSeleniumMiddleware:
    """Упрощенный Selenium Middleware."""

    def __init__(self, settings):
        self.settings = settings
        self.driver: Optional[Chrome] = None

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler.settings)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def init_driver(self):
        """Инициализация драйвера."""
        if self.driver:
            return

        try:
            logger.info("🚀 Инициализация Chrome драйвера...")

            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")

            window_size = self.settings.get("SELENIUM_WINDOW_SIZE", "1920,1080")
            options.add_argument(f"--window-size={window_size}")

            if self.settings.getbool("SELENIUM_HEADLESS", False):
                options.add_argument("--headless=new")

            self.driver = Chrome(options=options)
            self.driver.set_page_load_timeout(30)

            logger.info("Chrome драйвер инициализирован")

        except Exception as e:
            logger.error(f"Ошибка инициализации драйвера: {e}")
            raise

    def process_request(self, request, spider):
        """Обработка запроса через Selenium."""
        if not self.driver:
            self.init_driver()

        logger.info(f"Загружаю: {request.url}")

        try:
            self.driver.get(request.url)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            time.sleep(2)
            self.scroll_page()

            html = self.driver.page_source
            return HtmlResponse(
                url=request.url,
                body=html.encode("utf-8"),
                encoding="utf-8",
                request=request,
            )

        except TimeoutException:
            logger.error(f"Таймаут при загрузке {request.url}")
            return HtmlResponse(url=request.url, status=408, request=request)
        except Exception as e:
            logger.error(f"Ошибка загрузки {request.url}: {e}")
            return HtmlResponse(
                url=request.url,
                status=500,
                body=str(e).encode("utf-8"),
                request=request,
            )

    def scroll_page(self):
        """Простая прокрутка страницы."""
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 300)")
            time.sleep(0.5)
        except Exception as e:
            logger.debug(f"Ошибка прокрутки: {e}")

    def spider_closed(self, spider):
        """Закрытие драйвера."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Драйвер закрыт")
            except Exception as e:
                logger.error(f"Ошибка закрытия драйвера: {e}")