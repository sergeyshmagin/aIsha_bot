import os
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Загрузка переменных окружения из .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = AsyncTeleBot(TELEGRAM_TOKEN)


def main_menu_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("❓ Помощь"))
    return markup


@bot.message_handler(commands=['start'])
async def start(message):
    await bot.send_message(
        message.chat.id,
        (
            "👋 Привет! Я помогу оживить твои фотографии — придай им эмоции, голос и "
            "волшебство.\n\nВыбери, что хочешь сделать:"
        ),
        reply_markup=main_menu_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
async def help_handler(message):
    await bot.send_message(
        message.chat.id,
        (
            "❓ Справка:\n\n"
            "📸 Оживить фото — добавь эмоции на лице\n"
            "🗣 Сделать говорящим — напиши текст, и фото 'скажет' его\n"
            "🎁 Видео-поздравление — оживлённое поздравление в видеоформате\n\n"
            "Просто отправь фото или нажми кнопку 👇"
        ),
        reply_markup=main_menu_keyboard()
    )

# Для запуска используйте:
# import asyncio
# asyncio.run(bot.polling())
