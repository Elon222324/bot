import requests
from bs4 import BeautifulSoup
import random
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import logging

# Настройка логгера
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Функция для парсинга цитат
def get_quotes():
    url = 'https://www.forbes.ru/forbeslife/dosug/262327-na-vse-vremena-100-vdokhnovlyayushchikh-tsitat'
    response = requests.get(url)
    
    if response.status_code != 200:
        return "Не удалось подключиться к сайту."
    
    soup = BeautifulSoup(response.text, 'html.parser')
    quotes_elements = soup.find_all('p', class_='ywx5e Q0w8z')
    quotes = [quote.get_text(strip=True) for quote in quotes_elements if quote.find('b')]
    
    return random.choice(quotes) if quotes else "Не удалось найти цитаты."

# Функция для парсинга анекдотов
def get_joke():
    url = 'https://anekdotbar.ru/top-100.html'
    response = requests.get(url)
    
    if response.status_code != 200:
        return "Не удалось подключиться к сайту."
    
    soup = BeautifulSoup(response.text, 'html.parser')
    jokes_elements = soup.find_all('div', class_='tecst')
    jokes = [joke.get_text(strip=True) for joke in jokes_elements if joke.get_text(strip=True)]
    
    return random.choice(jokes) if jokes else "Не удалось найти анекдоты."

# Функция для команды /start, которая сохраняет chat_id
async def start(update, context):
    chat_id = update.message.chat_id  # Получаем chat_id пользователя
    keyboard = [
        [InlineKeyboardButton("Получить цитату", callback_data='get_quote')],
        [InlineKeyboardButton("Получить анекдот", callback_data='get_joke')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Ваш Chat ID: {chat_id}", reply_markup=reply_markup)

    # Сохраняем chat_id для отправки сообщений в будущем
    context.user_data['chat_id'] = chat_id

# Функция для обработки нажатий кнопок
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'get_quote':
        quote = get_quotes()
        await query.message.reply_text(quote)
    elif query.data == 'get_joke':
        joke = get_joke()
        await query.message.reply_text(joke)

# Функция для ежедневной отправки цитаты и анекдота
async def send_daily_message(application):
    for chat_id in application.user_data.keys():
        quote = get_quotes()
        joke = get_joke()
        await application.bot.send_message(chat_id=chat_id, text=f"Цитата дня:\n\n{quote}")
        await application.bot.send_message(chat_id=chat_id, text=f"Анекдот дня:\n\n{joke}")

# Создаем приложение для бота
app = ApplicationBuilder().token('7816271701:AAGTWZ4aJvvzZkdcdjv-jX1cN3NLNzKhMmg').build()

# Настроим планировщик для ежедневной задачи
scheduler = AsyncIOScheduler()

# Устанавливаем московский часовой пояс
moscow_tz = pytz.timezone('Europe/Moscow')

# Ежедневная задача отправки цитат и анекдотов в 9:00 утра по московскому времени
scheduler.add_job(send_daily_message, CronTrigger(hour=9, minute=0, timezone=moscow_tz), args=[app])

# Запускаем планировщик
scheduler.start()

# Обработчик команды /start
app.add_handler(CommandHandler("start", start))

# Обработчик для парсинга цитат и анекдотов
app.add_handler(CallbackQueryHandler(button_handler))

# Запуск бота
app.run_polling()
