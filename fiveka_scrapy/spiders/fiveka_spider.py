import scrapy
import time
import random
import json
import re
from datetime import datetime
from urllib.parse import urljoin
from fiveka_scrapy.items import FivekaItem


class FivekaSpider(scrapy.Spider):
    name = 'fiveka'
    allowed_domains = ['5ka.ru']
    start_urls = ['https://5ka.ru/catalog']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = 'https://5ka.ru'
        self.categories_parsed = set()
        self.product_urls_parsed = set()

    def parse(self, response):
        """Парсинг категорий"""
        category_links = response.css('a.chakra-link.css-1mjqhey')
        if not category_links:
            category_links = response.css('a[data-qa^="section-category-item-"]')

        for link in category_links:
            category_url = link.css('::attr(href)').get()
            category_name = link.css('p.css-54eu44::text').get() or 'Без названия'

            if category_url:
                full_url = urljoin(self.base_url, category_url)

                if full_url not in self.categories_parsed:
                    self.categories_parsed.add(full_url)

                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_category,
                        meta={'category_name': category_name}
                    )

    def parse_category(self, response):
        """Парсинг товаров в категории"""
        category_name = response.meta.get('category_name', 'Без названия')

        # Парсим товары на текущей странице
        for product_url in self.get_product_links(response):
            if product_url not in self.product_urls_parsed:
                self.product_urls_parsed.add(product_url)

                yield scrapy.Request(
                    url=product_url,
                    callback=self.parse_product,
                    meta={'category_name': category_name}
                )

        # Следующая страница
        next_page = self.find_next_page(response)
        if next_page:
            yield scrapy.Request(
                url=next_page,
                callback=self.parse_category,
                meta={'category_name': category_name}
            )

    def get_product_links(self, response):
        """Извлекает ссылки на товары"""
        links = []

        product_cards = response.css('div[data-qa^="product-card-"]')
        if not product_cards:
            product_cards = response.css('.chakra-stack.css-lovawgy')

        for card in product_cards:
            href = card.css('a[data-qa="product-card-link"]::attr(href)').get()
            if href and '/product/' in href:
                full_url = urljoin(self.base_url, href)
                if full_url not in links:
                    links.append(full_url)

        return links

    def parse_product(self, response):
        """Парсинг страницы товара"""
        item = FivekaItem()
        item['url'] = response.url
        item['category'] = response.meta.get('category_name', 'Без категории')
        item['timestamp'] = datetime.now().isoformat()

        # Артикул
        item['article'] = self.extract_article(response)

        # Название
        item['name'] = response.css('h1[data-qa="product-card-title"]::text').get() or \
                       response.css('h1::text').get() or \
                       response.css('[itemprop="name"]::text').get()

        # Цены
        prices = self.extract_prices(response)
        if prices:
            unique_prices = sorted(list(set(prices)))
            if len(unique_prices) >= 2:
                item['price'] = str(unique_prices[0])
                item['old_price'] = str(unique_prices[1])
            elif len(unique_prices) == 1:
                item['price'] = str(unique_prices[0])

        # Изображения
        item['image_url'] = self.extract_images(response)

        # Описание
        item['description'] = response.css('div.css-19ps4ew::text, div.css-6ua3wa::text').get()

        # Характеристики
        characteristics = self.extract_characteristics(response)
        item['characteristics'] = characteristics

        # Состав
        item['composition'] = self.extract_composition(characteristics)

        # КБЖУ
        item['nutritional_info'] = self.extract_nutritional_info(response, characteristics)

        # Бренд, вес, страна
        if characteristics:
            item['brand'] = characteristics.get('Бренд')
            item['weight'] = characteristics.get('Вес')
            item['country'] = characteristics.get('Страна производства') or characteristics.get('Страна')

        # Рейтинг и отзывы
        item['rating'] = response.css('h2.css-16706lo::text').get()
        reviews_text = response.css('h2.css-w9opm3::text').get()
        if reviews_text:
            numbers = re.findall(r'\d+', reviews_text)
            item['reviews_count'] = numbers[0] if numbers else reviews_text

        yield item

    def extract_article(self, response):
        """Извлекает артикул"""
        # Из JSON-LD
        json_ld_scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        for script in json_ld_scripts:
            try:
                data = json.loads(script)
                if isinstance(data, dict) and 'sku' in data:
                    return str(data['sku'])
                elif isinstance(data, dict) and '@graph' in data:
                    for item_data in data['@graph']:
                        if isinstance(item_data, dict) and 'sku' in item_data:
                            return str(item_data['sku'])
            except:
                continue

        # Из селекторов
        selectors = [
            '[itemprop="sku"]::text',
            '[data-qa="product-sku"]::text',
            'span:contains("Артикул") + span::text',
            'div:contains("Артикул")::text'
        ]

        for selector in selectors:
            article = response.css(selector).get()
            if article:
                return article.strip()

        return None

    def extract_prices(self, response):
        """Извлекает все цены"""
        prices = []

        # Основные селекторы цен
        price_selectors = [
            'meta[itemprop="price"]::attr(content)',
            '[itemprop="priceSpecification"] meta[itemprop="price"]::attr(content)',
            '.product-price::text',
            '.price::text',
            '[data-qa="product-price"]::text'
        ]

        for selector in price_selectors:
            for price in response.css(selector).getall():
                if price:
                    try:
                        clean_price = re.sub(r'[^\d\.]', '', price.replace(',', '.'))
                        if clean_price:
                            price_float = float(clean_price)
                            if price_float > 0:
                                prices.append(price_float)
                    except:
                        continue

        return prices

    def extract_images(self, response):
        """Извлекает изображения"""
        images = []

        main_img = response.css('img[itemprop="image"]::attr(src)').get()
        if main_img:
            images.append(main_img)

        all_images = response.css('img.chakra-image.css-1epf5lq::attr(src)').getall()
        for img in all_images:
            if img and img not in images:
                images.append(img)

        return images if images else None

    def extract_characteristics(self, response):
        """Извлекает характеристики"""
        characteristics = {}

        char_sections = response.css('.chakra-stack.css-o0cdb2, .css-o0cdb2')
        for section in char_sections:
            key = section.css('.css-8696l::text, .css-11ze7cv span::text').get()
            value = section.css('.css-1vhi7o2::text, .css-gai91n span::text').get()
            if key and value:
                characteristics[key.strip()] = value.strip()

        return characteristics if characteristics else None

    def extract_composition(self, characteristics):
        """Извлекает состав из характеристик"""
        if characteristics:
            for key in characteristics:
                if 'состав' in key.lower():
                    return characteristics[key]
        return None

    def extract_nutritional_info(self, response, characteristics):
        """Извлекает КБЖУ"""
        nutritional_info = {}

        # Из блоков КБЖУ
        nutrition_blocks = response.css('.chakra-stack.css-iicxse')
        for block in nutrition_blocks:
            value = block.css('h2.css-1j4x839::text').get()
            label = block.css('p.css-sdw6z7::text').get()
            if value and label:
                nutritional_info[label.strip()] = value.strip().replace(',', '.')

        # Из характеристик
        if not nutritional_info and characteristics:
            nutrition_mapping = {
                'белки': 'белки',
                'жиры': 'жиры',
                'углеводы': 'углеводы',
                'калории': 'калории'
            }

            for key, value in characteristics.items():
                key_lower = key.lower()
                for ru_key in nutrition_mapping:
                    if ru_key in key_lower:
                        nutritional_info[ru_key] = value

        return nutritional_info if nutritional_info else None

    def find_next_page(self, response):
        """Находит следующую страницу"""
        next_selectors = [
            '.pagination .next a::attr(href)',
            'a[rel="next"]::attr(href)',
            '[data-qa="pagination-next"]::attr(href)'
        ]

        for selector in next_selectors:
            next_url = response.css(selector).get()
            if next_url:
                return urljoin(self.base_url, next_url)

        return None