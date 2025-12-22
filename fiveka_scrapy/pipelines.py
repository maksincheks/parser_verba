import sqlite3
import os
import json
from datetime import datetime


class FivekaPipeline:
    """Pipeline для записи в SQLite базу"""

    def open_spider(self, spider):
        """Создаем базу при запуске"""
        if not os.path.exists('data'):
            os.makedirs('data')

        self.db_path = 'data/fiveka_products.db'
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """Создаем таблицу"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                price REAL,
                old_price REAL,
                article TEXT,
                url TEXT UNIQUE,
                category TEXT,
                description TEXT,
                characteristics TEXT,
                composition TEXT,
                nutritional_info TEXT,
                image_url TEXT,
                brand TEXT,
                weight TEXT,
                country TEXT,
                rating REAL,
                reviews_count INTEGER,
                date_scraped TEXT,
                timestamp TEXT
            )
        ''')
        self.conn.commit()

    def close_spider(self, spider):
        """Закрываем соединение"""
        if hasattr(self, 'conn'):
            self.conn.close()

    def process_item(self, item, spider):
        """Сохраняем товар в базу"""
        try:
            # Добавляем дату парсинга
            item['date_scraped'] = datetime.now().isoformat()

            # Преобразуем в JSON
            for field in ['characteristics', 'nutritional_info']:
                if item.get(field) and isinstance(item[field], dict):
                    item[field] = json.dumps(item[field], ensure_ascii=False)

            if item.get('image_url') and isinstance(item['image_url'], list):
                item['image_url'] = json.dumps(item['image_url'], ensure_ascii=False)

            # Вставляем данные
            self.cursor.execute('''
                INSERT OR REPLACE INTO products 
                (name, price, old_price, article, url, category, description, 
                 characteristics, composition, nutritional_info, image_url, 
                 brand, weight, country, rating, reviews_count, date_scraped, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.get('name'),
                item.get('price'),
                item.get('old_price'),
                item.get('article'),
                item.get('url'),
                item.get('category'),
                item.get('description'),
                item.get('characteristics'),
                item.get('composition'),
                item.get('nutritional_info'),
                item.get('image_url'),
                item.get('brand'),
                item.get('weight'),
                item.get('country'),
                item.get('rating'),
                item.get('reviews_count'),
                item.get('date_scraped'),
                item.get('timestamp')
            ))

            self.conn.commit()

        except Exception as e:
            spider.logger.error(f"Ошибка сохранения: {e}")
            self.conn.rollback()

        return item