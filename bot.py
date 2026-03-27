import sqlite3
import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Берем токен из переменной окружения (безопасно!)
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Путь к базе данных
DB_PATH = "/tmp/messages.db"

def create_database():
    """Создает таблицу для сообщений, если её нет"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            chat_name TEXT,
            message_id INTEGER,
            user_id INTEGER,
            user_name TEXT,
            text TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ База данных готова!")

async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет каждое новое сообщение в базу данных"""
    # Игнорируем свои же сообщения
    if update.effective_user and update.effective_user.id == context.bot.id:
        return
    
    msg = update.effective_message
    if not msg:
        return
    
    # Собираем данные о сообщении
    chat_id = msg.chat_id
    chat_name = msg.chat.title or msg.chat.first_name or "Личный чат"
    message_id = msg.message_id
    user_id = msg.from_user.id if msg.from_user else None
    user_name = msg.from_user.username if msg.from_user else "Неизвестно"
    
    # Получаем текст (или подпись к медиа)
    if msg.text:
        text = msg.text
    elif msg.caption:
        text = msg.caption
    else:
        text = "[Медиафайл]"
    
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Сохраняем в базу
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO saved_messages (chat_id, chat_name, message_id, user_id, user_name, text, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (chat_id, chat_name, message_id, user_id, user_name, text, date))
    conn.commit()
    conn.close()
    
    print(f"[{date}] 💾 Сохранено от @{user_name}: {text[:50]}...")

async def main():
    """Запуск бота"""
    if not TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL, save_message))
    
    print("🤖 Бот запущен и готов к работе!")
    print("📨 Добавь бота в чат, и он начнёт сохранять все сообщения")
    print("💾 Сохранённые сообщения хранятся в /tmp/messages.db")
    
    await application.run_polling()

if __name__ == '__main__':
    create_database()
    asyncio.run(main())
