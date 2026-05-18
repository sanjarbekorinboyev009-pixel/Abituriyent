import telebot
from bot.database.db import get_universities, update_user_activity, increment_views
from bot.utils.keyboards import university_type_keyboard, pagination_keyboard
from bot.utils.helpers import send_media_message, edit_or_send_media, university_text

user_state = {}


def register(bot: telebot.TeleBot):

    @bot.message_handler(func=lambda m: m.text == "🎓 Universitetlar")
    def find_uni(message):
        update_user_activity(message.from_user.id)
        user_state.pop(message.from_user.id, None)
        bot.send_message(
            message.chat.id,
            "🎓 <b>Universitetlar</b>\n\n🏛️ Turini tanlang:",
            parse_mode="HTML",
            reply_markup=university_type_keyboard()
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("utype:"))
    def on_uni_type(call):
        uni_type = call.data.split(":", 1)[1]
        uid = call.from_user.id
        unis = get_universities(uni_type=uni_type)
        if not unis:
            bot.answer_callback_query(call.id, f"😔 {uni_type} universitetlar topilmadi!", show_alert=True)
            return
        user_state[uid] = {"unis": unis, "u_index": 0, "uni_type": uni_type}
        bot.answer_callback_query(call.id)
        _send_uni_card(bot, call.message.chat.id, uid, edit_msg_id=call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("uni_page:"))
    def on_uni_page(call):
        uid = call.from_user.id
        parts = call.data.split(":")
        direction = parts[1]
        state = user_state.get(uid, {})
        unis = state.get("unis", [])
        index = state.get("u_index", 0)
        if direction == "next" and index < len(unis) - 1:
            index += 1
        elif direction == "prev" and index > 0:
            index -= 1
        user_state[uid]["u_index"] = index
        bot.answer_callback_query(call.id)
        _send_uni_card(bot, call.message.chat.id, uid, edit_msg_id=call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data == "back_uni_type")
    def back_uni_type(call):
        text = "🎓 <b>Universitetlar</b>\n\n🏛️ Turini tanlang:"
        try:
            bot.edit_message_text(
                text, call.message.chat.id, call.message.message_id,
                parse_mode="HTML", reply_markup=university_type_keyboard()
            )
        except Exception:
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            bot.send_message(
                call.message.chat.id, text,
                parse_mode="HTML", reply_markup=university_type_keyboard()
            )
        bot.answer_callback_query(call.id)


def _send_uni_card(bot, chat_id, uid, edit_msg_id=None):
    state = user_state.get(uid, {})
    unis = state.get("unis", [])
    index = state.get("u_index", 0)
    if not unis:
        return
    u = unis[index]
    increment_views("universities", u["id"])
    text = university_text(u)
    total = len(unis)
    kb = pagination_keyboard(index, total, "uni_page", "back_uni_type", item=u)
    if edit_msg_id:
        edit_or_send_media(bot, chat_id, edit_msg_id, text, u.get("media_file_id"), u.get("media_type"), kb)
    else:
        send_media_message(bot, chat_id, text, u.get("media_file_id"), u.get("media_type"), kb)
