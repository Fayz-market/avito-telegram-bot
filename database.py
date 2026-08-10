"""
Работа с базой данных PostgreSQL
"""

import logging
from typing import List, Optional, Tuple
import asyncpg
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def init_db(self) -> None:
        """Инициализирует подключение к БД и создает таблицы"""
        try:
            # Создаем пул подключений
            self.pool = await asyncpg.create_pool(self.database_url)
            logger.info("✅ Подключение к БД установлено")
            
            # Создаем таблицы
            async with self.pool.acquire() as connection:
                await connection.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        first_name VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notifications_enabled BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                await connection.execute('''
                    CREATE TABLE IF NOT EXISTS subscriptions (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                        category VARCHAR(100),
                        keywords TEXT,
                        min_price INTEGER DEFAULT 0,
                        max_price INTEGER DEFAULT 999999999,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, category)
                    )
                ''')
                
                await connection.execute('''
                    CREATE TABLE IF NOT EXISTS processed_ads (
                        ad_id VARCHAR(255) PRIMARY KEY,
                        category VARCHAR(100),
                        title TEXT,
                        price INTEGER,
                        url TEXT,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                logger.info("✅ Таблицы БД созданы/обновлены")
        
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    async def add_user(self, user_id: int, first_name: str) -> None:
        """Добавляет пользователя в БД"""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute('''
                    INSERT INTO users (user_id, first_name)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id) DO NOTHING
                ''', user_id, first_name)
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя: {e}")
    
    async def add_subscription(self, user_id: int, category: str, keywords: str = '') -> None:
        """Добавляет подписку пользователя"""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute('''
                    INSERT INTO subscriptions (user_id, category, keywords)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id, category) 
                    DO UPDATE SET keywords = $3
                ''', user_id, category, keywords)
                logger.info(f"✅ Подписка добавлена: user_id={user_id}, category={category}")
        except Exception as e:
            logger.error(f"Ошибка при добавлении подписки: {e}")
    
    async def remove_subscription(self, user_id: int, category: str) -> None:
        """Удаляет подписку пользователя"""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute('''
                    DELETE FROM subscriptions
                    WHERE user_id = $1 AND category = $2
                ''', user_id, category)
                logger.info(f"✅ Подписка удалена: user_id={user_id}, category={category}")
        except Exception as e:
            logger.error(f"Ошибка при удалении подписки: {e}")
    
    async def get_user_subscriptions(self, user_id: int) -> List[dict]:
        """Получает подписки пользователя"""
        try:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch('''
                    SELECT category, keywords, min_price, max_price
                    FROM subscriptions
                    WHERE user_id = $1
                ''', user_id)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка при получении подписок: {e}")
            return []
    
    async def get_all_subscriptions(self) -> List[Tuple[int, str, str]]:
        """Получает все подписки всех пользователей"""
        try:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch('''
                    SELECT user_id, category, keywords
                    FROM subscriptions
                    WHERE user_id IN (
                        SELECT user_id FROM users 
                        WHERE notifications_enabled = TRUE
                    )
                ''')
                return [(row['user_id'], row['category'], row['keywords'] or '') for row in rows]
        except Exception as e:
            logger.error(f"Ошибка при получении всех подписок: {e}")
            return []
    
    async def mark_ad_processed(self, ad_id: str, category: str, title: str, 
                               price: int, url: str) -> None:
        """Отмечает объявление как обработанное"""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute('''
                    INSERT INTO processed_ads (ad_id, category, title, price, url)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (ad_id) DO NOTHING
                ''', ad_id, category, title, price, url)
        except Exception as e:
            logger.error(f"Ошибка при отметке объявления: {e}")
    
    async def close(self) -> None:
        """Закрывает подключение к БД"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ Подключение к БД закрыто")
