from flask import (
    Flask,
    request,
    render_template_string,
    redirect,
    url_for,
    session,
    flash,
)
import sqlite3
import threading
import time
from datetime import datetime, timedelta
import pytz
import os
import requests
import random
import re
from functools import wraps

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123456")
SECRET_KEY = os.getenv("SECRET_KEY", "troque-essa-chave")
PORT = int(os.getenv("PORT", "10000"))

app = Flask(__name__)
app.secret_key = SECRET_KEY

FUSO = pytz.timezone("America/Sao_Paulo")
DB_PATH = "database.db"

ESTRATEGIAS = [
    "🔥 Entre com aposta baixa nas primeiras 5 rodadas\n💰 Se não sair, dobre na 6ª entrada\n⚡ Máximo 3 martingales\n🛑 Stop loss: 20% da banca",
    "🎯 Aguarde 3 rodadas sem ganho\n🚀 Entre na 4ª rodada com valor médio\n💎 Stop gain: 30%\n🛑 Stop loss: 20% da banca",
    "💎 Observe 5 rodadas antes de entrar\n🎰 3 entradas com 10% da banca\n⚡ Pare ao primeiro green\n🛑 Stop loss: 15%",
    "🌟 Aposte fixo por 6 rodadas\n💰 Dobre apenas 2 vezes\n🔄 Pare ao primeiro green\n🛑 Stop loss: 15% da banca",
    "⚡ Entre com bet baixo por 5 rodadas\n🚀 Aumente na 6ª se não saiu\n📊 Limite de 3 martingales\n💰 Stop gain: 35%",
    "🎰 Observe 3 rodadas antes de entrar\n💎 Aposte 8% da banca por entrada\n🔥 Máximo 4 tentativas\n🛑 Stop loss: 25%",
    "🌈 Entre somente após 4 rodadas sem ganho\n💰 Bet progressivo: 5%, 8%, 12%\n⚡ Stop gain: 25% de lucro",
    "🃏 Jogue leve nas primeiras 8 rodadas\n🚀 Force entrada na 9ª\n📊 3 martingales e pare\n🛑 Stop loss: 20%",
    "🎯 Entre após sequência de 3 perdas\n💰 Aposte 6% da banca\n🔥 Stop gain: 40%\n🛑 Stop loss: 18%",
    "⚡ Aguarde o bonus aparecer 1 vez\n🚀 Entre nas próximas 3 rodadas\n💎 Aposte 5% da banca\n🛑 Stop loss: 20%",
]

JOGOS = {
    "Fortune Tiger": "🐯",
    "Fortune Rabbit": "🐰",
    "Fortune Dragon": "🐉",
    "Fortune Mouse": "🐭",
    "Fortune Ox": "🐂",
    "Fortune Horse": "🐴",
    "Fortune Snake": "🐍",
    "Gates of Olympus": "⚡",
    "Sweet Bonanza": "🍬",
    "Big Bass Bonanza": "🐟",
    "The Dog House": "🐕",
    "Starlight Princess": "⭐",
    "Devil Fire Twins": "😈🔥",
    "Bone Fortune": "💀",
    "Fortune Hook Boom": "🎣💥",
    "Fortune Hook": "🎣",
    "Joker Coins": "🃏🪙",
    "Lucky Jaguar 500": "🐆",
    "Money Pot": "🍀💰",
    "Pirate Queen 2": "🏴‍☠️👑",
    "Caribbean Queen": "🌊👑",
    "Poseidon": "🔱",
    "Monkey Boom": "🐒💥",
    "Cybercats 500x": "🤖🐱",
    "Hamsta": "🐹",
    "Athens Megaways": "🏛️",
    "Bass Boss": "🐟👑",
    "Cake and Ice Cream": "🎂🍦",
    "Clover Craze": "🍀",
    "Cyber Attack": "💻⚡",
    "Dragon's Fire Megaways": "🐉🔥",
    "God Hand Feature Buy": "🙏⚡",
    "Infinity Tower": "🗼♾️",
    "Rise of the Mighty Gods": "⚡👑",
    "Dead Dear or Deader": "💀🦌",
    "East Coast vs West Coast": "🏙️",
    "Fire in the Hole 3": "💣🔥",
    "Magic Ace": "🃏✨",
    "Mjolnir": "⚡🔨",
    "Money Mags Man": "💰🕴️",
    "Pop Pop Candy": "🍭💥",
    "Prosperity Tiger": "🐯💰",
    "Treasure Bowl": "🏺💎",
    "Alibaba's Cave of Fortune": "🪔💰",
    "Cash Mania": "💵🎰",
    "Diner Delights": "🍔✨",
    "Diner Frenzy Spins": "🍕🎰",
    "Doomsday Rampage": "💥🌋",
    "Double Fortune": "🍀🍀",
    "Dragon Treasure Quest": "🐉💎",
    "Forbidden Alchemy": "⚗️🔮",
    "Fortune Ganesha": "🐘🙏",
    "Graffiti Rush": "🎨💨",
    "Hansel and Gretel": "🍬🏠",
    "Inferno Mayhem": "🔥💀",
    "Jack the Giant Hunter": "🪓👹",
    "Jungle Delight": "🌿🐾",
    "Jurassic Kingdom": "🦕👑",
    "Golden Genie": "🧞💛",
    "Poker Win": "♠️💰",
    "Cowboys": "🤠",
    "Chihuahua": "🐕",
    "Elves Town": "🧝🏘️",
    "Eternal Kiss": "💋🌹",
    "Bank Robbers": "🏦🦹",
    "Big Wild Buffalo": "🦬💥",
    "Electro Fiesta": "⚡🎉",
    "Halloween Meow": "🎃🐱",
    "Magic Scroll": "📜✨",
    "Futebol Fever": "⚽🔥",
    "Wild Tiger": "🐯⚡",
    "Bonanza Billion": "💎💰",
    "Fruit Million": "🍎🎰",
    "Burning Chilli X": "🌶️🔥",
    "Wild Clusters": "🍇✨",
    "777 Strike": "7️⃣🎰",
    "Aztec Fire": "🔥🏺",
    "Cash Bonanza": "💰🎊",
    "Fire and Gold": "🔥💛",
    "Lucky Piggy": "🐷🍀",
    "Book of Aztec": "📖🏺",
    "Twerk": "💃🎵",
    "Satoshi's Secret": "💻🔐",
    "Fruitmania": "🍓🎰",
    "Vegas Nights": "🌃🎲",
    "Solar Queen": "☀️👑",
    "Book of Gold": "📖💛",
    "Burning Wins": "🔥🏆",
    "Pearl River": "💧🐲",
    "Legend of Cleopatra": "👸🏺",
    "Wanted Dead or a Wild": "🤠🔫",
    "Stick Em": "🎯💥",
    "Chaos Crew": "🦹💣",
    "Cubes": "🧊⚡",
    "Pizza Pays": "🍕💰",
    "Hot Triple Sevens": "7️⃣🔥",
    "Candy Boom": "🍬💥",
    "Gold Express": "🚂💛",
    "Mighty Kong": "🦍💪",
    "Book of Tattoo": "📖🎨",
    "Mega Moolah": "🦁💰",
    "Thunderstruck II": "⚡🔨",
    "Immortal Romance": "🧛💕",
    "Break da Bank Again": "🏦💥",
    "Avalon II": "⚔️🏰",
    "Starburst": "⭐💎",
    "Game of Thrones": "👑⚔️",
    "Jurassic World": "🦕🌿",
    "Agent Jane Blonde": "🕵️💋",
    "Mermaids Millions": "🧜💎",
    "Aztec Gold": "🏺💛",
    "Book of Egypt": "📖🐱",
    "Cleopatra Jewels": "👸💎",
    "Dragon's Gold": "🐉💰",
    "Lucky Farm": "🌾🍀",
    "Pirate Gold": "🏴‍☠️💛",
    "Magic Forest": "🌲✨",
    "Safari Heat": "🦁🔥",
    "Thai Flower": "🌸💐",
    "Wolf Moon": "🐺🌙",
    "Panda Panda": "🐼🎋",
    "Lucky Panda": "🐼🍀",
    "Panda Gold": "🐼💛",
    "Ox Fortune Spirit": "🐂💰",
    "Mouse Fortune Spirit": "🐭💰",
    "Rabbit Fortune Spirit": "🐰💰",
    "Tiger Fortune Spirit": "🐯💰",
    "Dragon Fortune Spirit": "🐉💰",
    "Book of Ra": "📖☀️",
    "Lucky Lady's Charm": "🍀💋",
    "Sizzling Hot": "🔥🍒",
}


# =========================
# HELPERS
# =========================
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logado"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def validar_hora(hora):
    return bool(re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", hora or ""))


def validar_url_imagem(url):
    if not url:
        return True
    return url.startswith("http://") or url.startswith("https://")


def agora_br():
    return datetime.now(FUSO)


def gerar_mensagem(nome_jogo):
    emoji = JOGOS.get(nome_jogo, "🎰")
    estrategia = random.choice(ESTRATEGIAS)
    return f"""🎰 SINAL CONFIRMADO 🎰

🎮 Jogo: {nome_jogo} {emoji}

📊 Estratégia:
{estrategia}

⚠️ Jogue com responsabilidade!
🔥 ENTRE COM GERENCIAMENTO!"""


def gerar_alerta(nome_jogo):
    emoji = JOGOS.get(nome_jogo, "🎰")
    return f"""🚨 ATENÇÃO, POSSÍVEL OPORTUNIDADE! 🚨

🎮 Jogo em observação: {nome_jogo} {emoji}

⏳ Fiquem prontos...
Um sinal pode sair em instantes 👀

🔥 Gestão sempre!"""


def gerar_green(nome_jogo):
    emoji = JOGOS.get(nome_jogo, "🎰")
    return f"""✅ GREEN CONFIRMADO ✅

🎮 Jogo: {nome_jogo} {emoji}

💸 Parabéns para quem entrou!
🔥 Comentem: EU FUI"""

def gerar_red(nome_jogo):
    emoji = JOGOS.get(nome_jogo, "🎰")
    return f"""❌ RED CONTROLADO ❌

🎮 Jogo: {nome_jogo} {emoji}

📉 Faz parte da gestão!
💪 Seguimos firmes para o próximo sinal."""


def log_envio(tipo, nome_jogo, status, detalhe=""):
    conn = db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO logs_envio (tipo, nome_jogo, enviado_em, status, detalhe)
        VALUES (?, ?, ?, ?, ?)
    """, (
        tipo,
        nome_jogo,
        agora_br().strftime("%Y-%m-%d %H:%M:%S"),
        status,
        detalhe
    ))
    conn.commit()
    conn.close()


def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_jogo TEXT NOT NULL,
            imagem_url TEXT DEFAULT '',
            ultimo_envio TEXT DEFAULT '',
            ultimo_alerta TEXT DEFAULT '',
            ativo INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hora TEXT NOT NULL UNIQUE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS logs_envio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            nome_jogo TEXT NOT NULL,
            enviado_em TEXT NOT NULL,
            status TEXT NOT NULL,
            detalhe TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()


init_db()


def enviar_telegram(texto, imagem_url=""):
    if not TOKEN or not CHAT_ID:
        detalhe = "TOKEN ou CHAT_ID não configurados."
        print(detalhe)
        return False, detalhe

    try:
        if imagem_url and imagem_url.strip():
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            data = {
                "chat_id": CHAT_ID,
                "photo": imagem_url.strip(),
                "caption": texto
            }
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": texto
            }

        resultado = requests.post(url, data=data, timeout=30)
        ok = resultado.status_code == 200

        detalhe = f"{resultado.status_code} - {resultado.text[:300]}"
        print(f"Telegram respondeu: {detalhe}")
        return ok, detalhe

    except Exception as e:
        detalhe = f"Erro ao enviar: {e}"
        print(detalhe)
        return False, detalhe


def buscar_mensagens():
    conn = db()
    c = conn.cursor()
    c.execute("""
        SELECT id, nome_jogo, imagem_url, ultimo_envio, ultimo_alerta, ativo
        FROM mensagens
        ORDER BY id DESC
    """)
    dados = c.fetchall()
    conn.close()
    return dados


def buscar_horarios():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, hora FROM horarios ORDER BY hora")
    dados = c.fetchall()
    conn.close()
    return dados


def buscar_logs(limit=20):
    conn = db()
    c = conn.cursor()
    c.execute("""
        SELECT id, tipo, nome_jogo, enviado_em, status, detalhe
        FROM logs_envio
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    dados = c.fetchall()
    conn.close()
    return dados


def estatisticas():
    hoje = agora_br().strftime("%Y-%m-%d")
    conn = db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM mensagens WHERE ativo = 1")
    total_jogos = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM horarios")
    total_horarios = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM logs_envio WHERE enviado_em LIKE ?", (f"{hoje}%",))
    envios_hoje = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM logs_envio WHERE tipo='green' AND enviado_em LIKE ?", (f"{hoje}%",))
    greens_hoje = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM logs_envio WHERE tipo='red' AND enviado_em LIKE ?", (f"{hoje}%",))
    reds_hoje = c.fetchone()[0]

    conn.close()

    return {
        "total_jogos": total_jogos,
        "total_horarios": total_horarios,
        "envios_hoje": envios_hoje,
        "greens_hoje": greens_hoje,
        "reds_hoje": reds_hoje,
    }


def horarios_hoje():
    horarios = [h["hora"] for h in buscar_horarios()]
    if not horarios:
        return []

    agora = agora_br()
    rotacao = int(agora.strftime("%d")) % len(horarios)
    return horarios[rotacao:] + horarios[:rotacao]


def preview_mensagem(nome_jogo):
    return gerar_mensagem(nome_jogo)


# =========================
# HTML
# =========================
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Login - Painel Rainha Games</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #0f0f1a, #1a1a2e);
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .box {
            width: 100%;
            max-width: 420px;
            background: #16213e;
            border: 1px solid #f5c542;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,.35);
        }
        h1 { color: #f5c542; text-align: center; margin-bottom: 8px; }
        p { color: #aaa; text-align: center; margin-bottom: 20px; }
        input {
            width: 100%;
            padding: 12px;
            margin-bottom: 12px;
            border-radius: 8px;
            border: 1px solid #f5c542;
            background: #0f3460;
            color: #fff;
        }
        button {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: #f5c542;
            color: #000;
            font-weight: bold;
            cursor: pointer;
        }
        .msg {
            margin-bottom: 12px;
            background: #3d1f25;
            color: #ffb4b4;
            border-left: 4px solid #ff4d4d;
            border-radius: 8px;
            padding: 10px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="box">
        <h1>👑 Painel Rainha Games</h1>
        <p>Faça login para acessar o painel</p>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for m in messages %}
                    <div class="msg">{{ m }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="post">
            <input name="usuario" placeholder="Usuário">
            <input name="senha" type="password" placeholder="Senha">
            <button>Entrar</button>
        </form>
    </div>
</body>
</html>
"""

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Painel Rainha Games</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; padding: 20px; }
        a { text-decoration: none; }
        h1 { color: #f5c542; text-align: center; font-size: 28px; margin-bottom: 6px; }
        .sub { text-align: center; color: #aaa; margin-bottom: 16px; }
        .topbar {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 18px; gap: 10px; flex-wrap: wrap;
        }
        .hora-box {
            background: #f5c542; color: #000; padding: 10px 14px;
            border-radius: 10px; font-weight: bold;
        }
        .logout {
            background: #e8384f; color: #fff; padding: 10px 14px;
            border-radius: 10px; font-weight: bold;
        }
        .stats {
            display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 20px;
        }
        @media(max-width:900px){ .stats { grid-template-columns: repeat(2, 1fr); } }
        @media(max-width:600px){ .stats { grid-template-columns: 1fr; } }
        .stat {
            background: #16213e; border: 1px solid #f5c542;
            border-radius: 12px; padding: 16px; text-align: center;
        }
        .stat .n { font-size: 28px; color: #f5c542; font-weight: bold; }
        .stat .l { font-size: 13px; color: #bbb; margin-top: 4px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media(max-width:900px){ .grid { grid-template-columns: 1fr; } }
        .card {
            background: #16213e; border: 1px solid #f5c542;
            border-radius: 12px; padding: 20px; margin-bottom: 20px;
        }
        .card h2 { color: #f5c542; margin-bottom: 15px; font-size: 18px; }
        label { display: block; color: #ccc; margin-bottom: 5px; font-size: 14px; }
        input, select, textarea {
            width: 100%; padding: 10px; background: #0f3460; color: #fff;
            border: 1px solid #f5c542; border-radius: 8px; margin-bottom: 12px; font-size: 14px;
        }
        select option { background: #0f3460; }
        .btn {
            background: #f5c542; color: #000; padding: 10px 12px; border: none;
            border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 14px;
        }
        .btn:hover { background: #e5b532; }
        .btn-red { background: #e8384f; color: #fff; }
        .btn-blue { background: #4da3ff; color: #fff; }
        .btn-green { background: #1fb86a; color: #fff; }
        .btn-row { display: flex; gap: 8px; flex-wrap: wrap; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th { background: #f5c542; color: #000; padding: 8px; text-align: left; }
        td { padding: 8px; border-bottom: 1px solid #333; vertical-align: top; }
        tr:hover { background: #0f3460; }
        .tags { background: #0f3460; border-radius: 8px; padding: 12px; margin-top: 15px; }
        .tags span {
            background: #f5c542; color: #000; padding: 4px 10px; border-radius: 20px;
            margin: 3px; display: inline-block; font-weight: bold; font-size: 13px;
        }
        .secao { margin-top: 20px; }
        .del { color: #ff7d8e; font-weight: bold; }
        .dica {
            background: #0f3460; border-left: 3px solid #f5c542;
            border-radius: 6px; padding: 10px; margin-top: 10px; color: #ccc; font-size: 13px;
        }
        .flash {
            margin-bottom: 15px; padding: 12px; border-radius: 8px; font-size: 14px;
            background: #0f3460; border-left: 4px solid #f5c542;
        }
        pre {
            white-space: pre-wrap; background: #0f3460; padding: 12px;
            border-radius: 10px; border: 1px solid #2c4f82; margin-top: 10px;
        }
        .mini-form { display: inline; }
        .pill-ok { color: #63e6a7; font-weight: bold; }
        .pill-no { color: #ff8c9a; font-weight: bold; }
    </style>
</head>
<body>
    <h1>👑 Painel Rainha Games</h1>
    <p class="sub">Sistema de sinais automáticos + painel avançado</p>

    <div class="topbar">
        <div class="hora-box">🕐 Horário atual Brasil: {{ agora }}</div>
        <a class="logout" href="/logout">Sair</a>
    </div>

    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for m in messages %}
                <div class="flash">{{ m }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <div class="stats">
        <div class="stat"><div class="n">{{ stats.total_jogos }}</div><div class="l">Jogos ativos</div></div>
        <div class="stat"><div class="n">{{ stats.total_horarios }}</div><div class="l">Horários</div></div>
        <div class="stat"><div class="n">{{ stats.envios_hoje }}</div><div class="l">Envios hoje</div></div>
        <div class="stat"><div class="n">{{ stats.greens_hoje }}</div><div class="l">Greens hoje</div></div>
        <div class="stat"><div class="n">{{ stats.reds_hoje }}</div><div class="l">Reds hoje</div></div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>🎮 Cadastrar Jogo</h2>
            <form method="post" action="/">
                <label>Escolha o jogo:</label>
                <select name="nome_jogo">
                    {% for j in jogos_lista %}
                    <option value="{{ j }}">{{ j }}</option>
                    {% endfor %}
                </select>

                <label>Link da imagem (opcional):</label>
                <input name="imagem_url" placeholder="https://i.imgur.com/...">

                <button class="btn">💾 Salvar Jogo</button>
            </form>
            <div class="dica">💡 O sistema continua gerando estratégia automática e variando a mensagem a cada envio.</div>
        </div>

        <div class="card">
            <h2>⏰ Cadastrar Horário</h2>
            <form method="post" action="/horario/novo">
                <label>Horário (HH:MM):</label>
                <input name="hora" placeholder="Ex: 20:00" maxlength="5">
                <button class="btn">➕ Adicionar</button>
            </form>

            <div class="tags">
                <p style="color:#f5c542;font-weight:bold;margin-bottom:8px;">🔄 Rotação de hoje:</p>
                {% for h in horarios_hoje %}
                    <span>{{ h }}</span>
                {% else %}
                    <p style="color:#aaa;font-size:13px;">Nenhum horário ainda</p>
                {% endfor %}
            </div>

            <table style="margin-top:15px;">
                <tr><th>Horário</th><th>Excluir</th></tr>
                {% for h in todos_horarios %}
                <tr>
                    <td>{{ h["hora"] }}</td>
                    <td><a class="del" href="/horario/excluir/{{ h['id'] }}">🗑️</a></td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>

    <div class="card secao">
        <h2>📋 Jogos cadastrados ({{ mensagens|length }})</h2>
        <table>
            <tr>
                <th>#</th>
                <th>Jogo</th>
                <th>Img</th>
                <th>Último alerta</th>
                <th>Último sinal</th>
                <th>Ações</th>
            </tr>
            {% for m in mensagens %}
            <tr>
                <td>{{ m["id"] }}</td>
                <td>{{ m["nome_jogo"] }}</td>
                <td>{{ '✅' if m["imagem_url"] else '❌' }}</td>
                <td>{{ m["ultimo_alerta"] or 'Nunca' }}</td>
                <td>{{ m["ultimo_envio"] or 'Nunca' }}</td>
                <td>
                    <div class="btn-row">
                        <a class="btn btn-blue" href="/preview/{{ m['id'] }}">Preview</a>
                        <a class="btn" href="/acao/testar/{{ m['id'] }}">Teste</a>
                        <a class="btn" href="/acao/alerta/{{ m['id'] }}">Alerta</a>
                        <a class="btn btn-green" href="/acao/green/{{ m['id'] }}">Green</a>
                        <a class="btn btn-red" href="/acao/red/{{ m['id'] }}">Red</a>
                        <a class="btn" href="/acao/sinal/{{ m['id'] }}">Enviar agora</a>
                        <a class="del" href="/excluir/{{ m['id'] }}">🗑️</a>
                    </div>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>

    {% if preview %}
    <div class="card secao">
        <h2>👀 Preview da mensagem</h2>
        <pre>{{ preview }}</pre>
    </div>
    {% endif %}

    <div class="card secao">
        <h2>📝 Logs recentes</h2>
        <table>
            <tr>
                <th>Quando</th>
                <th>Tipo</th>
                <th>Jogo</th>
                <th>Status</th>
                <th>Detalhe</th>
            </tr>
            {% for l in logs %}
            <tr>
                <td>{{ l["enviado_em"] }}</td>
                <td>{{ l["tipo"] }}</td>
                <td>{{ l["nome_jogo"] }}</td>
                <td>
                    {% if l["status"] == 'ok' %}
                        <span class="pill-ok">OK</span>
                    {% else %}
                        <span class="pill-no">ERRO</span>
                    {% endif %}
                </td>
                <td>{{ l["detalhe"][:120] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""


# =========================
# ROUTES
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        if usuario == ADMIN_USER and senha == ADMIN_PASSWORD:
            session["admin_logado"] = True
            return redirect(url_for("painel"))

        flash("Usuário ou senha inválidos.")
        return redirect(url_for("login"))

    return render_template_string(LOGIN_HTML)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
@login_required
def painel():
    if request.method == "POST":
        nome_jogo = request.form.get("nome_jogo", "").strip()
        imagem_url = request.form.get("imagem_url", "").strip()

        if nome_jogo not in JOGOS:
            flash("Jogo inválido.")
            return redirect(url_for("painel"))

        if not validar_url_imagem(imagem_url):
            flash("Link da imagem inválido. Use http:// ou https://")
            return redirect(url_for("painel"))

        conn = db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO mensagens (nome_jogo, imagem_url) VALUES (?, ?)",
            (nome_jogo, imagem_url)
        )
        conn.commit()
        conn.close()

        flash("Jogo cadastrado com sucesso.")
        return redirect(url_for("painel"))

    agora = agora_br().strftime("%H:%M")
    preview = session.pop("preview_temp", None)

    return render_template_string(
        HTML,
        agora=agora,
        mensagens=buscar_mensagens(),
        todos_horarios=buscar_horarios(),
        horarios_hoje=horarios_hoje(),
        jogos_lista=sorted(JOGOS.keys()),
        preview=preview,
        logs=buscar_logs(),
        stats=estatisticas(),
    )


@app.route("/excluir/<int:msg_id>")
@login_required
def excluir(msg_id):
    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM mensagens WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()
    flash("Jogo removido.")
    return redirect(url_for("painel"))


@app.route("/horario/novo", methods=["POST"])
@login_required
def novo_horario():
    hora = request.form.get("hora", "").strip()

    if not validar_hora(hora):
        flash("Horário inválido. Use HH:MM, exemplo: 20:00")
        return redirect(url_for("painel"))

    conn = db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO horarios (hora) VALUES (?)", (hora,))
        conn.commit()
        flash("Horário adicionado com sucesso.")
    except sqlite3.IntegrityError:
        flash("Esse horário já existe.")
    finally:
        conn.close()

    return redirect(url_for("painel"))


@app.route("/horario/excluir/<int:h_id>")
@login_required
def excluir_horario(h_id):
    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM horarios WHERE id = ?", (h_id,))
    conn.commit()
    conn.close()
    flash("Horário removido.")
    return redirect(url_for("painel"))


@app.route("/preview/<int:msg_id>")
@login_required
def preview(msg_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT nome_jogo FROM mensagens WHERE id = ?", (msg_id,))
    item = c.fetchone()
    conn.close()

    if not item:
        flash("Jogo não encontrado.")
        return redirect(url_for("painel"))

    session["preview_temp"] = preview_mensagem(item["nome_jogo"])
    return redirect(url_for("painel"))


@app.route("/acao/<tipo>/<int:msg_id>")
@login_required
def acao(tipo, msg_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM mensagens WHERE id = ?", (msg_id,))
    item = c.fetchone()
    conn.close()

    if not item:
        flash("Jogo não encontrado.")
        return redirect(url_for("painel"))

    nome_jogo = item["nome_jogo"]
    imagem_url = item["imagem_url"] or ""

    if tipo == "testar":
        texto = f"""🧪 TESTE DO BOT

🎮 Jogo: {nome_jogo} {JOGOS.get(nome_jogo, '🎰')}

✅ Se esta mensagem chegou, o bot está funcionando."""
    elif tipo == "alerta":
        texto = gerar_alerta(nome_jogo)
    elif tipo == "green":
        texto = gerar_green(nome_jogo)
    elif tipo == "red":
        texto = gerar_red(nome_jogo)
    elif tipo == "sinal":
        texto = gerar_mensagem(nome_jogo)
    else:
        flash("Ação inválida.")
        return redirect(url_for("painel"))

    ok, detalhe = enviar_telegram(texto, imagem_url if tipo in ["alerta", "sinal", "testar"] else "")
    log_envio(tipo, nome_jogo, "ok" if ok else "erro", detalhe)

    if ok:
        flash(f"Ação '{tipo}' enviada com sucesso.")
    else:
        flash(f"Erro ao enviar ação '{tipo}'.")

    return redirect(url_for("painel"))


# =========================
# AUTO ENVIO
# =========================
def verificar_mensagens():
    while True:
        try:
            agora = agora_br()
            hora_atual = agora.strftime("%H:%M")
            data_hoje = agora.strftime("%Y-%m-%d")
            hora_alerta = (agora + timedelta(minutes=2)).strftime("%H:%M")
            horarios = horarios_hoje()

            print(f"Verificando... {hora_atual} | alerta+2={hora_alerta} | Horários: {horarios}")

            if horarios:
                conn = db()
                c = conn.cursor()
                c.execute("""
                    SELECT id, nome_jogo, imagem_url, ultimo_envio, ultimo_alerta
                    FROM mensagens
                    WHERE ativo = 1
                    ORDER BY id ASC
                """)
                jogos = c.fetchall()

                for i, m in enumerate(jogos):
                    if i >= len(horarios):
                        continue

                    msg_id = m["id"]
                    nome_jogo = m["nome_jogo"]
                    imagem_url = m["imagem_url"] or ""
                    ultimo_envio = m["ultimo_envio"] or ""
                    ultimo_alerta = m["ultimo_alerta"] or ""
                    horario_jogo = horarios[i]

                    # Alerta automático 2 minutos antes
                    if horario_jogo == hora_alerta and ultimo_alerta != data_hoje:
                        texto_alerta = gerar_alerta(nome_jogo)
                        ok, detalhe = enviar_telegram(texto_alerta, imagem_url)
                        log_envio("alerta_auto", nome_jogo, "ok" if ok else "erro", detalhe)
                        if ok:
                            c.execute(
                                "UPDATE mensagens SET ultimo_alerta = ? WHERE id = ?",
                                (data_hoje, msg_id)
                            )
                            print(f"Alerta enviado: {nome_jogo}")

                    # Sinal automático no horário
                    if horario_jogo == hora_atual and ultimo_envio != data_hoje:
                        texto = gerar_mensagem(nome_jogo)
                        ok, detalhe = enviar_telegram(texto, imagem_url)
                        log_envio("sinal_auto", nome_jogo, "ok" if ok else "erro", detalhe)
                        if ok:
                            c.execute(
                                "UPDATE mensagens SET ultimo_envio = ? WHERE id = ?",
                                (data_hoje, msg_id)
                            )
                            print(f"Enviado: {nome_jogo}")

                conn.commit()
                conn.close()

        except Exception as e:
            print(f"Erro no loop automático: {e}")

        time.sleep(20)


threading.Thread(target=verificar_mensagens, daemon=True).start()


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

