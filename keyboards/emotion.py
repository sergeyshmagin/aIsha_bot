from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def emotion_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("😊 Улыбка", callback_data="emotion:smile"))
    markup.add(InlineKeyboardButton("🥲 Трогательно", callback_data="emotion:soft"))
    markup.add(InlineKeyboardButton("🎉 Празднично", callback_data="emotion:celebrate"))
    return markup
