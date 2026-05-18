import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import telebot
from bot.config import BOT_TOKEN, BOT_NAME
from bot.database.db import init_db
from bot.handlers import start, about, teachers, centers, universities, admin


def main():
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN topilmadi!")
        sys.exit(1)

    init_db()
    print("✅ Ma'lumotlar bazasi tayyor.")

    bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

    start.register(bot)
    about.register(bot)
    teachers.register(bot)
    centers.register(bot)
    universities.register(bot)
    admin.register(bot)

    print(f"🚀 {BOT_NAME} ishga tushdi...")

    bot.infinity_polling(timeout=60, long_polling_timeout=60)


if __name__ == "__main__":
    main()
