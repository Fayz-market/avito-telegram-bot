"""
Парсер объявлений Авито (демонстрационная версия)
В реальном проекте нужно использовать официальный API или более сложный парсинг
"""

import logging
import asyncio
from typing import List, Dict
import aiohttp
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class AvitoParser:
    """
    Парсер объявлений с Авито
    
    ВАЖНО: Это демонстрационная реализация!
    Авито активно блокирует веб-скрепинг.
    Для реального использования:
    1. Используй официальный Avito API (если есть доступ)
    2. Используй прокси-сервисы
    3. Добавь задержки между запросами
    4. Используй User-Agent rotation
    """
    
    CATEGORIES = {
        'smartphones': 'https://www.avito.ru/sankt-peterburg/telefony',
        'iphones': 'https://www.avito.ru/sankt-peterburg/iphone',
        'android': 'https://www.avito.ru/sankt-peterburg/android',
        'gaming': 'https://www.avito.ru/sankt-peterburg/igrovyie_pristavki',
        'laptops': 'https://www.avito.ru/sankt-peterburg/noutbuki',
    }
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    ]
    
    def __init__(self):
        self.session = None
        self.mock_counter = 0
    
    async def get_ads(self, category: str) -> List[Dict]:
        """
        Получает объявления по категории
        
        ДЕМО ВЕРСИЯ: Возвращает тестовые данные
        В реальной версии здесь будет парсинг Авито
        """
        logger.info(f"Получаю объявления для категории: {category}")
        
        try:
            # ДЕМОНСТРАЦИОННЫЕ ДАННЫЕ для тестирования
            mock_ads = self._get_mock_ads(category)
            return mock_ads
        
        except Exception as e:
            logger.error(f"Ошибка при получении объявлений: {e}")
            return []
    
    def _get_mock_ads(self, category: str) -> List[Dict]:
        """
        Возвращает тестовые объявления для демонстрации
        В реальном проекте здесь будет реальный парсинг
        """
        self.mock_counter += 1
        
        mock_data = {
            'smartphones': [
                {
                    'id': f'phone_{self.mock_counter}_1',
                    'title': 'Samsung Galaxy S24 новый',
                    'price': 45000,
                    'location': 'Санкт-Петербург',
                    'url': 'https://www.avito.ru/sankt-peterburg/telefony/samsung',
                    'description': 'Новый смартфон Samsung Galaxy S24',
                    'date': datetime.now().isoformat()
                },
                {
                    'id': f'phone_{self.mock_counter}_2',
                    'title': 'OnePlus 12 отличное состояние',
                    'price': 38000,
                    'location': 'Санкт-Петербург',
                    'url': 'https://www.avito.ru/sankt-peterburg/telefony/oneplus',
                    'description': 'OnePlus 12 в отличном состоянии',
                    'date': datetime.now().isoformat()
                },
            ],
            'iphones': [
                {
                    'id': f'iphone_{self.mock_counter}_1',
                    'title': 'iPhone 15 Pro Max',
                    'price': 95000,
                    'location': 'Санкт-Петербург',
                    'url': 'https://www.avito.ru/sankt-peterburg/iphone',
                    'description': 'iPhone 15 Pro Max 256GB',
                    'date': datetime.now().isoformat()
                },
            ],
            'android': [
                {
                    'id': f'android_{self.mock_counter}_1',
                    'title': 'Google Pixel 8 Pro',
                    'price': 72000,
                    'location': 'Санкт-Петербург',
                    'url': 'https://www.avito.ru/sankt-peterburg/android',
                    'description': 'Google Pixel 8 Pro новый',
                    'date': datetime.now().isoformat()
                },
            ],
            'gaming': [
                {
                    'id': f'gaming_{self.mock_counter}_1',
                    'title': 'PlayStation 5',
                    'price': 35000,
                    'location': 'Санкт-Петербург',
                    'url': 'https://www.avito.ru/sankt-peterburg/igrovyie_pristavki',
                    'description': 'PS5 с играми',
                    'date': datetime.now().isoformat()
                },
                {
                    'id': f'gaming_{self.mock_counter}_2',
                    'title': 'Xbox Series X',
                    'price': 30000,
                    'location': 'Санкт-Петербург',
                    'url': 'https://www.avito.ru/sankt-peterburg/igrovyie_pristavki',
                    'description': 'Xbox Series X с Game Pass',
                    'date': datetime.now().isoformat()
                },
            ],
            'laptops': [
                {
                    'id': f'laptop_{self.mock_counter}_1',
                    'title': 'MacBook Pro 16 M3',
                    'price': 185000,
                    'location': 'Санкт-Петербург',
                    'url': 'https://www.avito.ru/sankt-peterburg/noutbuki',
                    'description': 'MacBook Pro 16 с процессором M3',
                    'date': datetime.now().isoformat()
                },
                {
                    'id': f'laptop_{self.mock_counter}_2',
                    'title': 'ASUS ROG Gaming laptop',
                    'price': 95000,
                    'location': 'Санкт-Петербург',
                    'url': 'https://www.avito.ru/sankt-peterburg/noutbuki',
                    'description': 'Мощный игровой ноутбук ASUS ROG',
                    'date': datetime.now().isoformat()
                },
            ],
        }
        
        return mock_data.get(category, [])
    
    async def parse_real_avito(self, category: str) -> List[Dict]:
        """
        Реальный парсинг Авито (требует решения проблемы с блокировками)
        
        ВАЖНО: Это просто skeleton для будущей реализации
        """
        logger.warning(f"⚠️ Реальный парсинг Авито требует дополнительной конфигурации")
        logger.warning("Используются демонстрационные данные")
        
        # Здесь должен быть код для:
        # 1. Использования прокси
        # 2. Добавления правильных User-Agent
        # 3. Обработки Cloudflare защиты
        # 4. Парсинга HTML с BeautifulSoup
        
        return []
    
    async def close(self) -> None:
        """Закрывает сессию"""
        if self.session:
            await self.session.close()
