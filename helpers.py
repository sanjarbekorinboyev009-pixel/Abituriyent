import telebot
from telebot import types


def send_media_message(bot, chat_id, text, media_file_id, media_type, reply_markup=None):
    kwargs = {"caption": text, "parse_mode": "HTML", "reply_markup": reply_markup}
    try:
        if media_file_id and media_type == "photo":
            return bot.send_photo(chat_id, media_file_id, **kwargs)
        elif media_file_id and media_type == "video":
            return bot.send_video(chat_id, media_file_id, **kwargs)
        elif media_file_id and media_type == "animation":
            return bot.send_animation(chat_id, media_file_id, **kwargs)
        else:
            return bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=reply_markup)
    except Exception:
        return bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=reply_markup)


def edit_or_send_media(bot, chat_id, message_id, text, media_file_id, media_type, reply_markup=None):
    try:
        if media_file_id and media_type == "photo":
            media = types.InputMediaPhoto(media_file_id, caption=text, parse_mode="HTML")
            bot.edit_message_media(media, chat_id, message_id, reply_markup=reply_markup)
        elif media_file_id and media_type == "video":
            media = types.InputMediaVideo(media_file_id, caption=text, parse_mode="HTML")
            bot.edit_message_media(media, chat_id, message_id, reply_markup=reply_markup)
        elif media_file_id and media_type == "animation":
            media = types.InputMediaAnimation(media_file_id, caption=text, parse_mode="HTML")
            bot.edit_message_media(media, chat_id, message_id, reply_markup=reply_markup)
        else:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=reply_markup)
    except Exception:
        pass


# Foydalanuvchiga FAQAT admin yozgan tavsif (formatlash va havolalar saqlanadi).
# Ism, shahar, fan, ID kabi maydonlar — faqat admin uchun ma'lumot, ko'rinmaydi.

def teacher_text(t):
    return t.get("description") or ""


def center_text(c):
    return c.get("description") or ""


def university_text(u):
    return u.get("description") or ""
