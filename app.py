from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3
import threading
import time
from datetime import datetime
import pytz
import os
import requests
import random

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)
FUSO = pytz.timezone("America/Sao_Paulo")
DB_PATH = "/tmp/database.db"

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
    # PG Soft
    "Fortune Tiger": "🐯",
    "Fortune Rabbit": "🐰",
    "Fortune Dragon": "🐉",
    "Fortune Mouse": "🐭",
    "Fortune Ox": "🐂",
    "Fortune Horse": "🐴",
    "Fortune Snake": "🐍",
    # Pragmatic Play
    "Gates of Olympus": "⚡",
    "Sweet Bonanza": "🍬",
    "Big Bass Bonanza": "🐟",
    "The Dog House": "🐕",
    "Starlight Princess": "⭐",
    # Outros jogos
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
    # BGaming
    "Wild Tiger": "🐯⚡",
    "Bonanza Billion": "💎💰",
    "Fruit Million": "🍎🎰",
    "Burning Chilli X": "🌶️🔥",
    "Wild Clusters": "🍇✨",
    # Ruby Play
    "777 Strike": "7️⃣🎰",
    "Aztec Fire": "🔥🏺",
    "Cash Bonanza": "💰🎊",
    "Fire and Gold": "🔥💛",
    "Lucky Piggy": "🐷🍀",
    # Endorphina
    "Book of Aztec": "📖🏺",
    "Twerk": "💃🎵",
    "Satoshi's Secret": "💻🔐",
    "Fruitmania": "🍓🎰",
    "Vegas Nights": "🌃🎲",
    # Playson
    "Solar Queen": "☀️👑",
    "Book of Gold": "📖💛",
    "Burning Wins": "🔥🏆",
    "Pearl River": "💧🐲",
    "Legend of Cleopatra": "👸🏺",
    # Hacksaw Gaming
    "Wanted Dead or a Wild": "🤠🔫",
    "Stick Em": "🎯💥",
    "Chaos Crew": "🦹💣",
    "Cubes": "🧊⚡",
    "Pizza Pays": "🍕💰",
    # 3 Oaks Gaming
    "Hot Triple Sevens": "7️⃣🔥",
    "Candy Boom": "🍬💥",
    "Gold Express": "🚂💛",
    "Mighty Kong": "🦍💪",
    "Book of Tattoo": "📖🎨",
    # Microgaming
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
    # B Gaming
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
    # Fat Panda
    "Panda Panda": "🐼🎋",
    "Lucky Panda": "🐼🍀",
    "Panda Gold": "🐼💛",
    # Spirit Gaming
    "Ox Fortune Spirit": "🐂💰",
    "Mouse Fortune Spirit": "🐭💰",
    "Rabbit Fortune Spirit": "🐰💰",
    "Tiger Fortune Spirit": "🐯💰",
    "Dragon Fortune Spirit": "🐉💰",
    # Original Games
    "Book of Ra": "📖☀️",
    "Lucky Lady's Charm": "🍀💋",
    "Sizzling Hot": "🔥🍒",
}


def gerar_mensagem(nome_jogo):
    emoji = JOGOS.get(nome_jogo, "🎰")
    estrategia = random.choice(ESTRATEGIAS)
    return f"""🎰 SINAL CONFIRMADO 🎰

🎮 Jogo: {nome_jogo} {emoji}

📊 Estratégia:
{estrategia}

⚠️ Jogue com responsabilidade!
🔥 ENTRE COM GERENCIAMENTO!"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS mensagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_jogo TEXT NOT NULL,
        imagem_url TEXT DEFAULT '',
        ultimo_envio TEXT DEFAULT ''
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS horarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hora TEXT NOT NULL
    )""")
    conn.commit()
    conn.close()

init_db()


def enviar_telegram(texto, imagem_url=""):
    if not TOKEN or not CHAT_ID:
        print("TOKEN ou CHAT_ID não configurados.")
        return
    try:
        if imagem_url and imagem_url.strip():
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            data = {"chat_id": CHAT_ID, "photo": imagem_url.strip(), "caption": texto}
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {"chat_id": CHAT_ID, "text": texto}
        resultado = requests.post(url, data=data, timeout=30)
        print(f"Telegram respondeu: {resultado.status_code} - {resultado.text}")
    except Exception as e:
        print(f"Erro ao enviar: {e}")


def buscar_mensagens():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, nome_jogo, imagem_url, ultimo_envio FROM mensagens")
    dados = c.fetchall()
    conn.close()
    return dados


def buscar_horarios():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, hora FROM horarios ORDER BY hora")
    dados = c.fetchall()
    conn.close()
    return dados


def horarios_hoje():
    horarios = [h[1] for h in buscar_horarios()]
    if not horarios:
        return []
    agora = datetime.now(FUSO)
    rotacao = int(agora.strftime("%d")) % len(horarios)
    return horarios[rotacao:] + horarios[:rotacao]


HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Painel Rainha Games</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial; background: #1a1a2e; color: #fff; padding: 20px; }
        h1 { color: #f5c542; text-align: center; font-size: 26px; margin-bottom: 5px; }
        .sub { text-align: center; color: #aaa; margin-bottom: 15px; }
        .hora-box { text-align: center; background: #f5c542; color: #000; padding: 8px; border-radius: 8px; font-weight: bold; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media(max-width:700px){ .grid { grid-template-columns: 1fr; } }
        .card { background: #16213e; border: 1px solid #f5c542; border-radius: 10px; padding: 20px; }
        .card h2 { color: #f5c542; margin-bottom: 15px; font-size: 17px; }
        label { display: block; color: #ccc; margin-bottom: 5px; font-size: 14px; }
        input, select { width: 100%; padding: 10px; background: #0f3460; color: #fff; border: 1px solid #f5c542; border-radius: 6px; margin-bottom: 12px; font-size: 14px; }
        select option { background: #0f3460; }
        .btn { background: #f5c542; color: #000; padding: 10px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px; width: 100%; }
        .btn:hover { background: #e5b532; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th { background: #f5c542; color: #000; padding: 8px; text-align: left; }
        td { padding: 8px; border-bottom: 1px solid #333; }
        tr:hover { background: #0f3460; }
        .tags { background: #0f3460; border-radius: 8px; padding: 12px; margin-top: 15px; }
        .tags span { background: #f5c542; color: #000; padding: 3px 10px; border-radius: 20px; margin: 3px; display: inline-block; font-weight: bold; font-size: 13px; }
        .secao { margin-top: 20px; }
        .del { color: #e8384f; text-decoration: none; }
        .dica { background: #0f3460; border-left: 3px solid #f5c542; border-radius: 6px; padding: 10px; margin-top: 10px; color: #ccc; font-size: 13px; }
    </style>
</head>
<body>
    <h1>👑 Painel Rainha Games</h1>
    <p class="sub">Sistema de sinais automáticos</p>
    <div class="hora-box">🕐 Horário atual Brasil: {{ agora }}</div>
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
            <div class="dica">💡 Estratégia gerada automaticamente e varia a cada envio!</div>
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
                {% for h in horarios_hoje %}<span>{{ h }}</span>
                {% else %}<p style="color:#aaa;font-size:13px;">Nenhum horário ainda</p>{% endfor %}
            </div>
            <table style="margin-top:15px;">
                <tr><th>Horário</th><th>Excluir</th></tr>
                {% for h in todos_horarios %}
                <tr><td>{{ h[1] }}</td><td><a class="del" href="/horario/excluir/{{ h[0] }}">🗑️</a></td></tr>
                {% endfor %}
            </table>
        </div>
    </div>
    <div class="card secao">
        <h2>📋 Jogos cadastrados ({{ mensagens|length }})</h2>
        <table>
            <tr><th>#</th><th>Jogo</th><th>Img</th><th>Último envio</th><th>Ação</th></tr>
            {% for m in mensagens %}
            <tr>
                <td>{{ m[0] }}</td>
                <td>{{ m[1] }}</td>
                <td>{{ '✅' if m[2] else '❌' }}</td>
                <td>{{ m[3] or 'Nunca' }}</td>
                <td><a class="del" href="/excluir/{{ m[0] }}">🗑️</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def painel():
    if request.method == "POST":
        nome_jogo = request.form["nome_jogo"]
        imagem_url = request.form.get("imagem_url", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO mensagens (nome_jogo, imagem_url) VALUES (?, ?)", (nome_jogo, imagem_url))
        conn.commit()
        conn.close()
        return redirect(url_for("painel"))
    agora = datetime.now(FUSO).strftime("%H:%M")
    return render_template_string(HTML,
        agora=agora,
        mensagens=buscar_mensagens(),
        todos_horarios=buscar_horarios(),
        horarios_hoje=horarios_hoje(),
        jogos_lista=sorted(JOGOS.keys())
    )


@app.route("/excluir/<int:msg_id>")
def excluir(msg_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM mensagens WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("painel"))


@app.route("/horario/novo", methods=["POST"])
def novo_horario():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO horarios (hora) VALUES (?)", (request.form["hora"],))
    conn.commit()
    conn.close()
    return redirect(url_for("painel"))


@app.route("/horario/excluir/<int:h_id>")
def excluir_horario(h_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM horarios WHERE id=?", (h_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("painel"))


def verificar_mensagens():
    while True:
        agora = datetime.now(FUSO)
        hora_atual = agora.strftime("%H:%M")
        data_hoje = agora.strftime("%Y-%m-%d")
        horarios = horarios_hoje()
        print(f"Verificando... {hora_atual} | Horários: {horarios}")
        if horarios:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, nome_jogo, imagem_url, ultimo_envio FROM mensagens")
            for i, m in enumerate(c.fetchall()):
                msg_id, nome_jogo, imagem_url, ultimo_envio = m
                if i < len(horarios) and horarios[i] == hora_atual and ultimo_envio != data_hoje:
                    texto = gerar_mensagem(nome_jogo)
                    enviar_telegram(texto, imagem_url)
                    c.execute("UPDATE mensagens SET ultimo_envio=? WHERE id=?", (data_hoje, msg_id))
                    print(f"Enviado: {nome_jogo}")
            conn.commit()
            conn.close()
        time.sleep(20)


threading.Thread(target=verificar_mensagens, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
