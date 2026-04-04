from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import sqlite3
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import requests
import secrets
from functools import wraps

# =========================================================
# CONFIG
# =========================================================
APP_TZ = ZoneInfo("America/Sao_Paulo")
DB_PATH = os.getenv("DB_PATH", "/tmp/rainha_games.db")

TOKEN = os.getenv("TOKEN", "").strip()
CHAT_ID = os.getenv("CHAT_ID", "").strip()

DEFAULT_ADMIN_USER = os.getenv("ADMIN_USER", "admin").strip()
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123456").strip()
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

app = Flask(__name__)
app.secret_key = SECRET_KEY

# =========================================================
# CATÁLOGO INICIAL
# Você pode adicionar mais pelo painel admin sem mexer no código.
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
    ("Cleopatra", "PG Soft", "96.24%", "🏺"),
    ("Rise of Apollo", "PG Soft", "96.20%", "⚡"),
    ("Totem Wonders", "PG Soft", "96.71%", "🗿"),
    ("Opera Dynasty", "PG Soft", "96.52%", "🎭"),
    ("Muay Thai Champion", "PG Soft", "96.86%", "🥊"),
    ("Ninja vs Samurai", "PG Soft", "97.44%", "⚔️"),
    ("Legend of Perseus", "PG Soft", "96.31%", "🛡️"),
    ("Legend of Hou Yi", "PG Soft", "96.95%", "🏹"),

    # PRAGMATIC PLAY
    ("Gates of Olympus", "Pragmatic Play", "96.50%", "⚡"),
    ("Gates of Olympus 1000", "Pragmatic Play", "96.50%", "⚡"),
    ("Sweet Bonanza", "Pragmatic Play", "96.51%", "🍭"),
    ("Sweet Bonanza Xmas", "Pragmatic Play", "96.48%", "🎄"),
    ("Sweet Bonanza 1000", "Pragmatic Play", "96.50%", "🍭"),
    ("Starlight Princess", "Pragmatic Play", "96.50%", "⭐"),
    ("Starlight Princess 1000", "Pragmatic Play", "96.50%", "⭐"),
    ("Starlight Christmas", "Pragmatic Play", "96.50%", "🎄"),
    ("Big Bass Bonanza", "Pragmatic Play", "96.71%", "🎣"),
    ("Big Bass Splash", "Pragmatic Play", "96.71%", "🎣"),
    ("Big Bass Bonanza Megaways", "Pragmatic Play", "96.70%", "🎣"),
    ("Big Bass Halloween", "Pragmatic Play", "96.50%", "🎃"),
    ("Big Bass Christmas Bash", "Pragmatic Play", "96.50%", "🎄"),
    ("Big Bass Day at the Races", "Pragmatic Play", "96.53%", "🏇"),
    ("Big Bass Amazon Xtreme", "Pragmatic Play", "96.50%", "🌿"),
    ("The Dog House", "Pragmatic Play", "96.51%", "🐶"),
    ("The Dog House Megaways", "Pragmatic Play", "96.55%", "🐶"),
    ("The Dog House Multihold", "Pragmatic Play", "96.50%", "🐶"),
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
    ("Great Rhino Deluxe", "Pragmatic Play", "96.50%", "🦏"),
    ("Extra Juicy", "Pragmatic Play", "96.50%", "🍉"),
    ("Extra Juicy Megaways", "Pragmatic Play", "96.52%", "🍉"),
    ("Juicy Fruits", "Pragmatic Play", "96.50%", "🍓"),
    ("Juicy Fruits Multihold", "Pragmatic Play", "96.50%", "🍓"),
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
    ("John Hunter and the Tomb of the Scarab Queen", "Pragmatic Play", "96.50%", "🏺"),
    ("John Hunter and the Aztec Treasure", "Pragmatic Play", "96.50%", "🏺"),
    ("Wild West Gold", "Pragmatic Play", "96.51%", "🤠"),
    ("Wild West Gold Megaways", "Pragmatic Play", "96.54%", "🤠"),
    ("Pirate Gold", "Pragmatic Play", "96.50%", "🏴‍☠️"),
    ("Queen of Gold", "Pragmatic Play", "96.50%", "👑"),
    ("Emerald King", "Pragmatic Play", "96.50%", "💎"),
    ("Rise of Samurai", "Pragmatic Play", "96.50%", "🗾"),
    ("Greek Gods", "Pragmatic Play", "96.50%", "🏛️"),
    ("Hercules and Pegasus", "Pragmatic Play", "96.50%", "🐎"),
    ("Candy Stars", "Pragmatic Play", "96.50%", "🍬"),
    ("Diamond Strike", "Pragmatic Play", "96.50%", "💎"),
    ("Book of Kingdoms", "Pragmatic Play", "96.50%", "📖"),
    ("Book of Tut", "Pragmatic Play", "96.50%", "📖"),
    ("Book of Aztec", "Pragmatic Play", "96.50%", "📖"),
    ("Queen of Atlantis", "Pragmatic Play", "96.50%", "🌊"),
    ("Vikings Unleashed", "Pragmatic Play", "96.50%", "🛡️"),
    ("Cyber Heist", "Pragmatic Play", "96.50%", "🤖"),
    ("Spaceman", "Pragmatic Play", "96.50%", "🚀"),
    ("Alien Nights", "Pragmatic Play", "96.50%", "👽"),
    ("Neon Dreams", "Pragmatic Play", "96.50%", "🌆"),
    ("Robo Cash", "Pragmatic Play", "96.50%", "🤖"),
    ("Quantum Rush", "Pragmatic Play", "96.50%", "⚛️"),
    ("Rise of Giza", "Pragmatic Play", "96.50%", "🏺"),
    ("Eye of Anubis", "Pragmatic Play", "96.50%", "🐺"),
    ("Pharaoh's Fortune", "Pragmatic Play", "96.50%", "👑"),
    ("Zeus Unleashed", "Pragmatic Play", "96.50%", "⚡"),
    ("Hades Inferno", "Pragmatic Play", "96.50%", "🔥"),

    # SPIRIT GAMING
    ("Gems Fortune", "Spirit Gaming", "96.50%", "💎"),
    ("Gems Fortune 2", "Spirit Gaming", "96.30%", "💎"),
    ("God of Wealth", "Spirit Gaming", "96.00%", "🙏"),
    ("Ice Princess", "Spirit Gaming", "96.20%", "❄️"),
    ("Joker Spin", "Spirit Gaming", "95.80%", "🃏"),
    ("Merry Christmas", "Spirit Gaming", "96.40%", "🎅"),
    ("Mouse Fortune", "Spirit Gaming", "96.10%", "🐭"),
    ("Ox Fortune", "Spirit Gaming", "96.30%", "🐂"),
    ("Rabbit Fortune", "Spirit Gaming", "96.50%", "🐰"),
    ("Tiger Fortune", "Spirit Gaming", "96.70%", "🐯"),
    ("Wild Buffalo", "Spirit Gaming", "96.20%", "🦬"),
    ("Wild Lion", "Spirit Gaming", "96.40%", "🦁"),

    # FAT PANDA
    ("Lucky Tiger", "Fat Panda", "96.50%", "🐯"),
    ("Lucky Tiger 1000", "Fat Panda", "96.50%", "🐯"),
    ("Lucky Mouse", "Fat Panda", "96.57%", "🐭"),
    ("Lucky Phoenix", "Fat Panda", "96.50%", "🦅"),
    ("Lucky Dog", "Fat Panda", "96.50%", "🐕"),
    ("Lucky Ox", "Fat Panda", "96.50%", "🐂"),
    ("Lucky Monkey", "Fat Panda", "96.50%", "🐒"),
    ("Lucky Dice", "Fat Panda", "96.50%", "🎲"),
    ("Lucky Fortune Tree", "Fat Panda", "96.50%", "🌳"),
    ("Starlight Wins", "Fat Panda", "96.50%", "⭐"),
    ("Pig Farm", "Fat Panda", "96.50%", "🐷"),
    ("Emotiwins", "Fat Panda", "96.50%", "😄"),
    ("Jelly Candy", "Fat Panda", "96.52%", "🍬"),
    ("Plushie Wins", "Fat Panda", "96.50%", "🧸"),
    ("Wealthy Frog", "Fat Panda", "96.50%", "🐸"),
    ("Fortunes of Aztec", "Fat Panda", "96.50%", "🏺"),
    ("Olympus Wins", "Fat Panda", "96.50%", "⚡"),
    ("Master Gems", "Fat Panda", "96.50%", "💎"),
    ("777 Rush", "Fat Panda", "96.50%", "7️⃣"),
    ("Code of Cairo", "Fat Panda", "96.50%", "📜"),
    ("Dino Drop", "Fat Panda", "96.50%", "🦕"),
    ("Mystic Wishes", "Fat Panda", "96.50%", "🔮"),
    ("Happy Nets", "Fat Panda", "96.50%", "🎣"),
    ("DJ Neko", "Fat Panda", "96.50%", "🐱"),
    ("Sweet Burst", "Fat Panda", "96.50%", "🍭"),

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
    ("Chaos Crew 3", "Hacksaw", "96.30%", "🔥"),
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
    ("Keep Em", "Hacksaw", "96.27%", "🥫"),
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

    # RECTANGLE
    ("Prosperity Dragon", "Rectangle", "96.00%", "🐉"),
    ("Prosperity Horse", "Rectangle", "96.00%", "🐎"),
    ("Prosperity Mouse", "Rectangle", "96.00%", "🐭"),
    ("Prosperity Ox", "Rectangle", "96.00%", "🐂"),
    ("Prosperity Rabbit", "Rectangle", "96.00%", "🐰"),
    ("Prosperity Tiger", "Rectangle", "96.00%", "🐯"),
    ("Prosperity Clash", "Rectangle", "96.00%", "⚔️"),
    ("Lucky Duck", "Rectangle", "96.00%", "🦆"),
    ("Lucky Fox", "Rectangle", "96.00%", "🦊"),
    ("Lucky Panda", "Rectangle", "96.00%", "🐼"),
    ("Lucky Snake", "Rectangle", "96.00%", "🐍"),
    ("Lucky Turtle", "Rectangle", "96.00%", "🐢"),
    ("Fiesta Green", "Rectangle", "96.00%", "💚"),
    ("Fiesta Magenta", "Rectangle", "96.00%", "💜"),
    ("Fiesta Red", "Rectangle", "96.00%", "❤️"),
    ("Fiesta Blue", "Rectangle", "96.00%", "💙"),
    ("Money Mania", "Rectangle", "96.00%", "💸"),
    ("Piggy Mines", "Rectangle", "96.00%", "🐷"),
    ("Fortune Pig", "Rectangle", "96.00%", "🐷"),
    ("Gold Diggers", "Rectangle", "96.00%", "💰"),
    ("Golden Koi Trail", "Rectangle", "96.00%", "🐟"),
    ("Solar Pong", "Rectangle", "96.00%", "🌞"),
    ("Tinkering Box", "Rectangle", "96.00%", "📦"),
    ("Shapes of Fortune", "Rectangle", "96.00%", "🔺"),
    ("Shapes of Fortune Xmas", "Rectangle", "96.00%", "🎄"),
    ("Smash Fury", "Rectangle", "96.00%", "💥"),
    ("Treasures of Hades", "Rectangle", "96.00%", "🔥"),
    ("Realm of Thunder", "Rectangle", "96.00%", "⚡"),
    ("Iron Valor", "Rectangle", "96.00%", "🤖"),
    ("Dragon Crash", "Rectangle", "96.00%", "🐉"),
    ("Aztec's Mystery", "Rectangle", "96.00%", "🏺"),
    ("Swaggy Caramelo", "Rectangle", "96.00%", "🐶"),
    ("Swaggy Prize", "Rectangle", "96.00%", "🎁"),
    ("Lucky Caramelo", "Rectangle", "96.00%", "🐶"),
    ("Lucky Caramelo 1000", "Rectangle", "96.00%", "🚀"),
    ("The Lone Fireball", "Rectangle", "96.00%", "🔥"),
    ("The Lucky Year", "Rectangle", "96.00%", "🧧"),
    ("Wheel of Wealth", "Rectangle", "96.00%", "🎡"),
    ("Topfly Pirates Treasure", "Rectangle", "96.00%", "🏴‍☠️"),
    ("Pirate's Treasure Reel", "Rectangle", "96.00%", "🏴‍☠️"),
    ("Pisces Realm of Fortune", "Rectangle", "96.00%", "♓"),
    ("Semana Santa Treasures", "Rectangle", "96.00%", "✝️"),
    ("Rudolph's Gifts", "Rectangle", "96.00%", "🎅"),
    ("Firecrackers Fortune", "Rectangle", "96.00%", "🎆"),
    ("Firecrackers Fortune 100", "Rectangle", "96.00%", "💯"),
    ("Aquarius Fortune Wheel", "Rectangle", "96.00%", "♒"),
    ("Battle Ship", "Rectangle", "96.00%", "🚢"),
    ("Black Assassin", "Rectangle", "96.00%", "🗡️"),
    ("Capricorn's Fortune", "Rectangle", "96.00%", "♑"),
    ("Chicken Uncrossable", "Rectangle", "96.00%", "🐔"),
    ("Disco Fever", "Rectangle", "96.00%", "🕺"),
    ("Eggy Pop", "Rectangle", "96.00%", "🐣"),
    ("Farmageddon", "Rectangle", "96.00%", "🚜"),

    # REVENGE
    ("Fortune Mouse 2", "Revenge", "96.00%", "🐭"),
    ("Fortune Tiger 2", "Revenge", "96.00%", "🐯"),
    ("Fortune Dragon 2", "Revenge", "96.00%", "🐉"),
    ("Fortune Ox 2", "Revenge", "96.00%", "🐂"),
    ("Fortune Chicken", "Revenge", "96.00%", "🐔"),
    ("Fortune Monkey", "Revenge", "96.00%", "🐒"),
    ("Fortune Horse", "Revenge", "96.00%", "🐎"),
    ("Fortune Dog", "Revenge", "96.00%", "🐶"),
    ("Fortune Goat", "Revenge", "96.00%", "🐐"),
    ("Super Dragon Hatch", "Revenge", "96.00%", "🐉"),
    ("Dragon Hatch Reborn", "Revenge", "96.00%", "🐉"),
    ("Treasures of Aztec Rewind", "Revenge", "96.00%", "🏺"),
]

# =========================================================
# ESTRATÉGIAS PREMIUM
# =========================================================
PREMIUM_STRATEGIES = {
    "leve": """💰 Estratégia Premium Leve:
• 3 giros em bet baixa no modo normal
• 5 giros no turbo mantendo a bet
• Se não entrar, faça mais 15 giros no automático
• Parou de responder? encerre e aguarde próxima oportunidade""",
    "media": """💰 Estratégia Premium Média:
• 3 giros em bet baixa no modo normal
• 5 giros no turbo
• Sem resposta? suba 1 nível de bet
• Faça +15 giros no automático
• Após sequência ruim, pausar e reavaliar""",
    "agressiva": """💰 Estratégia Premium Agressiva:
• 3 giros em bet baixa no modo normal
• 5 giros no turbo
• Sem resposta? subir a bet com controle
• Fazer +15 giros no automático
• Limite máximo: 6% da banca por tentativa
• Se bater sequência ruim, reinicie a operação"""
}

# =========================================================
# DB
# =========================================================
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'client',
            plan TEXT NOT NULL DEFAULT 'free',
            brand_name TEXT DEFAULT 'Rainha Games',
            accent_primary TEXT DEFAULT '#B3001B',
            accent_secondary TEXT DEFAULT '#D4AF37',
            accent_dark TEXT DEFAULT '#0B0B0F',
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
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            intro TEXT NOT NULL,
            strategy_level TEXT NOT NULL DEFAULT 'leve',
            footer_link TEXT NOT NULL DEFAULT 'https://beacons.ai/rainhagames',
            footer_text TEXT NOT NULL DEFAULT 'A Rainha Joga aqui:',
            image_url TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            send_time TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            send_date TEXT NOT NULL,
            send_time TEXT NOT NULL,
            template_id INTEGER,
            game_id INTEGER,
            sent_at TEXT NOT NULL,
            telegram_status TEXT DEFAULT '',
            telegram_response TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL
        )
    """)

    # seed settings
    seed_setting(cur, "active_from_time", "14:25")
    seed_setting(cur, "brand_name", "Rainha Games")
    seed_setting(cur, "footer_text", "A Rainha Joga aqui:")
    seed_setting(cur, "footer_link", "https://beacons.ai/rainhagames")
    seed_setting(cur, "theme_primary", "#B3001B")
    seed_setting(cur, "theme_secondary", "#D4AF37")
    seed_setting(cur, "theme_dark", "#0B0B0F")
    seed_setting(cur, "send_interval_seconds", "20")

    # seed plans
    seed_plan(cur, "Free", "R$ 0,00", "Acesso básico ao painel|Catálogo básico|Tema padrão")
    seed_plan(cur, "VIP", "R$ 97,00", "Mais jogos|Mais templates|Ajustes avançados")
    seed_plan(cur, "Premium", "R$ 297,00", "White label|Personalização total|Área admin + cliente")

    # seed admin
    now = now_br_str()
    cur.execute("SELECT id FROM users WHERE username = ?", (DEFAULT_ADMIN_USER,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (username, password, role, plan, brand_name, created_at)
            VALUES (?, ?, 'admin', 'Premium', 'Rainha Games', ?)
        """, (DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASSWORD, now))

    # seed templates
    cur.execute("SELECT id FROM templates WHERE name = 'Entrada Premium'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO templates
            (name, intro, strategy_level, footer_link, footer_text, image_url, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            "Entrada Premium",
            "🎰 Entrada confirmada",
            "media",
            "https://beacons.ai/rainhagames",
            "A Rainha Joga aqui:",
            "",
            now
        ))

    cur.execute("SELECT id FROM templates WHERE name = 'Entrada Premium Agressiva'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO templates
            (name, intro, strategy_level, footer_link, footer_text, image_url, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            "Entrada Premium Agressiva",
            "🎰 Entrada confirmada",
            "agressiva",
            "https://beacons.ai/rainhagames",
            "A Rainha Joga aqui:",
            "",
            now
        ))

    # seed schedules
    existing = cur.execute("SELECT COUNT(*) AS total FROM schedules").fetchone()["total"]
    if existing == 0:
        for t in ["14:25", "15:40", "17:10", "18:30", "20:00", "21:20", "22:40"]:
            cur.execute("INSERT INTO schedules (send_time, active) VALUES (?, 1)", (t,))

    # seed system messages
    seed_system_message(cur, "welcome", "Bem-vinda ao painel premium da Rainha Games 👑")
    seed_system_message(cur, "responsible", "Jogue com responsabilidade. Slots são aleatórios e não garantem resultado.")

    # seed games
    for name, provider, rtp, emoji in SEED_GAMES:
        cur.execute("SELECT id FROM games WHERE name = ?", (name,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO games (name, provider, rtp, emoji, active, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (name, provider, rtp, emoji, now))

    conn.commit()
    conn.close()

def seed_setting(cur, key, value):
    cur.execute("SELECT id FROM settings WHERE key = ?", (key,))
    if not cur.fetchone():
        cur.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))

def seed_plan(cur, name, price, features):
    cur.execute("SELECT id FROM plans WHERE name = ?", (name,))
    if not cur.fetchone():
        cur.execute("INSERT INTO plans (name, price, features, active) VALUES (?, ?, ?, 1)", (name, price, features))

def seed_system_message(cur, kind, content):
    cur.execute("SELECT id FROM system_messages WHERE kind = ?", (kind,))
    if not cur.fetchone():
        cur.execute("INSERT INTO system_messages (kind, content) VALUES (?, ?)", (kind, content))

# =========================================================
# HELPERS
# =========================================================
def now_br():
    return datetime.now(APP_TZ)

def now_br_str():
    return now_br().strftime("%Y-%m-%d %H:%M:%S")

def today_str():
    return now_br().strftime("%Y-%m-%d")

def current_time_str():
    return now_br().strftime("%H:%M")

def get_setting(key, default=""):
    conn = db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key, value):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()

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

def telegram_send(text, image_url=""):
    if not TOKEN or not CHAT_ID:
        return False, "TOKEN ou CHAT_ID não configurados."

    try:
        if image_url.strip():
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            data = {
                "chat_id": CHAT_ID,
                "photo": image_url.strip(),
                "caption": text[:1024]
            }
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": text
            }

        resp = requests.post(url, data=data, timeout=30)
        ok = resp.status_code == 200
        return ok, f"{resp.status_code} - {resp.text[:500]}"
    except Exception as e:
        return False, str(e)

def build_message(game_row, template_row):
    strategy_level = template_row["strategy_level"].lower().strip()
    strategy_text = PREMIUM_STRATEGIES.get(strategy_level, PREMIUM_STRATEGIES["leve"])
    footer_text = template_row["footer_text"].strip() or get_setting("footer_text", "A Rainha Joga aqui:")
    footer_link = template_row["footer_link"].strip() or get_setting("footer_link", "https://beacons.ai/rainhagames")

    provider_line = f"🏢 Provedora: {game_row['provider']}\n" if game_row["provider"] else ""
    rtp_line = f"📊 RTP: {game_row['rtp']}\n" if game_row["rtp"] else "📊 RTP: Verificado ✅\n"

    return f"""{template_row['intro']}

🎮 Jogo: {game_row['name']} {game_row['emoji']}
{provider_line}{rtp_line}
{strategy_text}

⚠️ Operação informativa. Slots são aleatórios. Use gestão e responsabilidade.

━━━━━━━━━━━━━━━
{footer_text}
{footer_link}
━━━━━━━━━━━━━━━"""

def get_rotated_schedules():
    conn = db()
    rows = conn.execute("SELECT send_time FROM schedules WHERE active = 1 ORDER BY send_time").fetchall()
    conn.close()

    times = [r["send_time"] for r in rows]
    if not times:
        return []

    day_num = int(now_br().strftime("%d"))
    rot = day_num % len(times)
    return times[rot:] + times[:rot]

def choose_next_game_and_template():
    conn = db()

    # template ativo
    template_row = conn.execute("""
        SELECT * FROM templates
        WHERE active = 1
        ORDER BY id ASC
        LIMIT 1
    """).fetchone()

    if not template_row:
        conn.close()
        return None, None

    # jogo com rotação simples usando data + total enviados do dia
    sent_today = conn.execute("""
        SELECT COUNT(*) AS total FROM sent_log WHERE send_date = ?
    """, (today_str(),)).fetchone()["total"]

    games = conn.execute("""
        SELECT * FROM games
        WHERE active = 1
        ORDER BY provider ASC, name ASC
    """).fetchall()

    if not games:
        conn.close()
        return None, None

    idx = sent_today % len(games)
    game_row = games[idx]
    conn.close()
    return game_row, template_row

def already_sent_today(send_time):
    conn = db()
    row = conn.execute("""
        SELECT id FROM sent_log
        WHERE send_date = ? AND send_time = ?
        LIMIT 1
    """, (today_str(), send_time)).fetchone()
    conn.close()
    return row is not None

def log_send(send_time, template_id, game_id, status, response):
    conn = db()
    conn.execute("""
        INSERT INTO sent_log (send_date, send_time, template_id, game_id, sent_at, telegram_status, telegram_response)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (today_str(), send_time, template_id, game_id, now_br_str(), "ok" if status else "erro", response[:1000]))
    conn.commit()
    conn.close()

# =========================================================
# SCHEDULER 24H
# =========================================================
def scheduler_loop():
    while True:
        try:
            active_from = get_setting("active_from_time", "14:25")
            interval_seconds = int(get_setting("send_interval_seconds", "20") or "20")
            now_time = current_time_str()

            if now_time >= active_from:
                rotated = get_rotated_schedules()
                for send_time in rotated:
                    if send_time == now_time and not already_sent_today(send_time):
                        game_row, template_row = choose_next_game_and_template()
                        if game_row and template_row:
                            msg = build_message(game_row, template_row)
                            ok, response = telegram_send(msg, template_row["image_url"] or "")
                            log_send(send_time, template_row["id"], game_row["id"], ok, response)
            time.sleep(max(10, interval_seconds))
        except Exception:
            time.sleep(20)

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
    grid-template-columns:1.2fr .8fr;
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
.btn-dark{
    background:rgba(255,255,255,.08);
    color:#fff;
}
.btn-danger{
    background:linear-gradient(180deg, #ff8484 0%, #db3c3c 100%);
    color:#fff;
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
.badge-danger{ background:rgba(255,94,94,.12); color:var(--danger);}
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
.footer-note{
    margin-top:18px;
    color:#cfcfcf;
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
                <a href="{{ url_for('admin_games') }}">Jogos</a>
                <a href="{{ url_for('admin_templates') }}">Mensagens</a>
                <a href="{{ url_for('admin_schedules') }}">Horários</a>
                <a href="{{ url_for('admin_settings') }}">Configurações</a>
                <a href="{{ url_for('sales_plans') }}">Plano de vendas</a>
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
    brand_name = get_setting("brand_name", "Rainha Games")
    return render_template_string(
        BASE_HTML,
        title=title,
        content=content,
        brand_name=brand_name,
        theme_primary=get_setting("theme_primary", "#B3001B"),
        theme_secondary=get_setting("theme_secondary", "#D4AF37"),
        theme_dark=get_setting("theme_dark", "#0B0B0F"),
        session=session
    )

# =========================================================
# AUTH
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
            <div class="footer-note">Tema premium, multiusuário, admin e cliente, white label e painel completo.</div>
        </div>
    </div>
    """
    return render_page("Login", html)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================================================
# DASHBOARD
# =========================================================
@app.route("/")
@require_login
def dashboard():
    conn = db()
    total_games = conn.execute("SELECT COUNT(*) AS total FROM games WHERE active = 1").fetchone()["total"]
    total_templates = conn.execute("SELECT COUNT(*) AS total FROM templates WHERE active = 1").fetchone()["total"]
    total_users = conn.execute("SELECT COUNT(*) AS total FROM users WHERE is_active = 1").fetchone()["total"]
    sent_today = conn.execute("SELECT COUNT(*) AS total FROM sent_log WHERE send_date = ?", (today_str(),)).fetchone()["total"]
    last_log = conn.execute("SELECT * FROM sent_log ORDER BY id DESC LIMIT 1").fetchone()
    current_template = conn.execute("SELECT * FROM templates WHERE active = 1 ORDER BY id ASC LIMIT 1").fetchone()
    current_game, current_template_for_preview = choose_next_game_and_template()
    conn.close()

    preview = "Nenhuma prévia disponível."
    if current_game and current_template_for_preview:
        preview = build_message(current_game, current_template_for_preview)

    schedules = ", ".join(get_rotated_schedules()) or "Nenhum horário ativo"
    active_from = get_setting("active_from_time", "14:25")
    responsible = "Jogue com responsabilidade. Slots são aleatórios."

    html = f"""
    <div class="grid grid-3">
        <div class="card">
            <div class="sub">Jogos ativos</div>
            <div class="kpi">{total_games}</div>
        </div>
        <div class="card">
            <div class="sub">Mensagens ativas</div>
            <div class="kpi">{total_templates}</div>
        </div>
        <div class="card">
            <div class="sub">Envios hoje</div>
            <div class="kpi">{sent_today}</div>
        </div>
    </div>

    <div class="grid grid-2" style="margin-top:18px;">
        <div class="card">
            <h2>Prévia da próxima mensagem</h2>
            <div class="preview">{preview}</div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Status do sistema</h3>
                <div class="sub">Horário atual Brasil</div>
                <div class="kpi">{current_time_str()}</div>
                <div class="sub" style="margin-top:12px;">Início automático diário</div>
                <div class="kpi" style="font-size:24px;">{active_from}</div>
                <div class="sub" style="margin-top:12px;">Horários rotativos de hoje</div>
                <div class="preview">{schedules}</div>
            </div>

            <div class="card">
                <h3>Último envio</h3>
                <div class="sub">Data</div>
                <div>{last_log["send_date"] if last_log else "Ainda não houve envio"}</div>
                <div class="sub" style="margin-top:10px;">Hora</div>
                <div>{last_log["send_time"] if last_log else "-"}</div>
                <div class="sub" style="margin-top:10px;">Status</div>
                <div>{last_log["telegram_status"] if last_log else "-"}</div>
            </div>
        </div>
    </div>

    <div class="card" style="margin-top:18px;">
        <h3>Resumo premium</h3>
        <div class="preview">Sistema rodando 24h, sem parar, com envio automático no Telegram, painel multiusuário, plano de vendas, estratégias premium com variações leve, média e agressiva, RTP aparecendo, rodapé com link e catálogo inicial robusto. {responsible}</div>
    </div>
    """
    return render_page("Painel", html)

# =========================================================
# SALES PLANS
# =========================================================
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
        <div class="sub">Multiusuário, login admin e cliente, white label e personalização total.</div>
    </div>
    <div class="grid grid-3" style="margin-top:18px;">
        {cards}
    </div>
    """
    return render_page("Plano de vendas", html)

# =========================================================
# ADMIN USERS
# =========================================================
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

# =========================================================
# ADMIN GAMES
# =========================================================
@app.route("/admin/games", methods=["GET", "POST"])
@require_admin
def admin_games():
    conn = db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        provider = request.form.get("provider", "").strip()
        rtp = request.form.get("rtp", "").strip()
        emoji = request.form.get("emoji", "🎰").strip() or "🎰"

        if name and provider:
            try:
                conn.execute("""
                    INSERT INTO games (name, provider, rtp, emoji, active, created_at)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (name, provider, rtp, emoji, now_br_str()))
                conn.commit()
                flash("Jogo adicionado.")
            except sqlite3.IntegrityError:
                flash("Esse jogo já existe.")
        else:
            flash("Preencha nome e provedora.")

    q = request.args.get("q", "").strip()
    if q:
        rows = conn.execute("""
            SELECT * FROM games
            WHERE name LIKE ? OR provider LIKE ?
            ORDER BY provider, name
        """, (f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM games ORDER BY provider, name LIMIT 500").fetchall()

    conn.close()

    trs = ""
    for g in rows:
        trs += f"""
        <tr>
            <td>{g['id']}</td>
            <td>{g['name']}</td>
            <td>{g['provider']}</td>
            <td>{g['rtp'] or 'Verificado ✅'}</td>
            <td>{g['emoji']}</td>
            <td>{"Ativo" if g['active'] else "Inativo"}</td>
        </tr>
        """

    html = f"""
    <div class="grid grid-2">
        <div class="card">
            <h2>Novo jogo</h2>
            <form method="post">
                <label>Nome do jogo</label>
                <input name="name" required>
                <label>Provedora</label>
                <input name="provider" required>
                <label>RTP</label>
                <input name="rtp" placeholder="96.50%">
                <label>Emoji</label>
                <input name="emoji" value="🎰">
                <button type="submit">Salvar jogo</button>
            </form>
        </div>

        <div class="card">
            <h2>Catálogo</h2>
            <form method="get">
                <label>Buscar</label>
                <input name="q" value="{q}" placeholder="Ex.: PG, Fortune, Pragmatic">
                <button type="submit">Pesquisar</button>
            </form>
            <div class="table-wrap" style="margin-top:14px;">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Jogo</th>
                            <th>Provedora</th>
                            <th>RTP</th>
                            <th>Emoji</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>{trs}</tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return render_page("Jogos", html)

# =========================================================
# ADMIN TEMPLATES
# =========================================================
@app.route("/admin/templates", methods=["GET", "POST"])
@require_admin
def admin_templates():
    conn = db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        intro = request.form.get("intro", "").strip() or "🎰 Entrada confirmada"
        strategy_level = request.form.get("strategy_level", "leve").strip()
        footer_text = request.form.get("footer_text", "").strip() or "A Rainha Joga aqui:"
        footer_link = request.form.get("footer_link", "").strip() or "https://beacons.ai/rainhagames"
        image_url = request.form.get("image_url", "").strip()

        if name:
            try:
                conn.execute("""
                    INSERT INTO templates
                    (name, intro, strategy_level, footer_link, footer_text, image_url, active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """, (name, intro, strategy_level, footer_link, footer_text, image_url, now_br_str()))
                conn.commit()
                flash("Mensagem salva.")
            except sqlite3.IntegrityError:
                flash("Já existe uma mensagem com esse nome.")
        else:
            flash("Dê um nome para a mensagem.")

    rows = conn.execute("SELECT * FROM templates ORDER BY id DESC").fetchall()
    conn.close()

    trs = ""
    for t in rows:
        trs += f"""
        <tr>
            <td>{t['id']}</td>
            <td>{t['name']}</td>
            <td>{t['strategy_level']}</td>
            <td>{t['footer_text']}</td>
            <td>{'✅' if t['image_url'] else '❌'}</td>
            <td>{"Ativa" if t['active'] else "Inativa"}</td>
        </tr>
        """

    html = f"""
    <div class="grid grid-2">
        <div class="card">
            <h2>Nova mensagem</h2>
            <form method="post">
                <label>Nome</label>
                <input name="name" required>
                <label>Texto de abertura</label>
                <input name="intro" value="🎰 Entrada confirmada">
                <label>Estratégia</label>
                <select name="strategy_level">
                    <option value="leve">Leve</option>
                    <option value="media" selected>Média</option>
                    <option value="agressiva">Agressiva</option>
                </select>
                <label>Texto do rodapé</label>
                <input name="footer_text" value="A Rainha Joga aqui:">
                <label>Link do rodapé</label>
                <input name="footer_link" value="https://beacons.ai/rainhagames">
                <label>URL da imagem opcional</label>
                <input name="image_url">
                <button type="submit">Salvar mensagem</button>
            </form>
        </div>

        <div class="card">
            <h2>Mensagens cadastradas</h2>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nome</th>
                            <th>Estratégia</th>
                            <th>Rodapé</th>
                            <th>Imagem</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>{trs}</tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return render_page("Mensagens", html)

# =========================================================
# ADMIN SCHEDULES
# =========================================================
@app.route("/admin/schedules", methods=["GET", "POST"])
@require_admin
def admin_schedules():
    conn = db()

    if request.method == "POST":
        send_time = request.form.get("send_time", "").strip()
        if len(send_time) == 5 and ":" in send_time:
            conn.execute("INSERT INTO schedules (send_time, active) VALUES (?, 1)", (send_time,))
            conn.commit()
            flash("Horário adicionado.")
        else:
            flash("Use o formato HH:MM.")

    rows = conn.execute("SELECT * FROM schedules ORDER BY send_time").fetchall()
    conn.close()

    trs = ""
    for s in rows:
        trs += f"""
        <tr>
            <td>{s['id']}</td>
            <td>{s['send_time']}</td>
            <td>{"Ativo" if s['active'] else "Inativo"}</td>
        </tr>
        """

    html = f"""
    <div class="grid grid-2">
        <div class="card">
            <h2>Novo horário</h2>
            <form method="post">
                <label>Horário</label>
                <input name="send_time" placeholder="14:25" required>
                <button type="submit">Salvar horário</button>
            </form>
            <div class="footer-note">Os horários giram automaticamente a cada dia.</div>
        </div>
        <div class="card">
            <h2>Horários cadastrados</h2>
            <div class="preview">{", ".join(get_rotated_schedules()) or "Nenhum horário ativo"}</div>
            <div class="table-wrap" style="margin-top:14px;">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Horário</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>{trs}</tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return render_page("Horários", html)

# =========================================================
# ADMIN SETTINGS
# =========================================================
@app.route("/admin/settings", methods=["GET", "POST"])
@require_admin
def admin_settings():
    if request.method == "POST":
        set_setting("brand_name", request.form.get("brand_name", "Rainha Games").strip() or "Rainha Games")
        set_setting("footer_text", request.form.get("footer_text", "A Rainha Joga aqui:").strip() or "A Rainha Joga aqui:")
        set_setting("footer_link", request.form.get("footer_link", "https://beacons.ai/rainhagames").strip() or "https://beacons.ai/rainhagames")
        set_setting("active_from_time", request.form.get("active_from_time", "14:25").strip() or "14:25")
        set_setting("theme_primary", request.form.get("theme_primary", "#B3001B").strip() or "#B3001B")
        set_setting("theme_secondary", request.form.get("theme_secondary", "#D4AF37").strip() or "#D4AF37")
        set_setting("theme_dark", request.form.get("theme_dark", "#0B0B0F").strip() or "#0B0B0F")
        set_setting("send_interval_seconds", request.form.get("send_interval_seconds", "20").strip() or "20")
        flash("Configurações salvas.")
        return redirect(url_for("admin_settings"))

    html = f"""
    <div class="card" style="max-width:760px;">
        <h2>Configurações gerais</h2>
        <form method="post">
            <label>Nome da marca</label>
            <input name="brand_name" value="{get_setting('brand_name', 'Rainha Games')}">

            <label>Texto do rodapé</label>
            <input name="footer_text" value="{get_setting('footer_text', 'A Rainha Joga aqui:')}">

            <label>Link do rodapé</label>
            <input name="footer_link" value="{get_setting('footer_link', 'https://beacons.ai/rainhagames')}">

            <label>Início automático diário</label>
            <input name="active_from_time" value="{get_setting('active_from_time', '14:25')}">

            <label>Intervalo do agendador em segundos</label>
            <input name="send_interval_seconds" value="{get_setting('send_interval_seconds', '20')}">

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

# =========================================================
# TESTE DE ENVIO
# =========================================================
@app.route("/admin/test-send")
@require_admin
def test_send():
    game_row, template_row = choose_next_game_and_template()
    if not game_row or not template_row:
        flash("Cadastre pelo menos um jogo e uma mensagem.")
        return redirect(url_for("dashboard"))

    msg = build_message(game_row, template_row)
    ok, response = telegram_send(msg, template_row["image_url"] or "")
    flash("Teste enviado com sucesso." if ok else f"Erro no teste: {response}")
    return redirect(url_for("dashboard"))

# =========================================================
# START
# =========================================================
init_db()

scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
scheduler_thread.start()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
