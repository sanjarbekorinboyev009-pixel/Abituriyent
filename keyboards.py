import json
import telebot
from telebot import types


def _parse_item_buttons(item):
    """Itemdan tugmalar ro'yxatini chiqaradi (JSON yoki eski button_text/url)."""
    if not item:
        return []
    bj = item.get("buttons_json")
    if bj:
        try:
            data = json.loads(bj)
            return [(b[0], b[1]) for b in data if len(b) == 2 and b[0] and b[1]][:3]
        except Exception:
            pass
    bt, bu = item.get("button_text"), item.get("button_url")
    if bt and bu:
        return [(bt, bu)]
    return []


def main_menu_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("🔍 O'qituvchi topish"),
        types.KeyboardButton("🏫 O'quv markazlari"),
        types.KeyboardButton("🎓 Universitetlar"),
        types.KeyboardButton("ℹ️ Bot haqida")
    )
    return kb


def back_inline(callback):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=callback))
    return kb


def build_inline_grid(items, callback_prefix, cols=2, back_cb=None):
    kb = types.InlineKeyboardMarkup(row_width=cols)
    buttons = [
        types.InlineKeyboardButton(item, callback_data=f"{callback_prefix}:{item}")
        for item in items
    ]
    kb.add(*buttons)
    if back_cb:
        kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=back_cb))
    return kb


def _card_keyboard(index, total, prefix, back_cb, item=None):
    """Umumiy karta klaviaturasi - tugma qo'shimchasi bilan."""
    kb = types.InlineKeyboardMarkup(row_width=3)
    prev_cb = f"{prefix}:prev:{index}" if index > 0 else "noop"
    next_cb = f"{prefix}:next:{index}" if index < total - 1 else "noop"
    kb.row(
        types.InlineKeyboardButton("⬅️", callback_data=prev_cb),
        types.InlineKeyboardButton("❌ Yopish", callback_data="close_pagination"),
        types.InlineKeyboardButton("➡️", callback_data=next_cb),
    )
    for bt, bu in _parse_item_buttons(item):
        kb.add(types.InlineKeyboardButton(bt, url=bu))
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=back_cb))
    return kb


def pagination_keyboard(index, total, prefix, back_cb, item=None):
    return _card_keyboard(index, total, prefix, back_cb, item)


def teacher_type_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🖥️ Online", callback_data="ttype:Online"),
        types.InlineKeyboardButton("🏠 Offline", callback_data="ttype:Offline"),
    )
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="back_main"))
    return kb


def university_type_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🇺🇿 Davlat", callback_data="utype:Davlat"),
        types.InlineKeyboardButton("🌐 Nodavlat", callback_data="utype:Nodavlat"),
    )
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="back_main"))
    return kb


def center_card_keyboard(index, total, center, back_cb):
    return _card_keyboard(index, total, "center_page", back_cb, center)


# ─── ADMIN PANEL ─────────────────────────────────────────────────

def admin_main_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("👨‍🏫 Ustoz ➕", callback_data="adm:add_teacher"),
        types.InlineKeyboardButton("👨‍🏫 Ustoz 🗑", callback_data="adm:del_teacher"),
    )
    kb.row(
        types.InlineKeyboardButton("🏫 Markaz ➕", callback_data="adm:add_center"),
        types.InlineKeyboardButton("🏫 Markaz 🗑", callback_data="adm:del_center"),
    )
    kb.row(
        types.InlineKeyboardButton("🎓 Universitet ➕", callback_data="adm:add_uni"),
        types.InlineKeyboardButton("🎓 Universitet 🗑", callback_data="adm:del_uni"),
    )
    kb.row(
        types.InlineKeyboardButton("🏙️ Shaharlar", callback_data="adm:cities"),
        types.InlineKeyboardButton("📚 Fanlar", callback_data="adm:subjects"),
    )
    kb.row(
        types.InlineKeyboardButton("📢 Reklama", callback_data="adm:broadcast"),
        types.InlineKeyboardButton("🗑️ Reklamani o'chirish", callback_data="adm:del_broadcast"),
    )
    kb.row(
        types.InlineKeyboardButton("📥 Ustozlar", callback_data="adm:xlsx_teachers"),
        types.InlineKeyboardButton("📥 Markazlar", callback_data="adm:xlsx_centers"),
    )
    kb.row(
        types.InlineKeyboardButton("📥 Universitetlar", callback_data="adm:xlsx_unis"),
        types.InlineKeyboardButton("📊 Statistika", callback_data="adm:stats"),
    )
    kb.row(
        types.InlineKeyboardButton("📋 Tartibni tahrirlash", callback_data="adm:edit_positions"),
    )
    return kb


def position_select_keyboard(items):
    """Qo'shish vaqtida yangi element o'rnini tanlash."""
    kb = types.InlineKeyboardMarkup(row_width=4)
    if items:
        btns = [
            types.InlineKeyboardButton(str(i), callback_data=f"admpos:{i}")
            for i in range(1, len(items) + 1)
        ]
        for i in range(0, len(btns), 4):
            kb.row(*btns[i:i + 4])
    last = len(items) + 1
    kb.add(types.InlineKeyboardButton(
        f"⬇️ Oxirga ({last}-o'rin)", callback_data=f"admpos:{last}"
    ))
    kb.add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="adm:back"))
    return kb


def edit_positions_menu_keyboard():
    """Tartib tahrirlash bo'lim tanlash."""
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("👨‍🏫 Ustozlar tartibi", callback_data="adm:editpos:teachers"))
    kb.add(types.InlineKeyboardButton("🏫 Markazlar tartibi", callback_data="adm:editpos:centers"))
    kb.add(types.InlineKeyboardButton("🎓 Universitetlar tartibi", callback_data="adm:editpos:universities"))
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="adm:back"))
    return kb


def items_list_keyboard(items, table):
    """Tahrirlash uchun elementlar ro'yxati."""
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, item in enumerate(items, 1):
        name = (item.get("name") or f"#{item['id']}")[:35]
        kb.add(types.InlineKeyboardButton(
            f"✏️ {i}. {name}",
            callback_data=f"adm:moveitem:{table}:{item['id']}"
        ))
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="adm:edit_positions"))
    return kb


def move_item_keyboard(items, table, item_id):
    """Elementni yangi o'ringa ko'chirish uchun tugmalar."""
    kb = types.InlineKeyboardMarkup(row_width=4)
    current_pos = next((i for i, x in enumerate(items, 1) if x["id"] == item_id), None)
    btns = []
    for i, item in enumerate(items, 1):
        if i == current_pos:
            btns.append(types.InlineKeyboardButton(f"●{i}", callback_data="noop"))
        else:
            btns.append(types.InlineKeyboardButton(
                str(i), callback_data=f"adm:setpos:{table}:{item_id}:{i}"
            ))
    for i in range(0, len(btns), 4):
        kb.row(*btns[i:i + 4])
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"adm:editpos:{table}"))
    return kb


def admin_cities_keyboard(cities):
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(f"🗑 {c}", callback_data=f"adm_delcity:{c}") for c in cities]
    kb.add(*btns)
    kb.row(
        types.InlineKeyboardButton("➕ Shahar qo'shish", callback_data="adm:add_city"),
        types.InlineKeyboardButton("🔙 Orqaga", callback_data="adm:back"),
    )
    return kb


def admin_subjects_keyboard(subjects):
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(f"🗑 {s}", callback_data=f"adm_delsub:{s}") for s in subjects]
    kb.add(*btns)
    kb.row(
        types.InlineKeyboardButton("➕ Fan qo'shish", callback_data="adm:add_subject"),
        types.InlineKeyboardButton("🔙 Orqaga", callback_data="adm:back"),
    )
    return kb


def skip_media_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="skip_media"),
        types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="adm:back"),
    )
    return kb


def skip_button_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="skip_button"),
        types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="adm:back"),
    )
    return kb


def confirm_broadcast_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("✅ Yuborish", callback_data="broadcast:confirm"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="broadcast:cancel"),
    )
    return kb


def admin_select_keyboard(items, prefix, back_cb="adm:back"):
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(item, callback_data=f"admsel:{prefix}:{item}")
        for item in items
    ]
    kb.add(*buttons)
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=back_cb))
    return kb


def stats_views_keyboard():
    """Statistika sahifasidagi ko'rishlar bo'limlari."""
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("👨‍🏫 Ustozlar ko'rishlari", callback_data="adm:stats_views:teachers"))
    kb.add(types.InlineKeyboardButton("🏫 Markazlar ko'rishlari", callback_data="adm:stats_views:centers"))
    kb.add(types.InlineKeyboardButton("🎓 Universitetlar ko'rishlari", callback_data="adm:stats_views:universities"))
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="adm:back"))
    return kb


def broadcast_btn_step_keyboard():
    """Broadcast - inline tugma qo'shish yoki o'tkazib yuborish."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("🔗 Tugma qo'shish", callback_data="bcast:add_btn"),
        types.InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="bcast:skip_btn"),
    )
    kb.add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="broadcast:cancel"))
    return kb
