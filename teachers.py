import telebot
from bot.database.db import get_subjects, get_teachers, update_user_activity, increment_views
from bot.utils.keyboards import teacher_type_keyboard, build_inline_grid, pagination_keyboard
from bot.utils.helpers import send_media_message, edit_or_send_media, teacher_text

user_state = {}


def register(bot: telebot.TeleBot):

    @bot.message_handler(func=lambda m: m.text == "🔍 O'qituvchi topish")
    def find_teacher(message):
        update_user_activity(message.from_user.id)
        user_state.pop(message.from_user.id, None)
        bot.send_message(
            message.chat.id,
            "🔍 <b>O'qituvchi topish</b>\n\n🎯 Dars turini tanlang:",
            parse_mode="HTML",
            reply_markup=teacher_type_keyboard()
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ttype:"))
    def on_teach_type(call):
        teach_type = call.data.split(":", 1)[1]
        uid = call.from_user.id
        user_state[uid] = {"teach_type": teach_type}
        subjects = get_subjects()
        if not subjects:
            bot.answer_callback_query(call.id, "⚠️ Hozircha fanlar yo'q!", show_alert=True)
            return
        kb = build_inline_grid(subjects, "tsubject", cols=2, back_cb="back_teacher_type")
        bot.edit_message_text(
            f"📚 <b>Fan tanlang</b>\n🎯 Tur: <i>{teach_type}</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "back_teacher_type")
    def back_teacher_type(call):
        text = "🔍 <b>O'qituvchi topish</b>\n\n🎯 Dars turini tanlang:"
        try:
            bot.edit_message_text(
                text, call.message.chat.id, call.message.message_id,
                parse_mode="HTML", reply_markup=teacher_type_keyboard()
            )
        except Exception:
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            bot.send_message(
                call.message.chat.id, text,
                parse_mode="HTML", reply_markup=teacher_type_keyboard()
            )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("tsubject:"))
    def on_subject(call):
        subject = call.data.split(":", 1)[1]
        uid = call.from_user.id
        state = user_state.get(uid, {})
        teach_type = state.get("teach_type")
        teachers = get_teachers(teach_type=teach_type, subject=subject)
        if not teachers:
            bot.answer_callback_query(call.id, "😔 Bu bo'yicha o'qituvchi topilmadi!", show_alert=True)
            return
        user_state[uid]["teachers"] = teachers
        user_state[uid]["t_index"] = 0
        user_state[uid]["subject"] = subject
        bot.answer_callback_query(call.id)
        _send_teacher_card(bot, call.message.chat.id, uid, edit_msg_id=call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("teacher_page:"))
    def on_teacher_page(call):
        uid = call.from_user.id
        parts = call.data.split(":")
        direction = parts[1]
        state = user_state.get(uid, {})
        teachers = state.get("teachers", [])
        index = state.get("t_index", 0)
        if direction == "next" and index < len(teachers) - 1:
            index += 1
        elif direction == "prev" and index > 0:
            index -= 1
        user_state[uid]["t_index"] = index
        bot.answer_callback_query(call.id)
        _send_teacher_card(bot, call.message.chat.id, uid, edit_msg_id=call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data == "close_pagination")
    def close_pagination(call):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "back_main")
    def back_main(call):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "noop")
    def noop(call):
        bot.answer_callback_query(call.id)


def _send_teacher_card(bot, chat_id, uid, edit_msg_id=None):
    state = user_state.get(uid, {})
    teachers = state.get("teachers", [])
    index = state.get("t_index", 0)
    if not teachers:
        return
    t = teachers[index]
    increment_views("teachers", t["id"])
    text = teacher_text(t)
    total = len(teachers)
    kb = pagination_keyboard(index, total, "teacher_page", "back_teacher_type", item=t)
    if edit_msg_id:
        edit_or_send_media(bot, chat_id, edit_msg_id, text, t.get("media_file_id"), t.get("media_type"), kb)
    else:
        send_media_message(bot, chat_id, text, t.get("media_file_id"), t.get("media_type"), kb)
