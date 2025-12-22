#!/usr/bin/env python3
"""
Экспорт всех товаров в CSV
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime


def main():
    print("""
    ╔══════════════════════════════════╗
    ║     Экспорт данных 5ka.ru       ║
    ╚══════════════════════════════════╝
    """)

    db_path = 'data/fiveka_products.db'

    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return

    conn = sqlite3.connect(db_path)

    # Получаем последние данные для каждого товара
    query = '''
    WITH latest AS (
        SELECT url, MAX(date_scraped) as latest_date
        FROM products
        GROUP BY url
    )
    SELECT 
        p.name as "Название",
        p.price as "Цена (со скидкой)",
        p.old_price as "Цена (без скидки)",
        p.article as "Артикул",
        p.url as "Ссылка",
        p.category as "Категория",
        p.description as "Описание",
        p.characteristics as "Характеристики",
        p.composition as "Состав",
        p.nutritional_info as "КБЖУ",
        p.image_url as "Изображения",
        p.brand as "Бренд",
        p.weight as "Вес",
        p.country as "Страна",
        p.rating as "Рейтинг",
        p.reviews_count as "Отзывы",
        -- Форматируем дату для Excel (YYYY-MM-DD HH:MM:SS)
        strftime('%Y-%m-%d %H:%M:%S', p.date_scraped) as "Дата сбора"
    FROM products p
    JOIN latest l ON p.url = l.url AND p.date_scraped = l.latest_date
    ORDER BY p.date_scraped DESC
    '''

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("📭 Нет данных")
        return

    print(f"📊 Товаров: {len(df)}")

    # Сохраняем в CSV с правильными настройками для Excel
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'fiveka_products_{current_date}.csv'
    filepath = os.path.join('data', filename)

    # Используем UTF-8-BOM для корректного отображения в Excel
    df.to_csv(filepath, index=False, encoding='utf-8-sig', sep=';', date_format='%Y-%m-%d %H:%M:%S')

    print(f"✅ Сохранено в CSV: {filepath}")

    # Дополнительно создаем XLSX для Excel
    try:
        xlsx_filename = f'fiveka_products_{current_date}.xlsx'
        xlsx_filepath = os.path.join('data', xlsx_filename)
        df.to_excel(xlsx_filepath, index=False)
        print(f"✅ Сохранено в Excel: {xlsx_filepath}")
    except Exception as e:
        print(f"ℹ️  XLSX не сохранен: {e}")


if __name__ == '__main__':
    main()