#!/usr/bin/env python3
import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def main():
    # Добавляем путь к проекту
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Устанавливаем переменную окружения
    os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'fiveka_scrapy.settings')

    # Получаем настройки
    settings = get_project_settings()

    # Создаем процесс
    process = CrawlerProcess(settings)

    print("""
    ╔══════════════════════════════════════════════╗
    ║          ПАРСЕР 5KA.RU                       ║
    ╚══════════════════════════════════════════════╝

    Особенности:
    ✅ Selenium с ручным драйвером
    ✅ Сохранение в SQLite базу данных
    ✅ Автоматическая пагинация
    ✅ Дата парсинга в формате ISO 8601

    Данные сохраняются в:
    • data/fiveka_products.db - база данных
    • data/products_*.json - JSON файлы
    • logs/ - логи работы

    Для анализа данных используйте:
    • python analyze_prices.py - анализ изменения цен
    • python read_database.py - чтение базы данных

    Запускаю...
    """)

    # Запускаем паука
    process.crawl('fiveka')
    process.start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПарсер остановлен пользователем")
    except Exception as e:
        print(f"\nОшибка запуска: {e}")
        import traceback

        traceback.print_exc()