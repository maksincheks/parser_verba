#!/usr/bin/env python3
"""
Анализ цен и рейтингов 5ka.ru
"""

import sqlite3
import pandas as pd
import os
import json
from datetime import datetime
import numpy as np


def clean_rating(rating_str):
    """Очищает рейтинг от запятых и преобразует в float"""
    if pd.isna(rating_str):
        return np.nan

    try:
        # Если это уже число
        if isinstance(rating_str, (int, float)):
            return float(rating_str)

        # Если строка
        rating_str = str(rating_str).strip()
        if not rating_str:
            return np.nan

        # Заменяем запятую на точку
        rating_str = rating_str.replace(',', '.')

        # Убираем все не-цифры и не точки
        import re
        rating_str = re.sub(r'[^\d\.]', '', rating_str)

        if rating_str:
            return float(rating_str)
        else:
            return np.nan
    except:
        return np.nan


def clean_price(price_str):
    """Очищает цену"""
    if pd.isna(price_str):
        return np.nan

    try:
        if isinstance(price_str, (int, float)):
            return float(price_str)

        price_str = str(price_str).strip()
        if not price_str:
            return np.nan

        # Убираем пробелы и заменяем запятые
        price_str = price_str.replace(' ', '').replace(',', '.')

        # Убираем все кроме цифр и точки
        import re
        price_str = re.sub(r'[^\d\.]', '', price_str)

        if price_str:
            return float(price_str)
        else:
            return np.nan
    except:
        return np.nan


def main():
    print("""
    ╔══════════════════════════════════╗
    ║     Анализ цен 5ka.ru           ║
    ╚══════════════════════════════════╝
    """)

    db_path = 'data/fiveka_products.db'

    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return

    conn = sqlite3.connect(db_path)

    # Получаем все записи
    query = '''
    SELECT 
        name,
        price,
        old_price,
        article,
        url,
        category,
        rating,
        reviews_count,
        date_scraped
    FROM products
    ORDER BY date_scraped DESC
    '''

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("📭 Нет данных")
        return

    print(f"📊 Всего записей в базе: {len(df)}")

    # Очищаем данные
    df_clean = df.copy()

    # Очищаем рейтинги
    print("🔄 Очистка рейтингов...")
    df_clean['rating_clean'] = df_clean['rating'].apply(clean_rating)

    # Очищаем цены
    print("🔄 Очистка цен...")
    df_clean['price_clean'] = df_clean['price'].apply(clean_price)
    df_clean['old_price_clean'] = df_clean['old_price'].apply(clean_price)

    # Рассчитываем скидки - используем float
    df_clean['discount_percent'] = np.nan
    mask = (df_clean['old_price_clean'].notna()) & (df_clean['price_clean'].notna())
    df_clean.loc[mask, 'discount_percent'] = ((df_clean.loc[mask, 'old_price_clean'] -
                                               df_clean.loc[mask, 'price_clean']) /
                                              df_clean.loc[mask, 'old_price_clean'] * 100)

    # Преобразуем в числовой тип
    df_clean['discount_percent'] = pd.to_numeric(df_clean['discount_percent'], errors='coerce')

    # Статистика
    print("\n📈 СТАТИСТИКА:")
    print(f"   Всего товаров: {len(df_clean)}")

    # Товары с рейтингом
    rated = df_clean[df_clean['rating_clean'].notna()]
    print(f"   Товаров с рейтингом: {len(rated)} ({len(rated) / len(df_clean) * 100:.1f}%)")
    if len(rated) > 0:
        print(f"   Средний рейтинг: {rated['rating_clean'].mean():.2f}")
        print(f"   Максимальный рейтинг: {rated['rating_clean'].max():.2f}")
        print(f"   Минимальный рейтинг: {rated['rating_clean'].min():.2f}")

    # Товары со скидкой
    discounted = df_clean[df_clean['discount_percent'].notna()]
    print(f"   Товаров со скидкой: {len(discounted)} ({len(discounted) / len(df_clean) * 100:.1f}%)")
    if len(discounted) > 0:
        print(f"   Средняя скидка: {discounted['discount_percent'].mean():.1f}%")
        print(f"   Максимальная скидка: {discounted['discount_percent'].max():.1f}%")

    # Цены
    priced = df_clean[df_clean['price_clean'].notna()]
    if len(priced) > 0:
        print(f"   Средняя цена: {priced['price_clean'].mean():.2f} руб.")
        print(f"   Максимальная цена: {priced['price_clean'].max():.2f} руб.")
        print(f"   Минимальная цена: {priced['price_clean'].min():.2f} руб.")

    # Топ категорий
    print(f"\n🏷️  ТОП КАТЕГОРИЙ (по количеству товаров):")
    top_categories = df_clean['category'].value_counts().head(10)
    for cat, count in top_categories.items():
        print(f"   {cat}: {count} товаров")

    # Топ товаров по рейтингу
    if len(rated) > 0:
        print(f"\n🏆 ТОП ТОВАРОВ ПО РЕЙТИНГУ:")
        top_rated = rated.nlargest(10, 'rating_clean')[['name', 'rating_clean', 'price_clean', 'category']]
        for idx, row in top_rated.iterrows():
            price = f"{row['price_clean']:.2f} руб." if pd.notna(row['price_clean']) else "Нет цены"
            print(f"   {row['name'][:50]}... - {row['rating_clean']:.2f} ⭐ ({price})")

    # Топ товаров по скидке (с проверкой)
    if len(discounted) > 0:
        print(f"\n💰 ТОП ТОВАРОВ ПО СКИДКЕ:")
        # Убедимся, что discount_percent числовой
        discounted_sorted = discounted.sort_values('discount_percent', ascending=False)
        top_discounts = discounted_sorted.head(10)[['name', 'discount_percent', 'old_price_clean', 'price_clean']]

        for idx, row in top_discounts.iterrows():
            old_price = f"{row['old_price_clean']:.2f}" if pd.notna(row['old_price_clean']) else "?"
            new_price = f"{row['price_clean']:.2f}" if pd.notna(row['price_clean']) else "?"
            discount_val = row['discount_percent']
            if pd.notna(discount_val):
                print(f"   {row['name'][:50]}... - {discount_val:.1f}% ({old_price} → {new_price} руб.)")

    # Сохраняем очищенные данные
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join('data', f'analysis_report_{current_date}.csv')

    # Готовим данные для экспорта
    export_df = df_clean[[
        'name', 'category', 'article', 'price_clean',
        'old_price_clean', 'discount_percent', 'rating_clean',
        'reviews_count', 'url', 'date_scraped'
    ]].copy()

    export_df.columns = [
        'Название', 'Категория', 'Артикул', 'Цена',
        'Старая цена', 'Скидка %', 'Рейтинг',
        'Количество отзывов', 'Ссылка', 'Дата сбора'
    ]

    export_df.to_csv(output_file, index=False, encoding='utf-8-sig', sep=';')
    print(f"\n✅ Отчет сохранен: {output_file}")


if __name__ == '__main__':
    main()