#!/usr/bin/env python3
"""
Telegram Bot для мониторинга объявлений на Авито
Бот отслеживает новые объявления по категориям и отправляет уведомления пользователям
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Optional
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)
from telegram.error import TelegramError

from database import Database
from avito_parser import AvitoParser
from config import Config

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Состояния для диалогов
CHOOSING_CATEGORY, SETTING_KEYWORDS, SETTING_PRICE = range(3)

class AvitoBot:
    def __init__(self, config: Config):
        self.config = config
        self.db = Database(config.database_url)
        self.parser = AvitoParser()
        self.app = None
        self.monitored_ads = set()  # Для отслеживания уже отправленных объявлений
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Команда /start - приветствие и основное меню"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        # Добавляем пользователя в БД
        await self.db.add_user(user_id, user_name)
        
        keyboard = [
            [InlineKeyboardButton("📌 Подписаться на категорию", callback_data='subscribe')],
            [InlineKeyboardButton("📋 Мои подписки", callback_data='list_subs')],
            [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')],
            [InlineKeyboardButton("❌ Отписаться", callback_data='unsubscribe')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👋 Привет, {user_name}!\n\n"
            "Я помогу тебе найти новые объявления на Авито.\n"
            "Выбери действие ниже 👇",
            reply_markup=reply_markup
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка кнопок меню"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        if query.data == 'subscribe':
            return await self.show_categories(query, context)
        elif query.data == 'list_subs':
            return await self.list_subscriptions(query, context)
        elif query.data == 'settings':
            return await self.show_settings(query, context)
        elif query.data == 'unsubscribe':
            return await self.show_unsubscribe(query, context)
        elif query.data.startswith('cat_'):
            category = query.data.replace('cat_', '')
            await self.db.add_subscription(user_id, category)
            await query.edit_message_text(
                f"✅ Ты подписан на категорию: <b>{category}</b>\n\n"
                "Теперь ты будешь получать уведомления о новых объявлениях!",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        elif query.data.startswith('unsub_'):
            category = query.data.replace('unsub_', '')
            await self.db.remove_subscription(user_id, category)
            await query.edit_message_text(
                f"✅ Ты отписан от категории: <b>{category}</b>",
                parse_mode='HTML'
            )
            return ConversationHandler.END
    
    async def show_categories(self, query, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показывает доступные категории для подписки"""
        categories = [
            ('smartphones', '📱 Смартфоны'),
            ('iphones', '🍎 iPhone'),
            ('android', '🤖 Android'),
            ('gaming', '🎮 Игровые приставки'),
            ('laptops', '💻 Ноутбуки'),
        ]
        
        keyboard = [
            [InlineKeyboardButton(name, callback_data=f'cat_{code}')]
            for code, name in categories
        ]
        keyboard.append([InlineKeyboardButton('◀️ Назад', callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Выбери категорию для подписки:",
            reply_markup=reply_markup
        )
        return CHOOSING_CATEGORY
    
    async def list_subscriptions(self, query, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает текущие подписки пользователя"""
        user_id = query.from_user.id
        subs = await self.db.get_user_subscriptions(user_id)
        
        if not subs:
            text = "У тебя пока нет подписок. Подпишись на интересующие категории!"
        else:
            text = "📋 Твои подписки:\n\n"
            for sub in subs:
                text += f"• {sub['category']} (ключевые слова: {sub.get('keywords', 'нет')})\n"
        
        keyboard = [[InlineKeyboardButton('◀️ Назад', callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    async def show_settings(self, query, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает настройки"""
        keyboard = [
            [InlineKeyboardButton("🔔 Включить уведомления", callback_data='notify_on')],
            [InlineKeyboardButton("🔕 Выключить уведомления", callback_data='notify_off')],
            [InlineKeyboardButton('◀️ Назад', callback_data='back')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ Настройки:\n\n"
            "Управляй уведомлениями здесь",
            reply_markup=reply_markup
        )
    
    async def show_unsubscribe(self, query, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показывает подписки для отписки"""
        user_id = query.from_user.id
        subs = await self.db.get_user_subscriptions(user_id)
        
        if not subs:
            await query.edit_message_text("У тебя нет подписок для отписки")
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton(f"❌ {sub['category']}", callback_data=f"unsub_{sub['category']}")]
            for sub in subs
        ]
        keyboard.append([InlineKeyboardButton('◀️ Назад', callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Выбери категорию для отписки:",
            reply_markup=reply_markup
        )
        return 2
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Команда /help - справка"""
        help_text = (
            "/start - Главное меню\n"
            "/help - Эта справка\n"
            "/subscriptions - Мои подписки\n"
            "/check_now - Проверить новые объявления сейчас\n"
        )
        await update.message.reply_text(help_text)
    
    async def check_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Команда /check_now - проверить объявления сразу"""
        await update.message.reply_text("🔍 Проверяю новые объявления...")
    
    async def monitor_ads(self) -> None:
        """Фоновая задача для мониторинга объявлений"""
        logger.info("🤖 Бот начал мониторинг объявлений")
        
        while True:
            try:
                # Получаем всех пользователей с подписками
                users_subscriptions = await self.db.get_all_subscriptions()
                
                if not users_subscriptions:
                    logger.debug("Нет подписок для проверки")
                    await asyncio.sleep(self.config.check_interval)
                    continue
                
                # Группируем подписки по категориям
                categories_to_check = {}
                for user_id, category, keywords in users_subscriptions:
                    if category not in categories_to_check:
                        categories_to_check[category] = []
                    categories_to_check[category].append((user_id, keywords))
                
                # Проверяем каждую категорию
                for category, users_list in categories_to_check.items():
                    logger.info(f"Проверяю категорию: {category}")
                    
                    try:
                        # Получаем новые объявления
                        ads = await self.parser.get_ads(category)
                        
                        for ad in ads:
                            ad_id = ad.get('id')
                            
                            # Пропускаем уже отправленные
                            if ad_id in self.monitored_ads:
                                continue
                            
                            self.monitored_ads.add(ad_id)
                            
                            # Отправляем уведомления пользователям
                            for user_id, keywords in users_list:
                                # Если установлены ключевые слова, проверяем их
                                if keywords:
                                    if not self._match_keywords(ad, keywords):
                                        continue
                                
                                await self._send_ad_notification(user_id, ad)
                    
                    except Exception as e:
                        logger.error(f"Ошибка при проверке категории {category}: {e}")
                        continue
                
                logger.info(f"✅ Проверка завершена. Следующая проверка через {self.config.check_interval}с")
                await asyncio.sleep(self.config.check_interval)
            
            except Exception as e:
                logger.error(f"❌ Ошибка в мониторе объявлений: {e}")
                await asyncio.sleep(self.config.check_interval)
    
    def _match_keywords(self, ad: dict, keywords: str) -> bool:
        """Проверяет совпадают ли ключевые слова с объявлением"""
        if not keywords:
            return True
        
        ad_text = f"{ad.get('title', '')} {ad.get('description', '')}".lower()
        keywords_list = [k.strip().lower() for k in keywords.split(',')]
        
        return any(keyword in ad_text for keyword in keywords_list)
    
    async def _send_ad_notification(self, user_id: int, ad: dict) -> None:
        """Отправляет уведомление о новом объявлении"""
        try:
            message = (
                f"🎯 <b>Новое объявление!</b>\n\n"
                f"<b>{ad.get('title', 'Без названия')}</b>\n"
                f"💰 Цена: {ad.get('price', 'договорная')}\n"
                f"📍 {ad.get('location', 'не указано')}\n"
                f"🔗 <a href='{ad.get('url', '#')}'>Смотреть объявление</a>\n"
            )
            
            await self.app.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info(f"✅ Уведомление отправлено пользователю {user_id}")
        
        except TelegramError as e:
            logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        logger.error(f"Update {update} caused error {context.error}")
    
    async def initialize(self) -> None:
        """Инициализирует БД"""
        await self.db.init_db()
    
    async def start_bot(self) -> None:
        """Запускает бота"""
        logger.info("🚀 Запускаю Telegram бота...")
        
        # Инициализируем БД
        await self.initialize()
        
        # Создаем приложение
        self.app = Application.builder().token(self.config.telegram_token).build()
        
        # Добавляем обработчики команд
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("check_now", self.check_now))
        
        # Обработчик кнопок
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Обработчик ошибок
        self.app.add_error_handler(self.error_handler)
        
        # Запускаем бота
        async with self.app:
            await self.app.start()
            logger.info("✅ Бот успешно запущен!")
            
            # Запускаем фоновый монитор объявлений
            monitor_task = asyncio.create_task(self.monitor_ads())
            
            # Ждем завершения
            try:
                await asyncio.gather(
                    self.app.updater.start(),
                    monitor_task
                )
            except KeyboardInterrupt:
                logger.info("Бот остановлен")
            finally:
                await self.app.stop()

async def main():
    """Главная функция"""
    config = Config()
    
    # Проверяем наличие токена
    if not config.telegram_token:
        logger.error("❌ ОШИБКА: Не установлена переменная окружения TELEGRAM_TOKEN")
        logger.error("Установи токен: export TELEGRAM_TOKEN='ваш_токен'")
        sys.exit(1)
    
    logger.info("=" * 50)
    logger.info("🤖 Telegram Bot для мониторинга Авито")
    logger.info("=" * 50)
    
    bot = AvitoBot(config)
    await bot.start_bot()

if __name__ == "__main__":
    asyncio.run(main())
    
