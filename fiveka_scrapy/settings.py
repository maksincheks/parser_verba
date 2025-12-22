import os
from datetime import datetime

BOT_NAME = 'fiveka_scrapy'

SPIDER_MODULES = ['fiveka_scrapy.spiders']
NEWSPIDER_MODULE = 'fiveka_scrapy.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# Configure a delay for requests
DOWNLOAD_DELAY = 10
RANDOMIZE_DOWNLOAD_DELAY = True

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'fiveka_scrapy.middlewares.FivekaSeleniumMiddleware': 543,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

# Enable or disable extensions
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
}

# Configure item pipelines
ITEM_PIPELINES = {
    'fiveka_scrapy.pipelines.FivekaPipeline': 300,
}

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = False

# Logging
LOG_LEVEL = 'INFO'
os.makedirs('logs', exist_ok=True)
LOG_FILE = f'logs/fiveka_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

# Feeds
FEEDS = {
    f'data/products_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json': {
        'format': 'json',
        'encoding': 'utf8',
        'indent': 2,
        'overwrite': True,
        'ensure_ascii': False,
    },
}

# Настройки Selenium
SELENIUM_HEADLESS = False  # True для продакшена, False для отладки
SELENIUM_WINDOW_SIZE = '1920,1080'
SELENIUM_PAGE_LOAD_TIMEOUT = 30
SELENIUM_IMPLICIT_WAIT = 10

# Настройки сайта
BASE_URL = 'https://5ka.ru'
START_URLS = ['https://5ka.ru/catalog']

# User-Agents для ротации
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

# Настройки парсинга
PARSE_CATEGORIES = True  # Парсить категории
MAX_CATEGORIES = None    # Ограничить количество категорий (None - все)
MAX_PAGES_PER_CATEGORY = 10  # Максимальное количество страниц на категорию