import telebot
from bot.utils.keyboards import main_menu_keyboard
from bot.config import BOT_NAME, ADMIN_USERNAME, COMMUNITY_USERNAME


def register(bot: telebot.TeleBot):

    @bot.message_handler(func=lambda m: m.text == "ℹ️ Bot haqida")
    def about(message):
        text = (
            f"ℹ️ <b>{BOT_NAME} haqida</b>\n\n"
            "📌 <b>Versiya:</b> 1.0.0 Beta\n\n"
            "🎯 <b>Maqsad:</b>\n"
            "Bu bot orqali siz:\n"
            "• 👨‍🏫 O'qituvchilarni topishingiz\n"
            "• 🏫 O'quv markazlarini ko'rishingiz\n"
            "• 🎓 Universitetlar haqida ma'lumot olishingiz mumkin\n\n"
            "🔍 <b>Qidiruv imkoniyatlari:</b>\n"
            "• 🖥️ Online va 🏠 Offline o'qituvchilar\n"
            "• 🏙️ Shahar bo'yicha markazlar\n"
            "• 🇺🇿 Davlat va 🌐 Nodavlat universitetlar\n\n"
            f"📞 <b>Admin:</b> {ADMIN_USERNAME}\n"
            f"📢 <b>Kanal:</b> {COMMUNITY_USERNAME}"
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=main_menu_keyboard())
