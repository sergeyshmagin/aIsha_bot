from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters
from frontend_bot.keyboards.emotion import emotion_keyboard
from frontend_bot.services.backend_client import send_photo_for_animation
import os
from telebot.types import Message
from frontend_bot.handlers.general import bot

# Временное хранилище фото по user_id
user_photos = {}

@bot.message_handler(content_types=['photo'])
async def handle_photo(message: Message):
    user_id = message.from_user.id
    photo = message.photo[-1]  # самое большое по качеству
    file_info = await bot.get_file(photo.file_id)
    file_path = f"storage/{user_id}_photo.jpg"
    downloaded_file = await bot.download_file(file_info.file_path)
    os.makedirs("storage", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(downloaded_file)
    user_photos[user_id] = file_path
    await bot.send_message(
        message.chat.id,
        "📸 Фото получено! Выберите стиль оживления:",
        reply_markup=emotion_keyboard()
    )

async def handle_emotion_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    emotion = query.data.replace("emotion:", "")
    photo_path = user_photos.get(user_id)

    if not photo_path or not os.path.exists(photo_path):
        await query.edit_message_text("❌ Фото не найдено. Пришли его заново.")
        return

    await query.edit_message_text("🎬 Оживляю фото, подожди немного...")

    try:
        video_path = await send_photo_for_animation(photo_path, emotion)
        await context.bot.send_video(chat_id=user_id, video=open(video_path, "rb"))
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text="❌ Ошибка при оживлении фото.")
        raise e

def register_photo_handlers(app: Application):
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_emotion_choice, pattern="^emotion:"))
