from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import sqlite3
import threading
import time
import random
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import requests
import secrets
import json
from functools import wraps

# =========================================================
# CONFIG
# =========================================================
APP_TZ = ZoneInfo("America/Sao_Paulo")
DB_PATH = os.getenv("DB_PATH", "/tmp/rainha_games_auto.db")

TOKEN = os.getenv("TOKEN", "").strip()
CHAT_ID = os.getenv("CHAT_ID", "").strip()

DEFAULT_ADMIN_USER = os.getenv("ADMIN_USER", "admin").strip()
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123456").strip()
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

# Janela interna automática do sistema
AUTO_START_TIME = "18:45"
AUTO_END_TIME = "23:58"

# Tempo do loop
SCHEDULER_SLEEP_SECONDS = 15

# Link fixo do botão
DEFAULT_FOOTER_LINK = "https://beacons.ai/rainhagames"
DEFAULT_FOOTER_TEXT = "👑 A RAINHA JOGA AQUI"

app = Flask(__name__)
app.secret_key = SECRET_KEY

# =========================================================
# CATÁLOGO INICIAL
# =========================================================
SEED_GAMES = [
    # PG SOFT
    ("Fortune Tiger", "PG Soft", "96.81%", "🐯"),
    ("Fortune Ox", "PG Soft", "96.75%", "🐂"),
    ("Fortune Rabbit", "PG Soft", "96.75%", "🐰"),
    ("Fortune Mouse", "PG Soft", "96.72%", "🐭"),
    ("Fortune Dragon", "PG Soft", "96.83%", "🐉"),
    ("Fortune Snake", "PG Soft", "96.70%", "🐍"),
    ("Fortune Gods", "PG Soft", "96.74%", "💰"),
    ("Fortune Horse", "PG Soft", "96.72%", "🐎"),
    ("Mahjong Ways", "PG Soft", "96.92%", "🀄"),
    ("Mahjong Ways 2", "PG Soft", "96.95%", "🀄"),
    ("Wild Bandito", "PG Soft", "97.00%", "🤠"),
    ("Medusa", "PG Soft", "96.58%", "🐍"),
    ("Medusa II", "PG Soft", "96.58%", "🐍"),
    ("Ganesha Gold", "PG Soft", "96.49%", "🐘"),
    ("Ganesha Fortune", "PG Soft", "96.71%", "🐘"),
    ("Caishen Wins", "PG Soft", "96.92%", "💰"),
    ("Dragon Hatch", "PG Soft", "96.83%", "🐉"),
    ("Dragon Hatch 2", "PG Soft", "96.83%", "🐉"),
    ("Dragon Legend", "PG Soft", "96.50%", "🐉"),
    ("Rave Party Fever", "PG Soft", "96.32%", "🎧"),
    ("Cocktail Nights", "PG Soft", "96.20%", "🍸"),
    ("Speed Winner", "PG Soft", "96.53%", "🏎️"),
    ("Bikini Paradise", "PG Soft", "96.20%", "👙"),
    ("Galactic Gems", "PG Soft", "98.13%", "💎"),
    ("Galaxy Miner", "PG Soft", "96.32%", "🚀"),
    ("Crypto Gold", "PG Soft", "96.12%", "₿"),
    ("Safari Wilds", "PG Soft", "96.31%", "🦁"),
    ("Jurassic Kingdom", "PG Soft", "96.18%", "🦖"),
    ("Rise of Apollo", "PG Soft", "96.20%", "⚡"),
    ("Totem Wonders", "PG Soft", "96.71%", "🗿"),
    ("Opera Dynasty", "PG Soft", "96.52%", "🎭"),
    ("Muay Thai Champion", "PG Soft", "96.86%", "🥊"),
    ("Ninja vs Samurai", "PG Soft", "97.44%", "⚔️"),
    ("Legend of Perseus", "PG Soft", "96.31%", "🛡️"),
    ("Legend of Hou Yi", "PG Soft", "96.95%", "🏹"),
    ("Lucky Neko", "PG Soft", "96.73%", "🐱"),
    ("Lucky Piggy", "PG Soft", "96.44%", "🐷"),
    ("Leprechaun Riches", "PG Soft", "97.35%", "🍀"),
    ("Shark Bounty", "PG Soft", "96.71%", "🦈"),
    ("Wings of Iguazu", "PG Soft", "96.29%", "🦜"),
    ("Yakuza Honor", "PG Soft", "96.11%", "🕴️"),
    ("Zombie Outbreak", "PG Soft", "96.20%", "🧟"),

    # PRAGMATIC PLAY
    ("Gates of Olympus", "Pragmatic Play", "96.50%", "⚡"),
    ("Gates of Olympus 1000", "Pragmatic Play", "96.50%", "⚡"),
    ("Sweet Bonanza", "Pragmatic Play", "96.51%", "🍭"),
    ("Sweet Bonanza Xmas", "Pragmatic Play", "96.48%", "🎄"),
    ("Sweet Bonanza 1000", "Pragmatic Play", "96.50%", "🍭"),
    ("Starlight Princess", "Pragmatic Play", "96.50%", "⭐"),
    ("Starlight Princess 1000", "Pragmatic Play", "96.50%", "⭐"),
    ("Big Bass Bonanza", "Pragmatic Play", "96.71%", "🎣"),
    ("Big Bass Splash", "Pragmatic Play", "96.71%", "🎣"),
    ("Big Bass Bonanza Megaways", "Pragmatic Play", "96.70%", "🎣"),
    ("Big Bass Halloween", "Pragmatic Play", "96.50%", "🎃"),
    ("Big Bass Christmas Bash", "Pragmatic Play", "96.50%", "🎄"),
    ("The Dog House", "Pragmatic Play", "96.51%", "🐶"),
    ("The Dog House Megaways", "Pragmatic Play", "96.55%", "🐶"),
    ("Fruit Party", "Pragmatic Play", "96.50%", "🍓"),
    ("Fruit Party 2", "Pragmatic Play", "96.50%", "🍓"),
    ("Fruit Party 1000", "Pragmatic Play", "96.50%", "🍓"),
    ("Sugar Rush", "Pragmatic Play", "96.50%", "🍬"),
    ("Sugar Rush 1000", "Pragmatic Play", "96.50%", "🍬"),
    ("Wolf Gold", "Pragmatic Play", "96.01%", "🐺"),
    ("Wolf Gold Ultimate", "Pragmatic Play", "96.50%", "🐺"),
    ("Buffalo King", "Pragmatic Play", "96.06%", "🦬"),
    ("Buffalo King Megaways", "Pragmatic Play", "96.78%", "🦬"),
    ("Buffalo King Untamed", "Pragmatic Play", "96.50%", "🦬"),
    ("Great Rhino", "Pragmatic Play", "95.97%", "🦏"),
    ("Great Rhino Megaways", "Pragmatic Play", "96.58%", "🦏"),
    ("Extra Juicy", "Pragmatic Play", "96.50%", "🍉"),
    ("Extra Juicy Megaways", "Pragmatic Play", "96.52%", "🍉"),
    ("Juicy Fruits", "Pragmatic Play", "96.50%", "🍓"),
    ("Hot Fiesta", "Pragmatic Play", "96.08%", "🌶️"),
    ("Chili Heat", "Pragmatic Play", "96.50%", "🌶️"),
    ("Release the Kraken", "Pragmatic Play", "96.50%", "🐙"),
    ("Hand of Midas", "Pragmatic Play", "96.50%", "✋"),
    ("Power of Thor", "Pragmatic Play", "96.55%", "⚡"),
    ("Power of Thor Megaways", "Pragmatic Play", "96.55%", "⚡"),
    ("5 Lions", "Pragmatic Play", "96.50%", "🦁"),
    ("5 Lions Megaways", "Pragmatic Play", "96.50%", "🦁"),
    ("Aztec Gems", "Pragmatic Play", "96.50%", "🏺"),
    ("Aztec Gems Deluxe", "Pragmatic Play", "96.50%", "🏺"),
    ("Wild West Gold", "Pragmatic Play", "96.51%", "🤠"),
    ("Wild West Gold Megaways", "Pragmatic Play", "96.54%", "🤠"),
    ("Pirate Gold", "Pragmatic Play", "96.50%", "🏴‍☠️"),
    ("Queen of Gold", "Pragmatic Play", "96.50%", "👑"),
    ("Emerald King", "Pragmatic Play", "96.50%", "💎"),
    ("Cyber Heist", "Pragmatic Play", "96.50%", "🤖"),
    ("Spaceman", "Pragmatic Play", "96.50%", "🚀"),
    ("Zeus Unleashed", "Pragmatic Play", "96.50%", "⚡"),
    ("Hades Inferno", "Pragmatic Play", "96.50%", "🔥"),

    # HACKSAW
    ("Wanted Dead or a Wild", "Hacksaw", "96.38%", "🤠"),
    ("The Bowery Boys", "Hacksaw", "96.41%", "🦹"),
    ("Frutz", "Hacksaw", "96.40%", "🍓"),
    ("Aztec Twist", "Hacksaw", "96.36%", "🏺"),
    ("Joker Bombs", "Hacksaw", "96.48%", "🃏"),
    ("Cash Compass", "Hacksaw", "96.42%", "🧭"),
    ("Densho", "Hacksaw", "96.40%", "⛩️"),
    ("RIP City", "Hacksaw", "96.22%", "💀"),
    ("Cubes 2", "Hacksaw", "96.38%", "🧊"),
    ("Hand of Anubis", "Hacksaw", "96.24%", "🐺"),
    ("Eye of Medusa", "Hacksaw", "96.20%", "👁️"),
    ("Chaos Crew 2", "Hacksaw", "96.30%", "💥"),
    ("Beam Boys", "Hacksaw", "96.30%", "⚡"),
    ("Le Bandit", "Hacksaw", "96.30%", "🎭"),
    ("Donut Division", "Hacksaw", "96.30%", "🍩"),
    ("2 Wild 2 Die", "Hacksaw", "96.30%", "💥"),
    ("Duel at Dawn", "Hacksaw", "96.30%", "🌅"),
    ("Bullets and Bounty", "Hacksaw", "96.30%", "🎯"),
    ("The Luxe", "Hacksaw", "96.30%", "💎"),
    ("Le Cowboy", "Hacksaw", "96.28%", "🤠"),
    ("Marlin Masters", "Hacksaw", "96.28%", "🐟"),
    ("Fist of Destruction", "Hacksaw", "96.30%", "👊"),
    ("Slayers Inc", "Hacksaw", "96.30%", "⚔️"),
    ("Benny the Beer", "Hacksaw", "96.30%", "🍺"),
    ("King Carrot", "Hacksaw", "96.30%", "🥕"),
    ("Klowns", "Hacksaw", "96.30%", "🤡"),
    ("Hounds of Hell", "Hacksaw", "96.30%", "🐕"),
    ("Le Viking", "Hacksaw", "96.30%", "🛡️"),
    ("Wings of Horus", "Hacksaw", "96.30%", "🦅"),
    ("Rise of Ymir", "Hacksaw", "96.30%", "🧊"),
    ("Shaolin Master", "Hacksaw", "96.30%", "🥋"),
    ("Stormborn", "Hacksaw", "96.30%", "⛈️"),
    ("Tiger Legends", "Hacksaw", "96.30%", "🐯"),
    ("Le Zeus", "Hacksaw", "96.30%", "⚡"),
    ("Fire My Laser", "Hacksaw", "96.30%", "🔫"),
]

INTRO_VARIANTS = [
    "🎰 Entrada confirmada",
    "🎰 Oportunidade do momento",
    "🎰 Fiquem de olho nessa entrada",
    "🎰 Entrada em observação",
    "🎰 Jogo liberado para análise",
    "🎰 Possível janela interessante",
    "🎰 Movimento favorável agora",
]

CLOSING_VARIANTS = [
    "⚠️ Operação informativa. Use gestão e responsabilidade.",
    "⚠️ Controle a banca e não force entradas.",
    "⚠️ Jogue com responsabilidade e respeite seu limite.",
    "⚠️ Gestão primeiro. Operação sempre com controle.",
]

STRATEGY_VARIANTS = {
    "leve": [
        "💰 Estratégia Premium Leve:\n• 3 giros em bet baixa no normal\n• 5 giros no turbo mantendo a bet\n• Se não responder, faça mais 15 giros no automático\n• Sem insistir além disso",
        "💰 Estratégia Premium Leve:\n• Comece com 3 giros em bet baixa\n• Depois faça 5 giros no turbo\n• Finalize com 15 giros no automático\n• Se não encaixar, aguarde a próxima",
    ],
    "media": [
        "💰 Estratégia Premium Média:\n• 3 giros em bet baixa no normal\n• 5 giros no turbo\n• Sem resposta? suba 1 nível de bet\n• Faça +15 giros no automático",
        "💰 Estratégia Premium Média:\n• Inicie com 3 giros em bet baixa\n• Vá para 5 giros no turbo\n• Suba 1 nível com controle\n• Feche com 15 giros no automático",
    ],
    "agressiva": [
        "💰 Estratégia Premium Agressiva:\n• 3 giros em bet baixa no normal\n• 5 giros no turbo\n• Sem resposta? subir a bet com controle\n• Fazer +15 giros no automático\n• Limite máximo: 6% da banca",
        "💰 Estratégia Premium Agressiva:\n• Comece leve com 3 giros no normal\n• Faça 5 giros no turbo\n• Suba a bet de forma controlada\n• Finalize com 15 giros no automático\n• Nunca ultrapasse 6% da banca",
    ]
}

# =========================================================
# DB
# =========================================================
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def now_br():
    return datetime.now(APP_TZ)


def now_br_str():
    return now_br().strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    return now_br().strftime("%Y-%m-%d")


def today_date():
    return now_br().date()


def parse_hhmm(hhmm: str):
    hh, mm = hhmm.split(":")
    return int(hh), int(mm)


def seed_setting(cur, key, value):
    cur.execute("SELECT id FROM settings WHERE key = ?", (key,))
    if not cur.fetchone():
        cur.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))


def set_setting(key, value):
    conn = db()
    conn.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()


def get_setting(key, default=""):
    conn = db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'client',
            plan TEXT NOT NULL DEFAULT 'Free',
            brand_name TEXT DEFAULT 'Rainha Games',
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price TEXT NOT NULL,
            features TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            provider TEXT NOT NULL,
            rtp TEXT DEFAULT '',
            emoji TEXT DEFAULT '🎰',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_date TEXT NOT NULL,
            position INTEGER NOT NULL,
            game_id INTEGER NOT NULL,
            send_at TEXT NOT NULL,
            sent INTEGER DEFAULT 0,
            sent_at TEXT DEFAULT '',
            telegram_status TEXT DEFAULT '',
            telegram_response TEXT DEFAULT '',
            UNIQUE(plan_date, game_id),
            UNIQUE(plan_date, position)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            send_date TEXT NOT NULL,
            send_time TEXT NOT NULL,
            game_id INTEGER,
            game_name TEXT,
            provider TEXT,
            sent_at TEXT NOT NULL,
            telegram_status TEXT DEFAULT '',
            telegram_response TEXT DEFAULT ''
        )
    """)

    seed_setting(cur, "brand_name", "Rainha Games")
    seed_setting(cur, "footer_text", DEFAULT_FOOTER_TEXT)
    seed_setting(cur, "footer_link", DEFAULT_FOOTER_LINK)
    seed_setting(cur, "theme_primary", "#B3001B")
    seed_setting(cur, "theme_secondary", "#D4AF37")
    seed_setting(cur, "theme_dark", "#0B0B0F")
    seed_setting(cur, "hero_image_url", "")
    seed_setting(cur, "auto_start_time", AUTO_START_TIME)
    seed_setting(cur, "auto_end_time", AUTO_END_TIME)

    cur.execute("SELECT id FROM users WHERE username = ?", (DEFAULT_ADMIN_USER,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (username, password, role, plan, brand_name, created_at)
            VALUES (?, ?, 'admin', 'Premium', 'Rainha Games', ?)
        """, (DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASSWORD, now_br_str()))

    plans = [
        ("Free", "R$ 0,00", "Acesso básico|Painel padrão|Uso simples"),
        ("VIP", "R$ 97,00", "Mais recursos|Mais personalização|Prioridade"),
        ("Premium", "R$ 297,00", "White label|Área admin e cliente|Personalização total"),
    ]
    for name, price, features in plans:
        cur.execute("SELECT id FROM plans WHERE name = ?", (name,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO plans (name, price, features, active)
                VALUES (?, ?, ?, 1)
            """, (name, price, features))

    for name, provider, rtp, emoji in SEED_GAMES:
        cur.execute("SELECT id FROM games WHERE name = ?", (name,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO games (name, provider, rtp, emoji, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, provider, rtp, emoji, now_br_str()))

    conn.commit()
    conn.close()

    ensure_current_start_time()


def ensure_current_start_time():
    desired = AUTO_START_TIME
    current = get_setting("auto_start_time", desired)
    if current != desired:
        set_setting("auto_start_time", desired)


# =========================================================
# AUTH
# =========================================================
def require_login(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Acesso restrito ao administrador.")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped


# =========================================================
# PLANEJAMENTO AUTOMÁTICO
# =========================================================
def stable_seed_for_day(day_str: str):
    digest = hashlib.sha256(day_str.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def choose_strategy_for_position(position: int):
    modes = ["leve", "media", "agressiva"]
    return modes[position % len(modes)]


def choose_variant(items, plan_date: str, game_id: int, salt: str):
    raw = f"{plan_date}|{game_id}|{salt}"
    idx = int(hashlib.sha256(raw.encode("utf-8")).hexdigest(), 16) % len(items)
    return items[idx]


def build_message_for_game(plan_date: str, position: int, game_row):
    intro = choose_variant(INTRO_VARIANTS, plan_date, game_row["id"], "intro")
    closing = choose_variant(CLOSING_VARIANTS, plan_date, game_row["id"], "closing")
    strategy_name = choose_strategy_for_position(position)
    strategy_text = choose_variant(STRATEGY_VARIANTS[strategy_name], plan_date, game_row["id"], "strategy")

    provider_line = f"🏢 Provedora: {game_row['provider']}\n" if game_row["provider"] else ""
    rtp_line = f"📊 RTP: {game_row['rtp']}\n" if game_row["rtp"] else "📊 RTP: Verificado ✅\n"

    return (
        f"{intro}\n\n"
        f"🎮 Jogo: {game_row['name']} {game_row['emoji']}\n"
        f"{provider_line}"
        f"{rtp_line}\n"
        f"{strategy_text}\n\n"
        f"{closing}"
    )


def build_send_slots_for_day(day_str: str, total_games: int):
    if total_games <= 0:
        return []

    start_time = get_setting("auto_start_time", AUTO_START_TIME)
    end_time = get_setting("auto_end_time", AUTO_END_TIME)

    day_obj = datetime.strptime(day_str, "%Y-%m-%d").date()
    sh, sm = parse_hhmm(start_time)
    eh, em = parse_hhmm(end_time)

    start_dt = datetime(day_obj.year, day_obj.month, day_obj.day, sh, sm, 0, tzinfo=APP_TZ)
    end_dt = datetime(day_obj.year, day_obj.month, day_obj.day, eh, em, 0, tzinfo=APP_TZ)

    if end_dt <= start_dt:
        end_dt = start_dt + timedelta(hours=6)

    total_seconds = int((end_dt - start_dt).total_seconds())

    if total_games == 1:
        return [start_dt]

    base_step = max(60, total_seconds // total_games)

    rng = random.Random(stable_seed_for_day(day_str))
    slots = []
    current = start_dt

    for i in range(total_games):
        if i == 0:
            send_time = current
        else:
            jitter = rng.randint(-20, 20)
            send_time = current + timedelta(seconds=jitter)
            if send_time <= slots[-1]:
                send_time = slots[-1] + timedelta(minutes=1)

        if send_time > end_dt:
            send_time = end_dt

        slots.append(send_time)
        current = current + timedelta(seconds=base_step)

    for i in range(1, len(slots)):
        if slots[i] <= slots[i - 1]:
            slots[i] = slots[i - 1] + timedelta(minutes=1)

    overflow = slots[-1] - end_dt
    if overflow.total_seconds() > 0:
        shift_back = int(overflow.total_seconds())
        slots = [dt - timedelta(seconds=shift_back) for dt in slots]

    return slots


def ensure_daily_plan(day_str: str):
    conn = db()
    existing = conn.execute("""
        SELECT COUNT(*) AS total
        FROM daily_plan
        WHERE plan_date = ?
    """, (day_str,)).fetchone()["total"]

    if existing > 0:
        conn.close()
        return

    games = conn.execute("SELECT * FROM games ORDER BY provider, name").fetchall()
    if not games:
        conn.close()
        return

    games_list = list(games)
    rng = random.Random(stable_seed_for_day(day_str))
    rng.shuffle(games_list)

    slots = build_send_slots_for_day(day_str, len(games_list))

    for position, game_row in enumerate(games_list, start=1):
        send_at = slots[position - 1].strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            INSERT OR IGNORE INTO daily_plan
            (plan_date, position, game_id, send_at, sent, sent_at, telegram_status, telegram_response)
            VALUES (?, ?, ?, ?, 0, '', '', '')
        """, (day_str, position, game_row["id"], send_at))

    conn.commit()
    conn.close()


def get_due_unsent_items(limit=5):
    day_str = today_str()
    ensure_daily_plan(day_str)

    conn = db()
    rows = conn.execute("""
        SELECT dp.*, g.name AS game_name, g.provider, g.rtp, g.emoji
        FROM daily_plan dp
        JOIN games g ON g.id = dp.game_id
        WHERE dp.plan_date = ?
          AND dp.sent = 0
          AND dp.send_at <= ?
        ORDER BY dp.position ASC
        LIMIT ?
    """, (day_str, now_br_str(), limit)).fetchall()
    conn.close()
    return rows


def log_send(plan_row, ok, response):
    conn = db()

    conn.execute("""
        UPDATE daily_plan
        SET sent = 1,
            sent_at = ?,
            telegram_status = ?,
            telegram_response = ?
        WHERE id = ?
    """, (
        now_br_str(),
        "ok" if ok else "erro",
        (response or "")[:1000],
        plan_row["id"]
    ))

    conn.execute("""
        INSERT INTO sent_log
        (send_date, send_time, game_id, game_name, provider, sent_at, telegram_status, telegram_response)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        today_str(),
        datetime.strptime(plan_row["send_at"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M"),
        plan_row["game_id"],
        plan_row["game_name"],
        plan_row["provider"],
        now_br_str(),
        "ok" if ok else "erro",
        (response or "")[:1000]
    ))

    conn.commit()
    conn.close()


# =========================================================
# TELEGRAM
# =========================================================
def telegram_send(text, image_url=""):
    if not TOKEN or not CHAT_ID:
        return False, "TOKEN ou CHAT_ID não configurados."

    footer_link = get_setting("footer_link", DEFAULT_FOOTER_LINK)
    footer_text = get_setting("footer_text", DEFAULT_FOOTER_TEXT)

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": footer_text,
                    "url": footer_link
                }
            ]
        ]
    }

    try:
        if image_url.strip():
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            data = {
                "chat_id": CHAT_ID,
                "photo": image_url.strip(),
                "caption": text[:1024],
                "reply_markup": json.dumps(keyboard)
            }
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": text,
                "reply_markup": json.dumps(keyboard)
            }

        resp = requests.post(url, data=data, timeout=30)
        ok = resp.status_code == 200
        return ok, f"{resp.status_code} - {resp.text[:600]}"
    except Exception as e:
        return False, str(e)


# =========================================================
# LOOP AUTOMÁTICO
# =========================================================
def scheduler_loop():
    while True:
        try:
            ensure_current_start_time()
            ensure_daily_plan(today_str())
            tomorrow = (today_date() + timedelta(days=1)).strftime("%Y-%m-%d")
            ensure_daily_plan(tomorrow)

            due_items = get_due_unsent_items(limit=10)
            hero_image_url = get_setting("hero_image_url", "").strip()

            for item in due_items:
                msg = build_message_for_game(
                    plan_date=item["plan_date"],
                    position=item["position"],
                    game_row={
                        "id": item["game_id"],
                        "name": item["game_name"],
                        "provider": item["provider"],
                        "rtp": item["rtp"],
                        "emoji": item["emoji"],
                    }
                )
                ok, response = telegram_send(msg, hero_image_url)
                log_send(item, ok, response)

            time.sleep(SCHEDULER_SLEEP_SECONDS)
        except Exception:
            time.sleep(SCHEDULER_SLEEP_SECONDS)


# =========================================================
# UI
# =========================================================
BASE_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<style>
:root{
    --primary: {{ theme_primary }};
    --secondary: {{ theme_secondary }};
    --dark: {{ theme_dark }};
    --dark2: #14141c;
    --light: #f6f1df;
    --danger: #ff5e5e;
    --success: #39d98a;
}
*{box-sizing:border-box}
body{
    margin:0;
    font-family:Arial, Helvetica, sans-serif;
    background:linear-gradient(180deg, var(--dark) 0%, #111 100%);
    color:#fff;
}
.topbar{
    background:#09090d;
    border-bottom:1px solid rgba(212,175,55,.25);
    padding:16px 22px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    position:sticky;
    top:0;
    z-index:9;
}
.brand{
    font-size:22px;
    font-weight:700;
    color:var(--secondary);
}
.top-actions a{
    color:#fff;
    text-decoration:none;
    margin-left:12px;
    padding:10px 14px;
    border-radius:12px;
    background:rgba(255,255,255,.06);
    display:inline-block;
}
.container{
    max-width:1280px;
    margin:0 auto;
    padding:24px;
}
.grid{
    display:grid;
    gap:18px;
}
.grid-2{
    grid-template-columns:1.15fr .85fr;
}
.grid-3{
    grid-template-columns:repeat(3, 1fr);
}
.card{
    background:var(--dark2);
    border:1px solid rgba(212,175,55,.18);
    border-radius:24px;
    padding:20px;
    box-shadow:0 10px 30px rgba(0,0,0,.25);
}
.card h2, .card h3{
    margin:0 0 14px 0;
    color:var(--secondary);
}
.kpi{
    font-size:30px;
    font-weight:700;
    margin-top:10px;
}
.sub{
    color:#d7d7d7;
    font-size:14px;
}
form input, form select, form textarea{
    width:100%;
    background:#0e0e14;
    color:#fff;
    border:1px solid rgba(212,175,55,.18);
    border-radius:14px;
    padding:12px 14px;
    margin:8px 0 14px 0;
    outline:none;
}
form textarea{
    min-height:110px;
    resize:vertical;
}
button, .btn{
    background:linear-gradient(180deg, var(--secondary) 0%, #b58d10 100%);
    color:#111;
    border:none;
    border-radius:14px;
    padding:12px 16px;
    font-weight:700;
    cursor:pointer;
    text-decoration:none;
    display:inline-block;
}
.table-wrap{
    overflow:auto;
}
table{
    width:100%;
    border-collapse:collapse;
}
th, td{
    padding:12px;
    border-bottom:1px solid rgba(255,255,255,.08);
    text-align:left;
    vertical-align:top;
}
th{
    color:var(--secondary);
    font-size:14px;
}
.badge{
    display:inline-block;
    padding:6px 10px;
    border-radius:999px;
    font-size:12px;
    font-weight:700;
}
.badge-success{ background:rgba(57,217,138,.12); color:var(--success);}
.badge-gold{ background:rgba(212,175,55,.12); color:var(--secondary);}
.flash{
    margin-bottom:16px;
    padding:14px 16px;
    border-radius:14px;
    background:rgba(255,255,255,.07);
}
.preview{
    white-space:pre-wrap;
    background:#0e0e14;
    padding:16px;
    border-radius:18px;
    border:1px solid rgba(212,175,55,.14);
}
.muted{
    color:#bdbdbd;
    font-size:13px;
}
@media (max-width: 980px){
    .grid-2, .grid-3{
        grid-template-columns:1fr;
    }
}
</style>
</head>
<body>
<div class="topbar">
    <div class="brand">👑 {{ brand_name }}</div>
    <div class="top-actions">
        {% if session.get('user_id') %}
            <a href="{{ url_for('dashboard') }}">Painel</a>
            {% if session.get('role') == 'admin' %}
                <a href="{{ url_for('admin_users') }}">Usuários</a>
                <a href="{{ url_for('sales_plans') }}">Plano de vendas</a>
                <a href="{{ url_for('admin_settings') }}">Configurações</a>
            {% endif %}
            <a href="{{ url_for('logout') }}">Sair</a>
        {% endif %}
    </div>
</div>
<div class="container">
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for m in messages %}
                <div class="flash">{{ m }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    {{ content|safe }}
</div>
</body>
</html>
"""


def render_page(title, content):
    return render_template_string(
        BASE_HTML,
        title=title,
        content=content,
        brand_name=get_setting("brand_name", "Rainha Games"),
        theme_primary=get_setting("theme_primary", "#B3001B"),
        theme_secondary=get_setting("theme_secondary", "#D4AF37"),
        theme_dark=get_setting("theme_dark", "#0B0B0F"),
        session=session
    )


# =========================================================
# ROUTES
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = db()
        user = conn.execute("""
            SELECT * FROM users
            WHERE username = ? AND password = ? AND is_active = 1
            LIMIT 1
        """, (username, password)).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["plan"] = user["plan"]
            return redirect(url_for("dashboard"))

        flash("Login inválido.")
        return redirect(url_for("login"))

    html = """
    <div class="grid">
        <div class="card" style="max-width:520px;margin:40px auto;">
            <h2>Entrar no sistema</h2>
            <form method="post">
                <label>Usuário</label>
                <input name="username" placeholder="Digite seu usuário" required>
                <label>Senha</label>
                <input name="password" type="password" placeholder="Digite sua senha" required>
                <button type="submit">Entrar</button>
            </form>
            <div class="muted" style="margin-top:12px;">
                Login padrão do admin: use as variáveis ADMIN_USER e ADMIN_PASSWORD.
            </div>
        </div>
    </div>
    """
    return render_page("Login", html)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@require_login
def dashboard():
    ensure_daily_plan(today_str())

    conn = db()
    total_games = conn.execute("SELECT COUNT(*) AS total FROM games").fetchone()["total"]
    total_users = conn.execute("SELECT COUNT(*) AS total FROM users WHERE is_active = 1").fetchone()["total"]
    sent_today = conn.execute("SELECT COUNT(*) AS total FROM daily_plan WHERE plan_date = ? AND sent = 1", (today_str(),)).fetchone()["total"]
    pending_today = conn.execute("SELECT COUNT(*) AS total FROM daily_plan WHERE plan_date = ? AND sent = 0", (today_str(),)).fetchone()["total"]
    first_time = conn.execute("SELECT send_at FROM daily_plan WHERE plan_date = ? ORDER BY position ASC LIMIT 1", (today_str(),)).fetchone()
    last_time = conn.execute("SELECT send_at FROM daily_plan WHERE plan_date = ? ORDER BY position DESC LIMIT 1", (today_str(),)).fetchone()
    last_log = conn.execute("SELECT * FROM sent_log ORDER BY id DESC LIMIT 1").fetchone()
    next_item = conn.execute("""
        SELECT dp.*, g.name AS game_name, g.provider, g.rtp, g.emoji
        FROM daily_plan dp
        JOIN games g ON g.id = dp.game_id
        WHERE dp.plan_date = ? AND dp.sent = 0
        ORDER BY dp.position ASC
        LIMIT 1
    """, (today_str(),)).fetchone()
    recent_logs = conn.execute("""
        SELECT * FROM sent_log
        ORDER BY id DESC
        LIMIT 12
    """).fetchall()
    conn.close()

    preview = "Nenhuma prévia disponível."
    if next_item:
        preview = build_message_for_game(
            plan_date=next_item["plan_date"],
            position=next_item["position"],
            game_row={
                "id": next_item["game_id"],
                "name": next_item["game_name"],
                "provider": next_item["provider"],
                "rtp": next_item["rtp"],
                "emoji": next_item["emoji"],
            }
        )

    rows_html = ""
    for row in recent_logs:
        status_badge = "badge-success" if row["telegram_status"] == "ok" else "badge-gold"
        rows_html += f"""
        <tr>
            <td>{row["send_date"]}</td>
            <td>{row["send_time"]}</td>
            <td>{row["game_name"] or "-"}</td>
            <td>{row["provider"] or "-"}</td>
            <td><span class="badge {status_badge}">{row["telegram_status"] or "-"}</span></td>
        </tr>
        """

    first_time_text = datetime.strptime(first_time["send_at"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M") if first_time else "-"
    last_time_text = datetime.strptime(last_time["send_at"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M") if last_time else "-"

    html = f"""
    <div class="grid grid-3">
        <div class="card">
            <div class="sub">Jogos no catálogo</div>
            <div class="kpi">{total_games}</div>
        </div>
        <div class="card">
            <div class="sub">Envios feitos hoje</div>
            <div class="kpi">{sent_today}</div>
        </div>
        <div class="card">
            <div class="sub">Pendentes hoje</div>
            <div class="kpi">{pending_today}</div>
        </div>
    </div>

    <div class="grid grid-2" style="margin-top:18px;">
        <div class="card">
            <h2>Próxima mensagem automática</h2>
            <div class="preview">{preview}</div>
            <div class="muted" style="margin-top:12px;">
                O botão "{get_setting("footer_text", DEFAULT_FOOTER_TEXT)}" é enviado automaticamente em todas as mensagens.
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Status do sistema</h3>
                <div class="sub">Horário atual Brasil</div>
                <div class="kpi">{now_br().strftime("%H:%M:%S")}</div>

                <div class="sub" style="margin-top:12px;">Janela automática interna</div>
                <div class="preview">{get_setting("auto_start_time", AUTO_START_TIME)} até {get_setting("auto_end_time", AUTO_END_TIME)}</div>

                <div class="sub" style="margin-top:12px;">Primeiro horário de hoje</div>
                <div>{first_time_text}</div>

                <div class="sub" style="margin-top:12px;">Último horário de hoje</div>
                <div>{last_time_text}</div>
            </div>

            <div class="card">
                <h3>Último envio</h3>
                <div class="sub">Jogo</div>
                <div>{last_log["game_name"] if last_log else "Ainda não houve envio"}</div>

                <div class="sub" style="margin-top:10px;">Hora</div>
                <div>{last_log["send_time"] if last_log else "-"}</div>

                <div class="sub" style="margin-top:10px;">Status</div>
                <div>{last_log["telegram_status"] if last_log else "-"}</div>
            </div>
        </div>
    </div>

    <div class="card" style="margin-top:18px;">
        <h3>Ações rápidas</h3>
        <a class="btn" href="/admin/test-send">Enviar teste agora</a>
        <a class="btn" href="/admin/rebuild-plan" style="margin-left:10px;">Regerar agenda de hoje</a>
    </div>

    <div class="card" style="margin-top:18px;">
        <h3>Últimos envios</h3>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Hora</th>
                        <th>Jogo</th>
                        <th>Provedora</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
    </div>
    """
    return render_page("Painel", html)


@app.route("/planos")
@require_admin
def sales_plans():
    conn = db()
    rows = conn.execute("SELECT * FROM plans WHERE active = 1 ORDER BY id ASC").fetchall()
    conn.close()

    cards = ""
    for row in rows:
        features = "".join(f"<div>• {f}</div>" for f in row["features"].split("|"))
        cards += f"""
        <div class="card">
            <h3>{row['name']}</h3>
            <div class="kpi" style="font-size:26px;">{row['price']}</div>
            <div class="preview" style="margin-top:12px;">{features}</div>
        </div>
        """

    html = f"""
    <div class="card">
        <h2>Plano de vendas</h2>
    </div>
    <div class="grid grid-3" style="margin-top:18px;">
        {cards}
    </div>
    """
    return render_page("Plano de vendas", html)


@app.route("/admin/users", methods=["GET", "POST"])
@require_admin
def admin_users():
    conn = db()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "client").strip()
        plan = request.form.get("plan", "Free").strip()
        brand_name = request.form.get("brand_name", "Rainha Games").strip() or "Rainha Games"

        if username and password:
            try:
                conn.execute("""
                    INSERT INTO users (username, password, role, plan, brand_name, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, password, role, plan, brand_name, now_br_str()))
                conn.commit()
                flash("Usuário criado com sucesso.")
            except sqlite3.IntegrityError:
                flash("Esse usuário já existe.")
        else:
            flash("Preencha usuário e senha.")

    rows = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    conn.close()

    trs = ""
    for u in rows:
        badge = "badge-gold" if u["role"] == "admin" else "badge-success"
        trs += f"""
        <tr>
            <td>{u['id']}</td>
            <td>{u['username']}</td>
            <td><span class="badge {badge}">{u['role']}</span></td>
            <td>{u['plan']}</td>
            <td>{u['brand_name']}</td>
            <td>{"Ativo" if u['is_active'] else "Inativo"}</td>
        </tr>
        """

    html = f"""
    <div class="grid grid-2">
        <div class="card">
            <h2>Novo usuário</h2>
            <form method="post">
                <label>Usuário</label>
                <input name="username" required>
                <label>Senha</label>
                <input name="password" required>
                <label>Perfil</label>
                <select name="role">
                    <option value="client">Cliente</option>
                    <option value="admin">Admin</option>
                </select>
                <label>Plano</label>
                <select name="plan">
                    <option>Free</option>
                    <option>VIP</option>
                    <option>Premium</option>
                </select>
                <label>Marca do cliente</label>
                <input name="brand_name" value="Rainha Games">
                <button type="submit">Criar usuário</button>
            </form>
        </div>
        <div class="card">
            <h2>Usuários cadastrados</h2>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Usuário</th>
                            <th>Perfil</th>
                            <th>Plano</th>
                            <th>Marca</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>{trs}</tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return render_page("Usuários", html)


@app.route("/admin/settings", methods=["GET", "POST"])
@require_admin
def admin_settings():
    if request.method == "POST":
        set_setting("brand_name", request.form.get("brand_name", "Rainha Games").strip() or "Rainha Games")
        set_setting("footer_text", request.form.get("footer_text", DEFAULT_FOOTER_TEXT).strip() or DEFAULT_FOOTER_TEXT)
        set_setting("footer_link", request.form.get("footer_link", DEFAULT_FOOTER_LINK).strip() or DEFAULT_FOOTER_LINK)
        set_setting("theme_primary", request.form.get("theme_primary", "#B3001B").strip() or "#B3001B")
        set_setting("theme_secondary", request.form.get("theme_secondary", "#D4AF37").strip() or "#D4AF37")
        set_setting("theme_dark", request.form.get("theme_dark", "#0B0B0F").strip() or "#0B0B0F")
        set_setting("hero_image_url", request.form.get("hero_image_url", "").strip())
        flash("Configurações salvas.")
        return redirect(url_for("admin_settings"))

    html = f"""
    <div class="card">
        <h2>Configurações</h2>
        <form method="post">
            <label>Nome da marca</label>
            <input name="brand_name" value="{get_setting('brand_name', 'Rainha Games')}">

            <label>Texto do botão</label>
            <input name="footer_text" value="{get_setting('footer_text', DEFAULT_FOOTER_TEXT)}">

            <label>Link do botão</label>
            <input name="footer_link" value="{get_setting('footer_link', DEFAULT_FOOTER_LINK)}">

            <label>URL da imagem opcional para envios</label>
            <input name="hero_image_url" value="{get_setting('hero_image_url', '')}" placeholder="https://...">

            <label>Cor principal</label>
            <input name="theme_primary" value="{get_setting('theme_primary', '#B3001B')}">

            <label>Cor secundária</label>
            <input name="theme_secondary" value="{get_setting('theme_secondary', '#D4AF37')}">

            <label>Cor escura</label>
            <input name="theme_dark" value="{get_setting('theme_dark', '#0B0B0F')}">

            <button type="submit">Salvar configurações</button>
        </form>
    </div>
    """
    return render_page("Configurações", html)


@app.route("/admin/test-send")
@require_admin
def admin_test_send():
    ensure_daily_plan(today_str())

    conn = db()
    next_item = conn.execute("""
        SELECT dp.*, g.name AS game_name, g.provider, g.rtp, g.emoji
        FROM daily_plan dp
        JOIN games g ON g.id = dp.game_id
        WHERE dp.plan_date = ? AND dp.sent = 0
        ORDER BY dp.position ASC
        LIMIT 1
    """, (today_str(),)).fetchone()
    conn.close()

    if not next_item:
        flash("Não há item pendente para teste hoje.")
        return redirect(url_for("dashboard"))

    msg = build_message_for_game(
        plan_date=next_item["plan_date"],
        position=next_item["position"],
        game_row={
            "id": next_item["game_id"],
            "name": next_item["game_name"],
            "provider": next_item["provider"],
            "rtp": next_item["rtp"],
            "emoji": next_item["emoji"],
        }
    )

    hero_image_url = get_setting("hero_image_url", "").strip()
    ok, response = telegram_send(msg, hero_image_url)

    flash("Teste enviado com sucesso." if ok else f"Falha no teste: {response}")
    return redirect(url_for("dashboard"))


@app.route("/admin/rebuild-plan")
@require_admin
def admin_rebuild_plan():
    conn = db()
    conn.execute("DELETE FROM daily_plan WHERE plan_date = ? AND sent = 0", (today_str(),))
    conn.commit()
    conn.close()

    ensure_daily_plan(today_str())
    flash("Agenda automática de hoje foi regerada.")
    return redirect(url_for("dashboard"))


# =========================================================
# START
# =========================================================
def start_scheduler():
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()


init_db()
start_scheduler()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
