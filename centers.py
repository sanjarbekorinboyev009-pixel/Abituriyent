import telebot
from bot.database.db import get_cities, get_centers, update_user_activity, increment_views
from bot.utils.keyboards import build_inline_grid, center_card_keyboard
from bot.utils.helpers import send_media_message, edit_or_send_media, center_text

user_state = {}


def register(bot: telebot.TeleBot):

    @bot.message_handler(func=lambda m: m.text == "🏫 O'quv markazlari")
    def find_center(message):
        update_user_activity(message.from_user.id)
        user_state.pop(message.from_user.id, None)
        cities = get_cities()
        kb = build_inline_grid(cities, "center_city", cols=2, back_cb="back_main")
        bot.send_message(
            message.chat.id,
            "🏫 <b>O'quv markazlari</b>\n\nShahringizni tanlang:",
            parse_mode="HTML",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("center_city:"))
    def on_center_city(call):
        city = call.data.split(":", 1)[1]
        uid = call.from_user.id
        centers = get_centers(city=city)

        if not centers:
            bot.answer_callback_query(call.id, f"{city}da hozircha markaz yo'q!", show_alert=True)
            return

        user_state[uid] = {"centers": centers, "c_index": 0, "city": city}
        bot.answer_callback_query(call.id)
        _send_center_card(bot, call.message.chat.id, uid, edit_msg_id=call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("center_page:"))
    def on_center_page(call):
        uid = call.from_user.id
        parts = call.data.split(":")
        direction = parts[1]
        state = user_state.get(uid, {})
        centers = state.get("centers", [])
        index = state.get("c_index", 0)

        if direction == "next" and index < len(centers) - 1:
            index += 1
        elif direction == "prev" and index > 0:
            index -= 1

        user_state[uid]["c_index"] = index
        bot.answer_callback_query(call.id)
        _send_center_card(bot, call.message.chat.id, uid, edit_msg_id=call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("center_city_back:"))
    def center_city_back(call):
        cities = get_cities()
        kb = build_inline_grid(cities, "center_city", cols=2, back_cb="back_main")
        text = "🏫 <b>O'quv markazlari</b>\n\nShahringizni tanlang:"
        try:
            bot.edit_message_text(
                text, call.message.chat.id, call.message.message_id,
                parse_mode="HTML", reply_markup=kb
            )
        except Exception:
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            bot.send_message(
                call.message.chat.id, text,
                parse_mode="HTML", reply_markup=kb
            )
        bot.answer_callback_query(call.id)


def _send_center_card(bot, chat_id, uid, edit_msg_id=None):
    state = user_state.get(uid, {})
    centers = state.get("centers", [])
    index = state.get("c_index", 0)
    city = state.get("city", "")

    if not centers:
        return

    c = centers[index]
    increment_views("centers", c["id"])
    text = center_text(c)
    total = len(centers)
    back_cb = f"center_city_back:{city}"
    kb = center_card_keyboard(index, total, c, back_cb)

    if edit_msg_id:
        edit_or_send_media(bot, chat_id, edit_msg_id, text, c.get("media_file_id"), c.get("media_type"), kb)
    else:
        send_media_message(bot, chat_id, text, c.get("media_file_id"), c.get("media_type"), kb)
