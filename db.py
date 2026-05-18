import sqlite3
import csv
import json
import os
from bot.config import DEFAULT_SUBJECTS, DEFAULT_CITIES

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "abutrend.db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            full_name TEXT,
            joined_at TEXT DEFAULT (datetime('now')),
            last_active TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            subject TEXT NOT NULL,
            teach_type TEXT NOT NULL,
            description TEXT,
            media_file_id TEXT,
            media_type TEXT,
            button_text TEXT,
            button_url TEXT,
            expires_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            description TEXT,
            media_file_id TEXT,
            media_type TEXT,
            button_text TEXT,
            button_url TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS universities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            uni_type TEXT NOT NULL,
            description TEXT,
            media_file_id TEXT,
            media_type TEXT,
            button_text TEXT,
            button_url TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_ids TEXT,
            sent_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Mavjud jadvalga yangi ustunlar qo'shish (migration)
    for table in ("teachers", "universities"):
        for col in ("button_text", "button_url"):
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass
    for table in ("teachers", "centers", "universities"):
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN buttons_json TEXT")
        except sqlite3.OperationalError:
            pass
    for table in ("teachers", "centers", "universities"):
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN position INTEGER")
        except sqlite3.OperationalError:
            pass
    for table in ("teachers", "centers", "universities"):
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN views INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

    for s in DEFAULT_SUBJECTS:
        c.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (s,))
    for city in DEFAULT_CITIES:
        c.execute("INSERT OR IGNORE INTO cities (name) VALUES (?)", (city,))

    conn.commit()
    conn.close()


# ─── FOYDALANUVCHILAR ────────────────────────────────────────────

def register_user(telegram_id, username, full_name):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (telegram_id, username, full_name)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username=excluded.username,
            full_name=excluded.full_name,
            last_active=datetime('now')
    """, (telegram_id, username or "", full_name or ""))
    conn.commit()
    conn.close()


def update_user_activity(telegram_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET last_active=datetime('now') WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()


def get_stats():
    conn = get_conn()
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    active = c.execute(
        "SELECT COUNT(*) FROM users WHERE last_active >= datetime('now', '-7 days')"
    ).fetchone()[0]
    conn.close()
    return total, active


def get_all_user_ids():
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("SELECT telegram_id FROM users").fetchall()
    conn.close()
    return [r[0] for r in rows]


# ─── SHAHARLAR ───────────────────────────────────────────────────

def get_cities():
    conn = get_conn()
    rows = get_conn().cursor().execute("SELECT name FROM cities ORDER BY name").fetchall()
    conn.close()
    return [r[0] for r in rows]


def add_city(name):
    conn = get_conn()
    try:
        conn.cursor().execute("INSERT INTO cities (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def delete_city(name):
    conn = get_conn()
    conn.cursor().execute("DELETE FROM cities WHERE name=?", (name,))
    conn.commit()
    conn.close()


# ─── FANLAR ──────────────────────────────────────────────────────

def get_subjects():
    conn = get_conn()
    rows = conn.cursor().execute("SELECT name FROM subjects ORDER BY name").fetchall()
    conn.close()
    return [r[0] for r in rows]


def add_subject(name):
    conn = get_conn()
    try:
        conn.cursor().execute("INSERT INTO subjects (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def delete_subject(name):
    conn = get_conn()
    conn.cursor().execute("DELETE FROM subjects WHERE name=?", (name,))
    conn.commit()
    conn.close()


# ─── O'QITUVCHILAR ───────────────────────────────────────────────

def _next_available_id(table):
    """Eng kichik bo'sh ID ni topadi (o'chirilgan ID lar qayta ishlatiladi)."""
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute(f"SELECT id FROM {table} ORDER BY id").fetchall()
    conn.close()
    used = {r[0] for r in rows}
    i = 1
    while i in used:
        i += 1
    return i


def increment_views(table, item_id):
    """Ko'rishlar sonini 1 ga oshiradi."""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        f"UPDATE {table} SET views = COALESCE(views, 0) + 1 WHERE id=?",
        (item_id,)
    )
    conn.commit()
    conn.close()


def get_views_list(table):
    """Admin uchun ko'rishlar ro'yxati, pozitsiya bo'yicha tartiblangan."""
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute(
        f"SELECT id, name, COALESCE(views, 0) as views FROM {table} "
        f"ORDER BY COALESCE(position, 999999), rowid"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _compact_positions_conn(c, table):
    """Internal: pozitsiyalarni ixchamlashtiradi 1,2,3,..."""
    rows = c.execute(
        f"SELECT id FROM {table} ORDER BY COALESCE(position, 999999), rowid"
    ).fetchall()
    for i, row in enumerate(rows, 1):
        c.execute(f"UPDATE {table} SET position=? WHERE id=?", (i, row[0]))


def get_positions_list(table):
    """Admin uchun tartib ro'yxati."""
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute(
        f"SELECT id, name, position FROM {table} "
        f"ORDER BY COALESCE(position, 999999), rowid"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_item_position(table, item_id, new_pos):
    """Elementni berilgan pozitsiyaga ko'chiradi, boshqalarni siljitadi."""
    conn = get_conn()
    c = conn.cursor()
    row = c.execute(f"SELECT position FROM {table} WHERE id=?", (item_id,)).fetchone()
    if not row:
        conn.close()
        return False
    old_pos = row[0]
    total = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    new_pos = max(1, min(new_pos, total))
    if old_pos is None:
        c.execute(
            f"UPDATE {table} SET position=position+1 "
            f"WHERE position IS NOT NULL AND position>=?", (new_pos,)
        )
    elif new_pos < old_pos:
        c.execute(
            f"UPDATE {table} SET position=position+1 WHERE position>=? AND position<?",
            (new_pos, old_pos)
        )
    elif new_pos > old_pos:
        c.execute(
            f"UPDATE {table} SET position=position-1 WHERE position>? AND position<=?",
            (old_pos, new_pos)
        )
    c.execute(f"UPDATE {table} SET position=? WHERE id=?", (new_pos, item_id))
    _compact_positions_conn(c, table)
    conn.commit()
    conn.close()
    return True


def add_teacher(name, city, subject, teach_type, description,
                media_file_id, media_type, buttons=None):
    new_id = _next_available_id("teachers")
    bj = json.dumps(buttons or [], ensure_ascii=False)
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO teachers
            (id, name, city, subject, teach_type, description,
             media_file_id, media_type, buttons_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (new_id, name, city, subject, teach_type, description,
          media_file_id, media_type, bj))
    conn.commit()
    conn.close()
    export_teachers_csv()
    return new_id


def delete_teacher(teacher_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM teachers WHERE id=?", (teacher_id,))
    affected = c.rowcount
    if affected:
        _compact_positions_conn(c, "teachers")
    conn.commit()
    conn.close()
    if affected:
        export_teachers_csv()
    return affected > 0


def get_teachers(teach_type=None, subject=None):
    conn = get_conn()
    c = conn.cursor()
    query = "SELECT * FROM teachers WHERE 1=1"
    params = []
    if teach_type:
        query += " AND teach_type=?"
        params.append(teach_type)
    if subject:
        query += " AND subject=?"
        params.append(subject)
    query += " ORDER BY COALESCE(position, 999999) ASC, created_at DESC"
    rows = c.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── MARKAZLAR ───────────────────────────────────────────────────

def add_center(name, city, description, media_file_id, media_type, buttons=None):
    new_id = _next_available_id("centers")
    bj = json.dumps(buttons or [], ensure_ascii=False)
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO centers
            (id, name, city, description, media_file_id, media_type, buttons_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (new_id, name, city, description, media_file_id, media_type, bj))
    conn.commit()
    conn.close()
    export_centers_csv()
    return new_id


def delete_center(center_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM centers WHERE id=?", (center_id,))
    affected = c.rowcount
    if affected:
        _compact_positions_conn(c, "centers")
    conn.commit()
    conn.close()
    if affected:
        export_centers_csv()
    return affected > 0


def get_centers(city=None):
    conn = get_conn()
    c = conn.cursor()
    if city:
        rows = c.execute(
            "SELECT * FROM centers WHERE city=? ORDER BY COALESCE(position,999999) ASC, created_at DESC",
            (city,)
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT * FROM centers ORDER BY COALESCE(position,999999) ASC, created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── UNIVERSITETLAR ──────────────────────────────────────────────

def add_university(name, uni_type, description, media_file_id, media_type, buttons=None):
    new_id = _next_available_id("universities")
    bj = json.dumps(buttons or [], ensure_ascii=False)
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO universities
            (id, name, uni_type, description, media_file_id, media_type, buttons_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (new_id, name, uni_type, description, media_file_id, media_type, bj))
    conn.commit()
    conn.close()
    export_universities_csv()
    return new_id


def delete_university(uni_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM universities WHERE id=?", (uni_id,))
    affected = c.rowcount
    if affected:
        _compact_positions_conn(c, "universities")
    conn.commit()
    conn.close()
    if affected:
        export_universities_csv()
    return affected > 0


def get_universities(uni_type=None):
    conn = get_conn()
    c = conn.cursor()
    if uni_type:
        rows = c.execute(
            "SELECT * FROM universities WHERE uni_type=? ORDER BY COALESCE(position,999999) ASC, created_at DESC",
            (uni_type,)
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT * FROM universities ORDER BY COALESCE(position,999999) ASC, created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── BROADCAST ───────────────────────────────────────────────────

def save_broadcast(message_ids: list):
    encoded = ",".join(f"{uid}:{mid}" for uid, mid in message_ids)
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO broadcasts (message_ids) VALUES (?)", (encoded,))
    conn.commit()
    conn.close()


def get_last_broadcast():
    conn = get_conn()
    c = conn.cursor()
    row = c.execute("SELECT * FROM broadcasts ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None


# ─── CSV EXPORT ──────────────────────────────────────────────────

def export_teachers_csv():
    conn = get_conn()
    rows = conn.cursor().execute(
        "SELECT id, name, city, subject, teach_type, description, button_text, button_url, expires_at, created_at FROM teachers"
    ).fetchall()
    conn.close()
    path = os.path.join(DATA_DIR, "oqituvchilar.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Ism", "Shahar", "Fan", "Tur", "Tavsif", "Tugma matni", "URL", "Muddat", "Qo'shilgan"])
        for r in rows:
            writer.writerow(list(r))


def export_centers_csv():
    conn = get_conn()
    rows = conn.cursor().execute(
        "SELECT id, name, city, description, button_text, button_url, created_at FROM centers"
    ).fetchall()
    conn.close()
    path = os.path.join(DATA_DIR, "markazlar.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Nomi", "Shahar", "Tavsif", "Tugma matni", "URL", "Qo'shilgan"])
        for r in rows:
            writer.writerow(list(r))


def export_universities_csv():
    conn = get_conn()
    rows = conn.cursor().execute(
        "SELECT id, name, uni_type, description, button_text, button_url, created_at FROM universities"
    ).fetchall()
    conn.close()
    path = os.path.join(DATA_DIR, "universitetlar.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Nomi", "Tur", "Tavsif", "Tugma matni", "URL", "Qo'shilgan"])
        for r in rows:
            writer.writerow(list(r))
