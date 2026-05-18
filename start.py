import telebot
from telebot import types
from bot.database.db import register_user
from bot.utils.keyboards import main_menu_keyboard
from bot.config import COMMUNITY_LINK, BOT_NAME


def register(bot: telebot.TeleBot):

    @bot.message_handler(commands=["start"])
    def start(message):
        user = message.from_user
        register_user(user.id, user.username, user.full_name)

        username_display = f"@{user.username}" if user.username else user.first_name

        welcome_kb = types.InlineKeyboardMarkup()
        welcome_kb.add(
            types.InlineKeyboardButton("📢 Kanalga qo'shilish", url=COMMUNITY_LINK)
        )

        bot.send_message(
            message.chat.id,
            f"👋 Salom <b>{username_display}</b>, <b>{BOT_NAME}</b>ga xush kelibsiz!\n\n"
            "📚 Bu bot orqali <b>o'qituvchilar</b>, <b>o'quv markazlari</b> va "
            "<b>universitetlar</b>ni osongina topishingiz mumkin.",
            parse_mode="HTML",
            reply_markup=welcome_kb
        )

        bot.send_message(
            message.chat.id,
            "📌 <b>Asosiy menyu</b>\n\n👇 Quyidagi tugmalardan birini tanlang:",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
