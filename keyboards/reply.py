from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def error_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для ошибок с кнопками Повторить и Главное меню."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Повторить"))
    markup.add(KeyboardButton("Главное меню"))
    return markup


def back_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой Назад."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Назад"))
    return markup


def transcript_format_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора формата транскрипта."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Полный официальный транскрипт"))
    markup.add(KeyboardButton("Сводка на 1 страницу"))
    markup.add(KeyboardButton("Сформировать MoM"))
    markup.add(KeyboardButton("Сформировать ToDo-план с чеклистами"))
    markup.add(KeyboardButton("Протокол заседания (Word)"))
    markup.add(KeyboardButton("ℹ️ О форматах"))
    markup.add(KeyboardButton("Назад"))
    return markup


def history_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для истории файлов пользователя."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🗑 Удалить мой файл"))
    markup.add(KeyboardButton("Назад"))
    return markup


def business_assistant_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для меню 'Бизнес-ассистент'."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🎤 Аудио"))
    markup.add(KeyboardButton("📄 Текстовый транскрипт"))
    markup.add(KeyboardButton("Назад"))
    return markup


def photo_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для меню 'Работа с фото'."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📸 Оживить фото"))
    markup.add(KeyboardButton("🗣 Говорящее фото"))
    markup.add(KeyboardButton("🎁 Видео-поздравление"))
    markup.add(KeyboardButton("Назад"))
    return markup 