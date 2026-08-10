"""
Конфигурация для Telegram бота
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    telegram_token = os.getenv('TELEGRAM_TOKEN', '')
    
    # База данных
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/avito_bot'
    )
    
    # Интервал проверки объявлений (в секундах)
    check_interval = int(os.getenv('CHECK_INTERVAL', '300'))  # 5 минут по умолчанию
    
    # Логирование
    log_level = os.getenv('LOG_LEVEL', 'INFO')
