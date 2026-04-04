from pathlib import Path

app_code = r'''from flask import Flask, request, redirect, url_for, session, render_template_string, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import sqlite3
import json
import os
import random
import threading
import time
import requests

# =========================================================
# CONFIGURAÇÕES GERAIS
# =========================================================
APP_NAME = "Painel Premium"
DB_PATH = os.getenv("DB_PATH", "painel_premium.db")
SECRET_KEY = os.getenv("SECRET_KEY", "troque_esta_chave_por_uma_bem_forte")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "America/Sao_Paulo")

app = Flask(__name__)
app.secret_key = SECRET_KEY

# =========================================================
# DADOS PADRÃO - ESTILO PREMIUM
# =========================================================
DEFAULT_HEADERS = [
    "╔══════════════════╗\n🎰  ENTRADA LIBERADA  🎰\n╚══════════════════╝",
    "🔥━━━━━━━━━━━━━━━━━🔥\n⚡   SINAL CONFIRMADO   ⚡\n🔥━━━━━━━━━━━━━━━━━🔥",
    "┌─────────────────────┐\n💎   ENTRADA PREMIUM   💎\n└─────────────────────┘",
    "🌟══════════════════🌟\n🎯  OPORTUNIDADE DO MOMENTO  🎯\n🌟══════════════════🌟",
    "╭──────────────────────╮\n👑   PAINEL PREMIUM   👑\n╰──────────────────────╯",
    "🏆▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬🏆\n💰  ENTRADA VIP  💰\n🏆▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬🏆",
]

DEFAULT_FOOTERS = [
    "⚠️ Use gestão de banca.\n🛑 Pare ao bater seu limite.\n💎 Disciplina vem antes do lucro.",
    "🧠 Entrada boa é entrada com controle.\n💰 Respeite seu gerenciamento.\n⚠️ Nunca force operação.",
    "📌 Siga a sequência completa.\n🛑 Não ultrapasse o limite da entrada.\n🔥 Consistência sempre.",
    "💎 Faça exatamente o passo a passo.\n⚠️ Sem ansiedade e sem exagero.\n🎯 Gestão é prioridade.",
]

DEFAULT_PREMIUM_STRATEGIES = [
    """💎 ESTILO PREMIUM — LEVE

🎯 Momento da entrada:
Aguarde 3 rodadas sem bônus ou sem destaque.

🎰 Execução:
➡️ 3 giros no modo normal com bet baixa
➡️ 5 giros no turbo mantendo a mesma bet
➡️ Se não bater, suba 1 nível de bet
➡️ Faça mais 15 giros no automático

🛑 Encerramento:
Pare ao finalizar essa sequência.""",

    """💎 ESTILO PREMIUM — LEVE

🎯 Momento da entrada:
Observe 4 rodadas comuns antes de entrar.

🎰 Execução:
➡️ 5 giros no modo normal com entrada leve
➡️ 5 giros no turbo sem alterar a bet
➡️ Se continuar frio, aumente levemente a bet
➡️ 10 giros no automático

🛑 Encerramento:
Máximo de 1 progressão nesta entrada.""",

    """💎 ESTILO PREMIUM — LEVE

🎯 Momento da entrada:
Entre após 2 rodadas fracas seguidas.

🎰 Execução:
➡️ 3 giros no normal com bet baixa
➡️ 3 giros no turbo
➡️ Suba a bet apenas se não houver resposta
➡️ 12 giros no automático

🛑 Encerramento:
Se não reagir após a sequência, encerre.""",

    """💎 ESTILO PREMIUM — MÉDIA

🎯 Momento da entrada:
Aguarde 3 perdas consecutivas no jogo.

🎰 Execução:
➡️ 4 giros no normal com bet controlada
➡️ 6 giros no turbo
➡️ Se não vier resultado, suba a bet
➡️ Faça 15 giros no automático
➡️ Finalize com 3 giros manuais no normal

🛑 Encerramento:
Máximo de 1 aumento de bet por entrada.""",

    """💎 ESTILO PREMIUM — MÉDIA

🎯 Momento da entrada:
Entre depois de 5 rodadas comuns sem destaque.

🎰 Execução:
➡️ 5 giros no normal com bet média
➡️ 5 giros no turbo
➡️ Aumente a bet em 1 nível
➡️ Faça mais 15 giros no automático

🛑 Encerramento:
Bateu lucro, encerre sem insistir.""",

    """💎 ESTILO PREMIUM — MÉDIA

🎯 Momento da entrada:
Observe o jogo e entre após sequência fraca.

🎰 Execução:
➡️ 3 giros no normal
➡️ 7 giros no turbo
➡️ Se não pagar, suba a bet
➡️ 15 giros no automático
➡️ Se pagar parcial, volte para bet inicial

🛑 Encerramento:
Sem segunda caça após perder a janela.""",

    """💎 ESTILO PREMIUM — MÉDIA

🎯 Momento da entrada:
Entre após 3 giros secos e ambiente morno.

🎰 Execução:
➡️ 5 giros no normal com bet média
➡️ 5 giros no turbo
➡️ Suba 1 nível de bet
➡️ 12 giros no automático
➡️ 5 giros finais no turbo

🛑 Encerramento:
Finalizou a sequência, pare e reavalie.""",

    """💎 ESTILO PREMIUM — AGRESSIVA

🎯 Momento da entrada:
Entre após 4 perdas seguidas e mantenha foco na execução.

🎰 Execução:
➡️ 5 giros no normal com bet média
➡️ 5 giros no turbo
➡️ Suba a bet em 1 nível
➡️ Faça 20 giros no automático
➡️ Se reagir, reduza para a bet inicial

🛑 Encerramento:
Máximo de 1 ataque por sinal.""",

    """💎 ESTILO PREMIUM — AGRESSIVA

🎯 Momento da entrada:
Espere 5 rodadas fracas antes de iniciar.

🎰 Execução:
➡️ 3 giros no normal com bet média
➡️ 7 giros no turbo
➡️ Suba a bet
➡️ 20 giros no automático
➡️ Termine com 5 giros no turbo

🛑 Encerramento:
Se não responder, pare sem recuperar no impulso.""",

    """💎 ESTILO PREMIUM — AGRESSIVA

🎯 Momento da entrada:
Entre quando o jogo estiver apagado por várias rodadas.

🎰 Execução:
➡️ 5 giros no normal
➡️ 5 giros no turbo
➡️ Aumente a bet em 1 nível
➡️ 15 giros no automático
➡️ Aumente mais 1 nível apenas se o cliente aceitar risco
➡️ Feche com 10 giros no automático

🛑 Encerramento:
Estratégia agressiva exige limite definido antes de entrar.""",

    """💎 ESTILO PREMIUM — AGRESSIVA

🎯 Momento da entrada:
Aguarde 3 perdas seguidas e entre sem pular etapas.

🎰 Execução:
➡️ 4 giros no normal
➡️ 6 giros no turbo
➡️ Suba a bet
➡️ 18 giros no automático
➡️ Se houver pagamento parcial, mantenha a sequência e não dobre de novo

🛑 Encerramento:
Nunca faça mais de 2 aumentos na mesma entrada.""",

    """💎 ESTILO PREMIUM — LEVE

🎯 Momento da entrada:
Entre após observar 5 rodadas e sentir o jogo morno.

🎰 Execução:
➡️ 3 giros no normal com bet baixa
➡️ 5 giros no turbo
➡️ Se não der sinal, aumente pouco a bet
➡️ 8 giros no automático

🛑 Encerramento:
Sem insistência além dessa janela.""",

    """💎 ESTILO PREMIUM — MÉDIA

🎯 Momento da entrada:
Faça a entrada após 4 rodadas comuns.

🎰 Execução:
➡️ 4 giros no normal
➡️ 4 giros no turbo
➡️ Suba a bet em 1 nível
➡️ 15 giros no automático
➡️ Volte para a bet anterior se vier lucro parcial

🛑 Encerramento:
Ao fim da sequência, encerre a tentativa.""",

    """💎 ESTILO PREMIUM — LEVE

🎯 Momento da entrada:
Entre após 2 perdas e 1 rodada neutra.

🎰 Execução:
➡️ 3 giros no normal com bet baixa
➡️ 4 giros no turbo
➡️ Suba a bet com cautela
➡️ 10 giros no automático

🛑 Encerramento:
Se não reagir, aguarde nova oportunidade.""",

    """💎 ESTILO PREMIUM — MÉDIA

🎯 Momento da entrada:
Aguarde 3 rodadas secas seguidas.

🎰 Execução:
➡️ 5 giros no normal
➡️ 5 giros no turbo
➡️ 1 aumento de bet
➡️ 15 giros no automático
➡️ Encerramento imediato ao atingir meta curta

🛑 Encerramento:
Não repita a mesma entrada em sequência.""",
]

DEFAULT_GAMES = {
    "Fortune Tiger": "🐯",
    "Fortune Rabbit": "🐰",
    "Fortune Dragon": "🐉",
    "Fortune Mouse": "🐭",
    "Fortune Ox": "🐂",
    "Fortune Horse": "🐴",
    "Fortune Snake": "🐍",
    "Mahjong Ways": "🀄",
    "Wild Bandito": "🤠💥",
    "Treasures of Aztec": "🏺⚡",
    "Candy Bonanza": "🍬💥",
    "Leprechaun Riches": "🍀💛",
    "Gates of Olympus": "⚡",
    "Sweet Bonanza": "🍬",
    "Big Bass Bonanza": "🐟",
    "The Dog House": "🐕",
    "Starlight Princess": "⭐",
    "Sugar Rush": "🍭",
    "Floating Dragon": "🐉🌊",
    "Wild West Gold": "🤠🌵",
    "Joker's Jewels": "🃏💎",
    "Aviator": "✈️💰",
    "Plinko": "🎯💸",
    "Mines": "💣⚠️",
    "Dice": "🎲💰",
    "Twerk": "💃🎵",
    "Lucky Panda": "🐼🍀",
    "Book of Ra": "📖☀️",
    "Wanted Dead or a Wild": "🤠🔫",
    "Chaos Crew": "🦹💣",
}

SEPARATOR = "\n---\n"

# =========================================================
# BANCO DE DADOS
# =========================================================
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'client',
            active INTEGER NOT NULL DEFAULT 1,
            brand_name TEXT NOT NULL DEFAULT 'Painel Premium',
            brand_subtitle TEXT NOT NULL DEFAULT 'Sistema automático com marca própria',
            primary_color TEXT NOT NULL DEFAULT '#8b0000',
            secondary_color TEXT NOT NULL DEFAULT '#111111',
            accent_color TEXT NOT NULL DEFAULT '#d4af37',
            logo_url TEXT DEFAULT '',
            expires_at TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            telegram_token TEXT DEFAULT '',
            telegram_chat_id TEXT DEFAULT '',
            start_hour INTEGER NOT NULL DEFAULT 14,
            start_minute INTEGER NOT NULL DEFAULT 40,
            timezone TEXT NOT NULL DEFAULT 'America/Sao_Paulo',
            bot_enabled INTEGER NOT NULL DEFAULT 0,
            headers_json TEXT NOT NULL,
            footers_json TEXT NOT NULL,
            strategies_json TEXT NOT NULL,
            games_json TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS send_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            cycle_id TEXT NOT NULL,
            scheduled_at TEXT NOT NULL,
            sent_at TEXT,
            game_name TEXT NOT NULL,
            message_text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'scheduled',
            response_code TEXT DEFAULT '',
            response_text TEXT DEFAULT '',
            UNIQUE(user_id, cycle_id, game_name, scheduled_at),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # cria admin inicial
    admin = cur.execute("SELECT * FROM users WHERE username = ?", (ADMIN_USER,)).fetchone()
    if not admin:
        now = datetime.now().isoformat()
        cur.execute("""
            INSERT INTO users (
                username, password_hash, role, active, brand_name, brand_subtitle,
                primary_color, secondary_color, accent_color, logo_url, expires_at, created_at
            ) VALUES (?, ?, 'admin', 1, ?, ?, ?, ?, ?, '', '', ?)
        """, (
            ADMIN_USER,
            generate_password_hash(ADMIN_PASSWORD),
            "Painel Administrativo",
            "Controle premium de clientes",
            "#8b0000",
            "#111111",
            "#d4af37",
            now,
        ))
        admin_id = cur.lastrowid
        create_default_bot_settings(conn, admin_id)
        conn.commit()

    conn.close()


def create_default_bot_settings(conn, user_id):
    conn.execute("""
        INSERT OR IGNORE INTO bot_settings (
            user_id, telegram_token, telegram_chat_id, start_hour, start_minute,
            timezone, bot_enabled, headers_json, footers_json, strategies_json, games_json
        ) VALUES (?, '', '', 14, 40, ?, 0, ?, ?, ?, ?)
    """, (
        user_id,
        DEFAULT_TIMEZONE,
        json.dumps(DEFAULT_HEADERS, ensure_ascii=False),
        json.dumps(DEFAULT_FOOTERS, ensure_ascii=False),
        json.dumps(DEFAULT_PREMIUM_STRATEGIES, ensure_ascii=False),
        json.dumps(DEFAULT_GAMES, ensure_ascii=False),
    ))


# =========================================================
# HELPERS
# =========================================================
def parse_json_field(value, fallback):
    try:
        data = json.loads(value) if value else fallback
        return data if data else fallback
    except Exception:
        return fallback


def serialize_blocks(text):
    items = [item.strip() for item in text.split(SEPARATOR) if item.strip()]
    return items


def blocks_to_text(items):
    return SEPARATOR.join(items)


def get_user_with_settings(user_id):
    conn = get_db()
    row = conn.execute("""
        SELECT
            u.*,
            b.telegram_token,
            b.telegram_chat_id,
            b.start_hour,
            b.start_minute,
            b.timezone,
            b.bot_enabled,
            b.headers_json,
            b.footers_json,
            b.strategies_json,
            b.games_json
        FROM users u
        LEFT JOIN bot_settings b ON b.user_id = u.id
        WHERE u.id = ?
    """, (user_id,)).fetchone()
    conn.close()
    return row


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_with_settings(user_id)


def is_subscription_valid(user_row):
    if not user_row:
        return False
    if int(user_row["active"]) != 1:
        return False
    expires_at = (user_row["expires_at"] or "").strip()
    if not expires_at:
        return True
    try:
        return datetime.fromisoformat(expires_at) >= datetime.now()
    except Exception:
        return True


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for("login"))
        if user["role"] != "admin":
            flash("Acesso permitido apenas para administradora.")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapper


def brand_theme(user=None):
    if not user:
        return {
            "brand_name": "Painel Premium",
            "brand_subtitle": "Sistema multiusuário com marca própria",
            "primary_color": "#8b0000",
            "secondary_color": "#111111",
            "accent_color": "#d4af37",
            "logo_url": "",
        }
    return {
        "brand_name": user["brand_name"] or "Painel Premium",
        "brand_subtitle": user["brand_subtitle"] or "Sistema premium",
        "primary_color": user["primary_color"] or "#8b0000",
        "secondary_color": user["secondary_color"] or "#111111",
        "accent_color": user["accent_color"] or "#d4af37",
        "logo_url": user["logo_url"] or "",
    }


def tz_now(tz_name):
    try:
        return datetime.now(ZoneInfo(tz_name))
    except Exception:
        return datetime.now(ZoneInfo(DEFAULT_TIMEZONE))


def get_cycle_start(now_dt, start_hour, start_minute):
    cycle_start = now_dt.replace(hour=int(start_hour), minute=int(start_minute), second=0, microsecond=0)
    if now_dt < cycle_start:
        cycle_start -= timedelta(days=1)
    return cycle_start


def get_cycle_id(now_dt, start_hour, start_minute):
    cycle_start = get_cycle_start(now_dt, start_hour, start_minute)
    return cycle_start.strftime("%Y-%m-%d %H:%M"), cycle_start


def get_cycle_label(cycle_start):
    cycle_end = cycle_start + timedelta(days=1) - timedelta(minutes=1)
    return f"{cycle_start.strftime('%d/%m %H:%M')} até {cycle_end.strftime('%d/%m %H:%M')}"


def generate_schedule(user_row, cycle_id, cycle_start):
    games = parse_json_field(user_row["games_json"], DEFAULT_GAMES)
    game_names = list(games.keys())
    if not game_names:
        return []

    rng = random.Random(f"{user_row['id']}-{cycle_id}")
    shuffled = game_names[:]
    rng.shuffle(shuffled)

    interval_seconds = max(1, int((24 * 60 * 60) / len(shuffled)))
    used_offsets = set()
    schedule = []

    for idx, game_name in enumerate(shuffled):
        start_window = idx * interval_seconds
        end_window = max(start_window, ((idx + 1) * interval_seconds) - 1)
        offset = rng.randint(start_window, end_window)
        while offset in used_offsets:
            offset += 1
        used_offsets.add(offset)

        scheduled_at = cycle_start + timedelta(seconds=offset)
        scheduled_at = scheduled_at.replace(second=0, microsecond=0)

        schedule.append({
            "game_name": game_name,
            "emoji": games.get(game_name, "🎰"),
            "scheduled_at": scheduled_at,
        })

    schedule.sort(key=lambda item: item["scheduled_at"])
    return schedule


def generate_message(user_row, game_name):
    games = parse_json_field(user_row["games_json"], DEFAULT_GAMES)
    headers = parse_json_field(user_row["headers_json"], DEFAULT_HEADERS)
    footers = parse_json_field(user_row["footers_json"], DEFAULT_FOOTERS)
    strategies = parse_json_field(user_row["strategies_json"], DEFAULT_PREMIUM_STRATEGIES)

    header = random.choice(headers) if headers else "🎰 ENTRADA LIBERADA"
    footer = random.choice(footers) if footers else "⚠️ Use gestão."
    strategy = random.choice(strategies) if strategies else "💎 ESTILO PREMIUM"

    brand = user_row["brand_name"] or "Painel Premium"
    emoji = games.get(game_name, "🎰")
    separator = "═" * 24

    return f"""{header}

🏷️ Marca: {brand}
🎮 Jogo: {game_name} {emoji}

{separator}
{strategy}
{separator}

{footer}"""


def already_sent(conn, user_id, cycle_id, game_name, scheduled_at):
    row = conn.execute("""
        SELECT id FROM send_history
        WHERE user_id = ? AND cycle_id = ? AND game_name = ? AND scheduled_at = ?
        LIMIT 1
    """, (user_id, cycle_id, game_name, scheduled_at)).fetchone()
    return row is not None


def send_telegram_message(token, chat_id, text):
    if not token or not chat_id:
        return False, "", "TOKEN ou CHAT_ID ausentes."

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(
            url,
            data={"chat_id": chat_id, "text": text},
            timeout=30
        )
        ok = response.status_code == 200
        return ok, str(response.status_code), response.text[:1000]
    except Exception as exc:
        return False, "EXCEPTION", str(exc)[:1000]


def render_page(page_title, content_template, **context):
    user = get_current_user()
    theme = brand_theme(user)

    base_template = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ page_title }} - {{ theme.brand_name }}</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(180deg, {{ theme.secondary_color }}, #050505);
                color: #ffffff;
                min-height: 100vh;
            }
            a { color: inherit; text-decoration: none; }
            .topbar {
                background: {{ theme.primary_color }};
                border-bottom: 2px solid {{ theme.accent_color }};
                padding: 16px 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 20px;
                flex-wrap: wrap;
            }
            .brand {
                display: flex;
                align-items: center;
                gap: 14px;
            }
            .brand img {
                width: 48px;
                height: 48px;
                object-fit: cover;
                border-radius: 12px;
                border: 2px solid {{ theme.accent_color }};
                background: #fff;
            }
            .brand h1 {
                font-size: 22px;
                color: #fff;
            }
            .brand p {
                font-size: 13px;
                opacity: 0.92;
            }
            .nav {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            .nav a, .nav button {
                background: rgba(0, 0, 0, 0.25);
                border: 1px solid {{ theme.accent_color }};
                color: #fff;
                padding: 10px 14px;
                border-radius: 10px;
                cursor: pointer;
                font-weight: bold;
            }
            .wrapper {
                max-width: 1280px;
                margin: 0 auto;
                padding: 24px;
            }
            .title-box {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-left: 5px solid {{ theme.accent_color }};
                border-radius: 16px;
                padding: 18px;
                margin-bottom: 22px;
            }
            .title-box h2 {
                color: {{ theme.accent_color }};
                font-size: 26px;
                margin-bottom: 6px;
            }
            .title-box p {
                color: #dddddd;
                line-height: 1.5;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
                margin-bottom: 22px;
            }
            .card {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 18px;
                padding: 18px;
                box-shadow: 0 0 14px rgba(0,0,0,0.18);
            }
            .card h3 {
                color: {{ theme.accent_color }};
                margin-bottom: 10px;
                font-size: 18px;
            }
            .stat-num {
                font-size: 30px;
                font-weight: bold;
                color: {{ theme.accent_color }};
            }
            .muted {
                color: #cfcfcf;
                line-height: 1.5;
            }
            .table-wrap { overflow-x: auto; }
            table {
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            }
            th {
                background: {{ theme.accent_color }};
                color: #000;
                text-align: left;
                padding: 12px;
            }
            td {
                padding: 12px;
                border-bottom: 1px solid rgba(255,255,255,0.08);
                vertical-align: top;
            }
            tr:hover { background: rgba(255,255,255,0.04); }
            .success { color: #62d26f; font-weight: bold; }
            .warning { color: #ffd166; font-weight: bold; }
            .danger { color: #ff6b6b; font-weight: bold; }
            .info { color: #7cd4ff; font-weight: bold; }
            .btn {
                display: inline-block;
                background: {{ theme.primary_color }};
                color: #fff;
                border: 1px solid {{ theme.accent_color }};
                padding: 10px 14px;
                border-radius: 10px;
                font-weight: bold;
                cursor: pointer;
            }
            .btn-secondary {
                background: transparent;
            }
            .form-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 16px;
            }
            label {
                display: block;
                margin-bottom: 6px;
                color: #f0f0f0;
                font-weight: bold;
            }
            input, textarea, select {
                width: 100%;
                padding: 12px;
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,0.15);
                background: rgba(0,0,0,0.28);
                color: #fff;
            }
            textarea {
                min-height: 170px;
                resize: vertical;
            }
            .flash {
                margin-bottom: 16px;
                padding: 12px;
                border-radius: 10px;
                background: rgba(255, 209, 102, 0.12);
                border: 1px solid #ffd166;
                color: #ffe8a1;
            }
            .small {
                font-size: 12px;
                color: #cfcfcf;
                margin-top: 6px;
            }
            .badge {
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.12);
                font-size: 12px;
                margin-right: 6px;
            }
            .login-shell {
                max-width: 460px;
                margin: 70px auto;
            }
            .hr {
                height: 1px;
                background: rgba(255,255,255,0.09);
                margin: 16px 0;
            }
            @media (max-width: 980px) {
                .grid, .form-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        {% if session.get('user_id') %}
        <div class="topbar">
            <div class="brand">
                {% if theme.logo_url %}
                    <img src="{{ theme.logo_url }}" alt="Logo">
                {% endif %}
                <div>
                    <h1>{{ theme.brand_name }}</h1>
                    <p>{{ theme.brand_subtitle }}</p>
                </div>
            </div>
            <div class="nav">
                <a href="{{ url_for('dashboard') }}">Dashboard</a>
                <a href="{{ url_for('settings') }}">Configurações</a>
                {% if current_user and current_user['role'] == 'admin' %}
                    <a href="{{ url_for('admin_users') }}">Clientes</a>
                    <a href="{{ url_for('admin_create_user') }}">Novo cliente</a>
                {% endif %}
                <a href="{{ url_for('logout') }}">Sair</a>
            </div>
        </div>
        {% endif %}

        <div class="wrapper">
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="flash">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            """ + content_template + """
        </div>
    </body>
    </html>
    """
    merged_context = {
        "page_title": page_title,
        "theme": theme,
        "current_user": user,
        "session": session,
    }
    merged_context.update(context)
    return render_template_string(base_template, **merged_context)


# =========================================================
# ROTAS DE AUTENTICAÇÃO
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Login inválido.")
            return redirect(url_for("login"))

        if int(user["active"]) != 1:
            flash("Conta inativa.")
            return redirect(url_for("login"))

        expires_at = (user["expires_at"] or "").strip()
        if expires_at:
            try:
                if datetime.fromisoformat(expires_at) < datetime.now():
                    flash("Acesso expirado.")
                    return redirect(url_for("login"))
            except Exception:
                pass

        session["user_id"] = user["id"]
        flash("Login realizado com sucesso.")
        return redirect(url_for("dashboard"))

    content = """
    <div class="login-shell">
        <div class="title-box">
            <h2>Entrar no painel</h2>
            <p>Acesso premium com login e senha.</p>
        </div>
        <div class="card">
            <form method="post">
                <div style="margin-bottom:14px;">
                    <label>Usuário</label>
                    <input type="text" name="username" required>
                </div>
                <div style="margin-bottom:14px;">
                    <label>Senha</label>
                    <input type="password" name="password" required>
                </div>
                <button class="btn" type="submit">Entrar</button>
            </form>
        </div>
    </div>
    """
    return render_page("Login", content)


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Sessão encerrada.")
    return redirect(url_for("login"))


# =========================================================
# DASHBOARD
# =========================================================
@app.route("/")
@login_required
def home():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    now_dt = tz_now(user["timezone"] or DEFAULT_TIMEZONE)
    cycle_id, cycle_start = get_cycle_id(now_dt, user["start_hour"], user["start_minute"])
    schedule = generate_schedule(user, cycle_id, cycle_start)

    conn = get_db()
    sent_rows = conn.execute("""
        SELECT * FROM send_history
        WHERE user_id = ? AND cycle_id = ?
        ORDER BY scheduled_at ASC
    """, (user["id"], cycle_id)).fetchall()

    sent_lookup = {(row["game_name"], row["scheduled_at"]): row for row in sent_rows}

    recent_history = conn.execute("""
        SELECT * FROM send_history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 20
    """, (user["id"],)).fetchall()
    conn.close()

    schedule_view = []
    next_marked = False
    sent_count = 0
    for item in schedule:
        scheduled_str = item["scheduled_at"].strftime("%Y-%m-%d %H:%M")
        sent_row = sent_lookup.get((item["game_name"], scheduled_str))
        sent = sent_row is not None and sent_row["status"] == "sent"
        failed = sent_row is not None and sent_row["status"] == "failed"
        if sent:
            sent_count += 1

        is_next = False
        if not sent and not failed and not next_marked and item["scheduled_at"] >= now_dt:
            is_next = True
            next_marked = True

        schedule_view.append({
            "date": item["scheduled_at"].strftime("%d/%m"),
            "time": item["scheduled_at"].strftime("%H:%M"),
            "game": item["game_name"],
            "emoji": item["emoji"],
            "sent": sent,
            "failed": failed,
            "next": is_next,
        })

    if not next_marked:
        for item in schedule_view:
            if not item["sent"] and not item["failed"]:
                item["next"] = True
                break

    bot_status = "Ligado" if int(user["bot_enabled"]) == 1 else "Desligado"
    account_status = "Ativa" if is_subscription_valid(user) else "Bloqueada"

    content = """
    <div class="title-box">
        <h2>Dashboard</h2>
        <p>
            Controle do seu painel white label. Aqui você acompanha seu ciclo, seus envios
            e sua configuração premium.
        </p>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Status do bot</h3>
            <div class="stat-num">{{ bot_status }}</div>
            <p class="muted">Conta: <span class="{{ 'success' if account_status == 'Ativa' else 'danger' }}">{{ account_status }}</span></p>
        </div>
        <div class="card">
            <h3>Jogos no ciclo</h3>
            <div class="stat-num">{{ total_games }}</div>
            <p class="muted">Escala organizada em 24 horas.</p>
        </div>
        <div class="card">
            <h3>Enviados no ciclo</h3>
            <div class="stat-num">{{ sent_count }}</div>
            <p class="muted">Janela atual: {{ cycle_label }}</p>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Marca</h3>
            <p class="muted"><strong>{{ current_user['brand_name'] }}</strong></p>
            <p class="muted">{{ current_user['brand_subtitle'] }}</p>
        </div>
        <div class="card">
            <h3>Início do ciclo</h3>
            <p class="muted"><strong>{{ "%02d"|format(current_user['start_hour']) }}:{{ "%02d"|format(current_user['start_minute']) }}</strong></p>
            <p class="muted">Fuso: {{ current_user['timezone'] }}</p>
        </div>
        <div class="card">
            <h3>Telegram</h3>
            <p class="muted">Token: {{ 'Configurado' if current_user['telegram_token'] else 'Pendente' }}</p>
            <p class="muted">Chat ID: {{ current_user['telegram_chat_id'] or 'Não informado' }}</p>
        </div>
    </div>

    <div class="card" style="margin-bottom:22px;">
        <h3>Escala do ciclo</h3>
        <div class="table-wrap">
            <table>
                <tr>
                    <th>Data</th>
                    <th>Horário</th>
                    <th>Jogo</th>
                    <th>Status</th>
                </tr>
                {% for item in schedule_view %}
                <tr>
                    <td>{{ item.date }}</td>
                    <td>{{ item.time }}</td>
                    <td>{{ item.emoji }} {{ item.game }}</td>
                    <td>
                        {% if item.sent %}
                            <span class="success">✅ Enviado</span>
                        {% elif item.failed %}
                            <span class="danger">❌ Falhou</span>
                        {% elif item.next %}
                            <span class="info">👉 Próximo</span>
                        {% else %}
                            <span class="warning">⏳ Pendente</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>

    <div class="card">
        <h3>Histórico recente</h3>
        <div class="table-wrap">
            <table>
                <tr>
                    <th>Horário programado</th>
                    <th>Jogo</th>
                    <th>Status</th>
                    <th>Enviado em</th>
                </tr>
                {% for row in recent_history %}
                <tr>
                    <td>{{ row['scheduled_at'] }}</td>
                    <td>{{ row['game_name'] }}</td>
                    <td>
                        {% if row['status'] == 'sent' %}
                            <span class="success">✅ Enviado</span>
                        {% elif row['status'] == 'failed' %}
                            <span class="danger">❌ Falhou</span>
                        {% else %}
                            <span class="warning">{{ row['status'] }}</span>
                        {% endif %}
                    </td>
                    <td>{{ row['sent_at'] or '-' }}</td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="4">Nenhum envio registrado ainda.</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
    """
    return render_page(
        "Dashboard",
        content,
        bot_status=bot_status,
        account_status=account_status,
        total_games=len(parse_json_field(user["games_json"], DEFAULT_GAMES)),
        sent_count=sent_count,
        cycle_label=get_cycle_label(cycle_start),
        schedule_view=schedule_view,
        recent_history=recent_history,
    )


# =========================================================
# CONFIGURAÇÕES DO CLIENTE
# =========================================================
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = get_current_user()

    if request.method == "POST":
        brand_name = request.form.get("brand_name", "").strip() or "Painel Premium"
        brand_subtitle = request.form.get("brand_subtitle", "").strip() or "Sistema premium"
        primary_color = request.form.get("primary_color", "").strip() or "#8b0000"
        secondary_color = request.form.get("secondary_color", "").strip() or "#111111"
        accent_color = request.form.get("accent_color", "").strip() or "#d4af37"
        logo_url = request.form.get("logo_url", "").strip()

        telegram_token = request.form.get("telegram_token", "").strip()
        telegram_chat_id = request.form.get("telegram_chat_id", "").strip()
        start_hour = int(request.form.get("start_hour", 14) or 14)
        start_minute = int(request.form.get("start_minute", 40) or 40)
        timezone = request.form.get("timezone", DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE
        bot_enabled = 1 if request.form.get("bot_enabled") == "on" else 0

        headers = serialize_blocks(request.form.get("headers_text", "").strip()) or DEFAULT_HEADERS
        footers = serialize_blocks(request.form.get("footers_text", "").strip()) or DEFAULT_FOOTERS
        strategies = serialize_blocks(request.form.get("strategies_text", "").strip()) or DEFAULT_PREMIUM_STRATEGIES

        games_lines = [line.strip() for line in request.form.get("games_text", "").splitlines() if line.strip()]
        games_map = {}
        for line in games_lines:
            if "|" in line:
                game_name, emoji = line.split("|", 1)
                games_map[game_name.strip()] = emoji.strip() or "🎰"
            else:
                games_map[line] = "🎰"
        if not games_map:
            games_map = DEFAULT_GAMES

        conn = get_db()
        conn.execute("""
            UPDATE users
            SET brand_name = ?, brand_subtitle = ?, primary_color = ?, secondary_color = ?, accent_color = ?, logo_url = ?
            WHERE id = ?
        """, (brand_name, brand_subtitle, primary_color, secondary_color, accent_color, logo_url, user["id"]))

        conn.execute("""
            UPDATE bot_settings
            SET telegram_token = ?, telegram_chat_id = ?, start_hour = ?, start_minute = ?,
                timezone = ?, bot_enabled = ?, headers_json = ?, footers_json = ?,
                strategies_json = ?, games_json = ?
            WHERE user_id = ?
        """, (
            telegram_token,
            telegram_chat_id,
            start_hour,
            start_minute,
            timezone,
            bot_enabled,
            json.dumps(headers, ensure_ascii=False),
            json.dumps(footers, ensure_ascii=False),
            json.dumps(strategies, ensure_ascii=False),
            json.dumps(games_map, ensure_ascii=False),
            user["id"],
        ))
        conn.commit()
        conn.close()

        flash("Configurações atualizadas com sucesso.")
        return redirect(url_for("settings"))

    headers_text = blocks_to_text(parse_json_field(user["headers_json"], DEFAULT_HEADERS))
    footers_text = blocks_to_text(parse_json_field(user["footers_json"], DEFAULT_FOOTERS))
    strategies_text = blocks_to_text(parse_json_field(user["strategies_json"], DEFAULT_PREMIUM_STRATEGIES))
    games_map = parse_json_field(user["games_json"], DEFAULT_GAMES)
    games_text = "\n".join([f"{name} | {emoji}" for name, emoji in games_map.items()])

    content = """
    <div class="title-box">
        <h2>Configurações premium</h2>
        <p>
            Aqui você personaliza sua marca própria, seu bot, seus jogos e suas mensagens.
            Para separar um bloco do outro, use exatamente: <strong>{{ separator }}</strong>
        </p>
    </div>

    <form method="post">
        <div class="card" style="margin-bottom:22px;">
            <h3>White label / marca própria</h3>
            <div class="form-grid">
                <div>
                    <label>Nome da marca</label>
                    <input type="text" name="brand_name" value="{{ current_user['brand_name'] }}">
                </div>
                <div>
                    <label>Subtítulo da marca</label>
                    <input type="text" name="brand_subtitle" value="{{ current_user['brand_subtitle'] }}">
                </div>
                <div>
                    <label>Cor principal</label>
                    <input type="text" name="primary_color" value="{{ current_user['primary_color'] }}">
                </div>
                <div>
                    <label>Cor secundária</label>
                    <input type="text" name="secondary_color" value="{{ current_user['secondary_color'] }}">
                </div>
                <div>
                    <label>Cor destaque</label>
                    <input type="text" name="accent_color" value="{{ current_user['accent_color'] }}">
                </div>
                <div>
                    <label>URL da logo</label>
                    <input type="text" name="logo_url" value="{{ current_user['logo_url'] }}">
                </div>
            </div>
        </div>

        <div class="card" style="margin-bottom:22px;">
            <h3>Bot e Telegram</h3>
            <div class="form-grid">
                <div>
                    <label>Token do Telegram</label>
                    <input type="text" name="telegram_token" value="{{ current_user['telegram_token'] or '' }}">
                </div>
                <div>
                    <label>Chat ID</label>
                    <input type="text" name="telegram_chat_id" value="{{ current_user['telegram_chat_id'] or '' }}">
                </div>
                <div>
                    <label>Hora de início do ciclo</label>
                    <input type="number" min="0" max="23" name="start_hour" value="{{ current_user['start_hour'] }}">
                </div>
                <div>
                    <label>Minuto de início do ciclo</label>
                    <input type="number" min="0" max="59" name="start_minute" value="{{ current_user['start_minute'] }}">
                </div>
                <div>
                    <label>Fuso</label>
                    <input type="text" name="timezone" value="{{ current_user['timezone'] }}">
                </div>
                <div>
                    <label style="margin-bottom:12px;">Status</label>
                    <input type="checkbox" name="bot_enabled" {% if current_user['bot_enabled'] == 1 %}checked{% endif %}>
                    <span class="small">Marque para deixar o bot ligado.</span>
                </div>
            </div>
        </div>

        <div class="card" style="margin-bottom:22px;">
            <h3>Cabeçalhos</h3>
            <textarea name="headers_text">{{ headers_text }}</textarea>
            <div class="small">Separe um cabeçalho do outro com {{ separator }}</div>
        </div>

        <div class="card" style="margin-bottom:22px;">
            <h3>Rodapés</h3>
            <textarea name="footers_text">{{ footers_text }}</textarea>
            <div class="small">Separe um rodapé do outro com {{ separator }}</div>
        </div>

        <div class="card" style="margin-bottom:22px;">
            <h3>Estratégias — Estilo premium</h3>
            <textarea name="strategies_text">{{ strategies_text }}</textarea>
            <div class="small">Estratégias claras, passo a passo, com leve, média e agressiva.</div>
        </div>

        <div class="card" style="margin-bottom:22px;">
            <h3>Jogos ativos</h3>
            <textarea name="games_text">{{ games_text }}</textarea>
            <div class="small">Use um jogo por linha no formato: Nome do jogo | emoji</div>
        </div>

        <button class="btn" type="submit">Salvar tudo</button>
    </form>
    """
    return render_page(
        "Configurações",
        content,
        separator=SEPARATOR,
        headers_text=headers_text,
        footers_text=footers_text,
        strategies_text=strategies_text,
        games_text=games_text,
    )


# =========================================================
# ADMIN - CLIENTES
# =========================================================
@app.route("/admin/users")
@admin_required
def admin_users():
    conn = get_db()
    users = conn.execute("""
        SELECT
            u.*,
            b.bot_enabled,
            b.start_hour,
            b.start_minute
        FROM users u
        LEFT JOIN bot_settings b ON b.user_id = u.id
        ORDER BY u.id DESC
    """).fetchall()
    conn.close()

    content = """
    <div class="title-box">
        <h2>Clientes</h2>
        <p>Gerencie contas, acesso, vencimento e status dos bots.</p>
    </div>

    <div class="card">
        <h3>Lista de contas</h3>
        <div class="table-wrap">
            <table>
                <tr>
                    <th>ID</th>
                    <th>Usuário</th>
                    <th>Tipo</th>
                    <th>Marca</th>
                    <th>Status</th>
                    <th>Bot</th>
                    <th>Início</th>
                    <th>Vencimento</th>
                    <th>Ações</th>
                </tr>
                {% for row in users %}
                <tr>
                    <td>{{ row['id'] }}</td>
                    <td>{{ row['username'] }}</td>
                    <td>{{ row['role'] }}</td>
                    <td>{{ row['brand_name'] }}</td>
                    <td>
                        {% if row['active'] == 1 %}
                            <span class="success">Ativa</span>
                        {% else %}
                            <span class="danger">Inativa</span>
                        {% endif %}
                    </td>
                    <td>
                        {% if row['bot_enabled'] == 1 %}
                            <span class="success">Ligado</span>
                        {% else %}
                            <span class="warning">Desligado</span>
                        {% endif %}
                    </td>
                    <td>{{ "%02d"|format(row['start_hour'] or 0) }}:{{ "%02d"|format(row['start_minute'] or 0) }}</td>
                    <td>{{ row['expires_at'] or '-' }}</td>
                    <td>
                        <a class="btn btn-secondary" href="{{ url_for('admin_edit_user', user_id=row['id']) }}">Editar</a>
                        {% if row['id'] != current_user['id'] %}
                            <a class="btn btn-secondary" href="{{ url_for('admin_toggle_user', user_id=row['id']) }}">Ativar/Desativar</a>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
    """
    return render_page("Clientes", content, users=users)


@app.route("/admin/users/create", methods=["GET", "POST"])
@admin_required
def admin_create_user():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "client").strip()
        brand_name = request.form.get("brand_name", "").strip() or username or "Painel Premium"
        brand_subtitle = request.form.get("brand_subtitle", "").strip() or "Sistema premium"
        expires_at = request.form.get("expires_at", "").strip()

        if not username or not password:
            flash("Usuário e senha são obrigatórios.")
            return redirect(url_for("admin_create_user"))

        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (
                    username, password_hash, role, active, brand_name, brand_subtitle,
                    primary_color, secondary_color, accent_color, logo_url, expires_at, created_at
                ) VALUES (?, ?, ?, 1, ?, ?, '#8b0000', '#111111', '#d4af37', '', ?, ?)
            """, (
                username,
                generate_password_hash(password),
                role,
                brand_name,
                brand_subtitle,
                expires_at,
                datetime.now().isoformat(),
            ))
            user_id = cur.lastrowid
            create_default_bot_settings(conn, user_id)
            conn.commit()
            flash("Conta criada com sucesso.")
            return redirect(url_for("admin_users"))
        except sqlite3.IntegrityError:
            flash("Esse usuário já existe.")
        finally:
            conn.close()

    content = """
    <div class="title-box">
        <h2>Novo cliente</h2>
        <p>Crie uma nova conta premium com painel próprio.</p>
    </div>

    <div class="card">
        <form method="post">
            <div class="form-grid">
                <div>
                    <label>Usuário</label>
                    <input type="text" name="username" required>
                </div>
                <div>
                    <label>Senha</label>
                    <input type="password" name="password" required>
                </div>
                <div>
                    <label>Tipo</label>
                    <select name="role">
                        <option value="client">Cliente</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
                <div>
                    <label>Marca</label>
                    <input type="text" name="brand_name">
                </div>
                <div>
                    <label>Subtítulo</label>
                    <input type="text" name="brand_subtitle">
                </div>
                <div>
                    <label>Vencimento (opcional)</label>
                    <input type="text" name="expires_at" placeholder="2026-12-31T23:59:00">
                </div>
            </div>
            <br>
            <button class="btn" type="submit">Criar conta</button>
        </form>
    </div>
    """
    return render_page("Novo cliente", content)


@app.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_user(user_id):
    target = get_user_with_settings(user_id)
    if not target:
        flash("Usuária não encontrada.")
        return redirect(url_for("admin_users"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "client").strip()
        active = 1 if request.form.get("active") == "on" else 0
        expires_at = request.form.get("expires_at", "").strip()
        brand_name = request.form.get("brand_name", "").strip() or "Painel Premium"
        brand_subtitle = request.form.get("brand_subtitle", "").strip() or "Sistema premium"
        primary_color = request.form.get("primary_color", "").strip() or "#8b0000"
        secondary_color = request.form.get("secondary_color", "").strip() or "#111111"
        accent_color = request.form.get("accent_color", "").strip() or "#d4af37"
        logo_url = request.form.get("logo_url", "").strip()

        telegram_token = request.form.get("telegram_token", "").strip()
        telegram_chat_id = request.form.get("telegram_chat_id", "").strip()
        start_hour = int(request.form.get("start_hour", 14) or 14)
        start_minute = int(request.form.get("start_minute", 40) or 40)
        timezone = request.form.get("timezone", DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE
        bot_enabled = 1 if request.form.get("bot_enabled") == "on" else 0

        headers = serialize_blocks(request.form.get("headers_text", "").strip()) or DEFAULT_HEADERS
        footers = serialize_blocks(request.form.get("footers_text", "").strip()) or DEFAULT_FOOTERS
        strategies = serialize_blocks(request.form.get("strategies_text", "").strip()) or DEFAULT_PREMIUM_STRATEGIES

        games_lines = [line.strip() for line in request.form.get("games_text", "").splitlines() if line.strip()]
        games_map = {}
        for line in games_lines:
            if "|" in line:
                game_name, emoji = line.split("|", 1)
                games_map[game_name.strip()] = emoji.strip() or "🎰"
            else:
                games_map[line] = "🎰"
        if not games_map:
            games_map = DEFAULT_GAMES

        conn = get_db()
        try:
            if password:
                conn.execute("""
                    UPDATE users
                    SET username = ?, password_hash = ?, role = ?, active = ?, brand_name = ?, brand_subtitle = ?,
                        primary_color = ?, secondary_color = ?, accent_color = ?, logo_url = ?, expires_at = ?
                    WHERE id = ?
                """, (
                    username,
                    generate_password_hash(password),
                    role,
                    active,
                    brand_name,
                    brand_subtitle,
                    primary_color,
                    secondary_color,
                    accent_color,
                    logo_url,
                    expires_at,
                    user_id,
                ))
            else:
                conn.execute("""
                    UPDATE users
                    SET username = ?, role = ?, active = ?, brand_name = ?, brand_subtitle = ?,
                        primary_color = ?, secondary_color = ?, accent_color = ?, logo_url = ?, expires_at = ?
                    WHERE id = ?
                """, (
                    username,
                    role,
                    active,
                    brand_name,
                    brand_subtitle,
                    primary_color,
                    secondary_color,
                    accent_color,
                    logo_url,
                    expires_at,
                    user_id,
                ))

            conn.execute("""
                UPDATE bot_settings
                SET telegram_token = ?, telegram_chat_id = ?, start_hour = ?, start_minute = ?,
                    timezone = ?, bot_enabled = ?, headers_json = ?, footers_json = ?,
                    strategies_json = ?, games_json = ?
                WHERE user_id = ?
            """, (
                telegram_token,
                telegram_chat_id,
                start_hour,
                start_minute,
                timezone,
                bot_enabled,
                json.dumps(headers, ensure_ascii=False),
                json.dumps(footers, ensure_ascii=False),
                json.dumps(strategies, ensure_ascii=False),
                json.dumps(games_map, ensure_ascii=False),
                user_id,
            ))
            conn.commit()
            flash("Conta atualizada com sucesso.")
            return redirect(url_for("admin_users"))
        except sqlite3.IntegrityError:
            flash("Esse usuário já existe.")
        finally:
            conn.close()

    headers_text = blocks_to_text(parse_json_field(target["headers_json"], DEFAULT_HEADERS))
    footers_text = blocks_to_text(parse_json_field(target["footers_json"], DEFAULT_FOOTERS))
    strategies_text = blocks_to_text(parse_json_field(target["strategies_json"], DEFAULT_PREMIUM_STRATEGIES))
    games_map = parse_json_field(target["games_json"], DEFAULT_GAMES)
    games_text = "\n".join([f"{name} | {emoji}" for name, emoji in games_map.items()])

    content = """
    <div class="title-box">
        <h2>Editar conta #{{ target['id'] }}</h2>
        <p>Você pode alterar acesso, marca, Telegram, jogos e estratégias dessa conta.</p>
    </div>

    <form method="post">
        <div class="card" style="margin-bottom:22px;">
            <h3>Dados da conta</h3>
            <div class="form-grid">
                <div>
                    <label>Usuário</label>
                    <input type="text" name="username" value="{{ target['username'] }}" required>
                </div>
                <div>
                    <label>Nova senha (opcional)</label>
                    <input type="password" name="password">
                </div>
                <div>
                    <label>Tipo</label>
                    <select name="role">
                        <option value="client" {% if target['role'] == 'client' %}selected{% endif %}>Cliente</option>
                        <option value="admin" {% if target['role'] == 'admin' %}selected{% endif %}>Admin</option>
                    </select>
                </div>
                <div>
                    <label>Vencimento</label>
                    <input type="text" name="expires_at" value="{{ target['expires_at'] or '' }}">
                </div>
                <div>
                    <label style="margin-bottom:12px;">Conta ativa</label>
                    <input type="checkbox" name="active" {% if target['active'] == 1 %}checked{% endif %}>
                </div>
            </div>
        </div>

        <div class="card" style="margin-bottom:22px;">
            <h3>Marca própria</h3>
            <div class="form-grid">
                <div>
                    <label>Nome da marca</label>
                    <input type="text" name="brand_name" value="{{ target['brand_name'] }}">
                </div>
                <div>
                    <label>Subtítulo</label>
                    <input type="text" name="brand_subtitle" value="{{ target['brand_subtitle'] }}">
                </div>
                <div>
                    <label>Cor principal</label>
                    <input type="text" name="primary_color" value="{{ target['primary_color'] }}">
                </div>
                <div>
                    <label>Cor secundária</label>
                    <input type="text" name="secondary_color" value="{{ target['secondary_color'] }}">
                </div>
                <div>
                    <label>Cor destaque</label>
                    <input type="text" name="accent_color" value="{{ target['accent_color'] }}">
                </div>
                <div>
                    <label>URL da logo</label>
                    <input type="text" name="logo_url" value="{{ target['logo_url'] or '' }}">
                </div>
            </div>
        </div>

        <div class="card" style="margin-bottom:22px;">
            <h3>Telegram e bot</h3>
            <div class="form-grid">
                <div>
                    <label>Token</label>
                    <input type="text" name="telegram_token" value="{{ target['telegram_token'] or '' }}">
                </div>
                <div>
                    <label>Chat ID</label>
                    <input type="text" name="telegram_chat_id" value="{{ target['telegram_chat_id'] or '' }}">
                </div>
                <div>
                    <label>Hora inicial</label>
                    <input type="number" min="0" max="23" name="start_hour" value="{{ target['start_hour'] }}">
                </div>
                <div>
                    <label>Minuto inicial</label>
                    <input type="number" min="0" max="59" name="start_minute" value="{{ target['start_minute'] }}">
                </div>
                <div>
                    <label>Fuso</label>
                    <input type="text" name="timezone" value="{{ target['timezone'] }}">
                </div>
                <div>
                    <label style="margin-bottom:12px;">Bot ligado</label>
                    <input type="checkbox" name="bot_enabled" {% if target['bot_enabled'] == 1 %}checked{% endif %}>
                </div>
            </div>
        </div>

        <div class="card" style="margin-bottom:22px;">
            <h3>Cabeçalhos</h3>
            <textarea name="headers_text">{{ headers_text }}</textarea>
        </div>

        <div class="card" style="margin-bottom:22px;">
            <h3>Rodapés</h3>
            <textarea name="footers_text">{{ footers_text }}</textarea>
        </div>

        <div class="card" style="margin-bottom:22px;">
            <h3>Estratégias premium</h3>
            <textarea name="strategies_text">{{ strategies_text }}</textarea>
        </div>

        <div class="card" style="margin-bottom:22px;">
            <h3>Jogos</h3>
            <textarea name="games_text">{{ games_text }}</textarea>
        </div>

        <button class="btn" type="submit">Salvar alterações</button>
    </form>
    """
    return render_page(
        "Editar conta",
        content,
        target=target,
        headers_text=headers_text,
        footers_text=footers_text,
        strategies_text=strategies_text,
        games_text=games_text,
    )


@app.route("/admin/users/<int:user_id>/toggle")
@admin_required
def admin_toggle_user(user_id):
    current = get_current_user()
    if user_id == current["id"]:
        flash("Você não pode desativar sua própria conta aqui.")
        return redirect(url_for("admin_users"))

    conn = get_db()
    row = conn.execute("SELECT active FROM users WHERE id = ?", (user_id,)).fetchone()
    if row:
        new_value = 0 if int(row["active"]) == 1 else 1
        conn.execute("UPDATE users SET active = ? WHERE id = ?", (new_value, user_id))
        conn.commit()
        flash("Status da conta alterado.")
    conn.close()
    return redirect(url_for("admin_users"))


# =========================================================
# MOTOR DE ENVIO MULTIUSUÁRIO
# =========================================================
def worker_loop():
    while True:
        try:
            conn = get_db()
            active_users = conn.execute("""
                SELECT
                    u.*,
                    b.telegram_token,
                    b.telegram_chat_id,
                    b.start_hour,
                    b.start_minute,
                    b.timezone,
                    b.bot_enabled,
                    b.headers_json,
                    b.footers_json,
                    b.strategies_json,
                    b.games_json
                FROM users u
                JOIN bot_settings b ON b.user_id = u.id
                WHERE u.active = 1
                  AND b.bot_enabled = 1
            """).fetchall()

            for user in active_users:
                if user["role"] == "admin":
                    continue

                if not is_subscription_valid(user):
                    continue

                now_dt = tz_now(user["timezone"] or DEFAULT_TIMEZONE)
                current_minute = now_dt.strftime("%Y-%m-%d %H:%M")
                cycle_id, cycle_start = get_cycle_id(now_dt, user["start_hour"], user["start_minute"])
                schedule = generate_schedule(user, cycle_id, cycle_start)

                for item in schedule:
                    scheduled_str = item["scheduled_at"].strftime("%Y-%m-%d %H:%M")
                    if scheduled_str != current_minute:
                        continue

                    if already_sent(conn, user["id"], cycle_id, item["game_name"], scheduled_str):
                        continue

                    text = generate_message(user, item["game_name"])
                    ok, code, response_text = send_telegram_message(
                        user["telegram_token"],
                        user["telegram_chat_id"],
                        text
                    )

                    conn.execute("""
                        INSERT OR IGNORE INTO send_history (
                            user_id, cycle_id, scheduled_at, sent_at, game_name,
                            message_text, status, response_code, response_text
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user["id"],
                        cycle_id,
                        scheduled_str,
                        datetime.now().isoformat() if ok else "",
                        item["game_name"],
                        text,
                        "sent" if ok else "failed",
                        code,
                        response_text,
                    ))
                    conn.commit()

            conn.close()
            time.sleep(15)

        except Exception as exc:
            print(f"Erro no worker: {exc}")
            time.sleep(15)


# =========================================================
# INICIALIZAÇÃO
# =========================================================
init_db()

worker = threading.Thread(target=worker_loop, daemon=True)
worker.start()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
'''

requirements = """Flask==3.1.0
requests==2.32.3
Werkzeug==3.1.3
"""

Path("/mnt/data/app_plano_vendas_estilo_premium.py").write_text(app_code, encoding="utf-8")
Path("/mnt/data/requirements_plano_vendas.txt").write_text(requirements, encoding="utf-8")
print("Arquivos criados com sucesso.")
