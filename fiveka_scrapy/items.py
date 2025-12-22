import scrapy


class FivekaItem(scrapy.Item):
    # Основная информация
    name = scrapy.Field()
    price = scrapy.Field()
    old_price = scrapy.Field()
    discount = scrapy.Field()

    # Ссылки
    url = scrapy.Field()
    image_url = scrapy.Field()

    # Идентификаторы
    product_id = scrapy.Field()
    article = scrapy.Field()  # Только артикул, без SKU

    # Категории
    category = scrapy.Field()
    subcategory = scrapy.Field()
    category_path = scrapy.Field()  # Полный путь категорий

    # Описание
    description = scrapy.Field()
    characteristics = scrapy.Field()
    composition = scrapy.Field()  # Состав
    nutritional_info = scrapy.Field()  # КБЖУ

    # Рейтинги и отзывы
    rating = scrapy.Field()
    reviews_count = scrapy.Field()

    # Статус
    in_stock = scrapy.Field()
    availability = scrapy.Field()

    # Дополнительно
    brand = scrapy.Field()
    weight = scrapy.Field()
    country = scrapy.Field()

    # Метаданные
    timestamp = scrapy.Field()
    source_url = scrapy.Field()
    page_number = scrapy.Field()
    date_scraped = scrapy.Field()  # Дата парсинга в формате ISO 8601