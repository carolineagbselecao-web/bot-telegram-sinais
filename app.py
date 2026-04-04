from flask import Flask, render_template_string
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

ESTRATEGIAS = [
    "⚡ ENTRADA CONFIRMADA — aposta baixa por 5 rodadas\n🚀 Aumente na 6ª se não saiu\n📊 Limite de 3 martingales\n💰 Stop loss: 20% da banca",
    "⚡ ENTRADA CONFIRMADA — aguarde 3 rodadas sem ganho e entre na 4ª\n💎 Stop gain: 30%\n🛑 Stop loss: 20% da banca",
    "⚡ ENTRADA CONFIRMADA — observe 5 rodadas antes de entrar\n🎰 3 entradas com 10% da banca\n🛑 Stop loss: 15%",
    "⚡ ENTRADA CONFIRMADA — aposta fixa por 6 rodadas\n💰 Dobre apenas 2 vezes\n🛑 Stop loss: 15%",
    "⚡ ENTRADA CONFIRMADA — aposta baixa por 5 rodadas\n🚀 Aumente na 6ª se não saiu\n💰 Stop gain: 35%",
    "⚡ ENTRADA CONFIRMADA — observe 3 rodadas antes de entrar\n💎 Aposte 8% da banca\n🛑 Stop loss: 25%",
    "⚡ ENTRADA CONFIRMADA — entre após 4 rodadas sem ganho\n💰 Progressão: 5%, 8%, 12%",
    "⚡ ENTRADA CONFIRMADA — jogue leve por 8 rodadas e entre na 9ª\n🛑 Stop loss: 20%",
    "⚡ ENTRADA CONFIRMADA — após 3 perdas seguidas\n💰 Aposte 6% da banca",
    "⚡ ENTRADA CONFIRMADA — após o bônus aparecer 1 vez\n🚀 Entre nas próximas 3 rodadas",
    "⚡ ENTRADA CONFIRMADA — comece com 3% da banca\n💰 Aumente 1% a cada perda\n🏆 Pare ao atingir 25% de lucro",
    "⚡ ENTRADA CONFIRMADA — aposta fixa por 8 rodadas\n💰 Dobre na 9ª se não saiu\n🏆 Stop gain: 35%",
    "⚡ ENTRADA CONFIRMADA — entre com 5% da banca\n🎯 Máximo de 3 tentativas\n💰 Stop gain: 30%",
    "⚡ ENTRADA CONFIRMADA — entre com aposta média\n🔄 Se perder, aguarde 3 rodadas e entre de novo\n💎 Stop gain: 25%",
    "⚡ ENTRADA CONFIRMADA — observe 3 rodadas antes da entrada\n💰 Stop loss: 18% da banca",
]

CABECALHOS = [
    "╔══════════════════╗\n🎰  SINAL CONFIRMADO  🎰\n╚══════════════════╝",
    "🔥━━━━━━━━━━━━━━━━━🔥\n⚡   SINAL LIBERADO   ⚡\n🔥━━━━━━━━━━━━━━━━━🔥",
    "┌─────────────────────┐\n💎     ENTRADA VIP     💎\n└─────────────────────┘",
    "🌟══════════════════🌟\n🎯  SINAL EXCLUSIVO  🎯\n🌟══════════════════🌟",
    "╭──────────────────────╮\n👑   RAINHA GAMES   👑\n╰──────────────────────╯",
    "🏆▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬🏆\n💰  OPORTUNIDADE VIP  💰\n🏆▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬🏆",
    "⚡🎰⚡🎰⚡🎰⚡🎰⚡\n🔥  ENTRADA QUENTE  🔥\n⚡🎰⚡🎰⚡🎰⚡🎰⚡",
]

RODAPES = [
    "⚠️ Nunca aposte mais do que pode perder!\n💪 GESTÃO É TUDO!\n🔥 BORA PRA CIMA!",
    "🛑 Respeite o stop loss!\n💡 Quem tem gestão, tem lucro!\n👑 RAINHA GAMES",
    "⚠️ Nunca aposte mais do que pode perder!\n🚀 VAMOS COM TUDO!\n👑 RAINHA GAMES",
    "💎 Disciplina gera resultado!\n🎯 Foco no gerenciamento!\n🔥 FORÇA TROPA!",
    "🧠 Jogue com inteligência!\n💰 Gestão primeiro, sempre!\n👑 RAINHA GAMES",
]

JOGOS = {
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
    "Bigger Bass Bonanza": "🐟💰",
    "Wild West Gold": "🤠🌵",
    "Joker's Jewels": "🃏💎",
    "Fire in the Hole 3": "💣🔥",
    "San Quentin xWays": "🔒⚡",
    "Tombstone RIP": "💀🪦",
    "Deadwood xNudge": "🤠💀",
    "Mental": "🧠💥",
    "Punk Rocker": "🎸🤘",
    "Book of Shadows": "📖🌑",
    "Infectious 5 xWays": "🦠⚡",
    "Folsom Prison": "🔒🏛️",
    "Brute Force": "💪💥",
    "Dragon's Fire": "🐉🔥",
    "Rainbow Jackpots": "🌈💰",
    "Golden Leprechaun Megaways": "🍀💛",
    "Primate King": "🦍👑",
    "Thor's Lightning": "⚡🔨",
    "Pirates Plenty": "🏴‍☠️💎",
    "Mystery Reels Megaways": "🎰✨",
    "Vault of Anubis": "⚱️👁️",
    "God of Wealth": "🙏💰",
    "Ali Baba's Luck": "🪔💎",
    "Age of the Gods": "⚡👑",
    "Buffalo Blitz": "🦬💨",
    "Gladiator": "⚔️🏛️",
    "Great Blue": "🌊🐳",
    "Heart of the Frontier": "🤠❤️",
    "Kingdoms Rise": "⚔️🏰",
    "Circus Delight": "🎪🎠",
    "Emoji Riches": "😍💰",
    "Wild Ape": "🦍🌴",
    "Ninja vs Samurai": "🥷⚔️",
    "Charge Buffalo": "🦬⚡",
    "Book of Myth": "📖🔮",
    "Lucky Goldenfish": "🐟💛",
    "Dragon Treasure": "🐉💎",
    "Fishing War": "🎣⚔️",
    "Super Bonus Slot": "🎰💥",
    "Lucky Drink": "🍹🍀",
    "Piggy Bank": "🐷💰",
    "Cleo's Book": "📖👸",
    "Big Wild Buffalo": "🦬💥",
    "Dragon's Bonanza": "🐉💎",
    "Mummyland Treasures": "⚱️🏺",
    "Tiger Gold": "🐯💛",
    "Dragon Pearl": "🐉🔮",
    "Lucky Fortune": "🍀💰",
    "Aviator": "✈️💰",
    "Plinko": "🎯💸",
    "Mines": "💣⚠️",
    "Dice": "🎲💰",
    "Fishing God": "🎣🙏",
    "Dragon Legend": "🐉✨",
    "Lucky Koi": "🐠🍀",
    "Golden Toad": "🐸💛",
    "Jungle King": "🌿🦁",
    "Fruit Super Nova": "🍎⭐",
    "Lucky Wheel": "🎡🍀",
    "Space Catcher": "🚀🎯",
    "Coin Flip": "🪙🔄",
    "Fruit Party": "🍇🎉",
    "Lucky Stars": "⭐🍀",
    "Ocean Fortune": "🌊💰",
    "Dragon Ball CP": "🐉⚽",
    "Golden Fish": "🐟💛",
    "Lucky Charm": "🍀✨",
    "Fortune Bull": "🐂💰",
    "Dragon Palace": "🐉🏯",
    "Tiger King": "🐯👑",
    "Ocean King": "🌊👑",
    "Lucky Dragon": "🐉🍀",
    "Caishen Riches": "🧧💰",
    "Dragon Gold": "🐉💛",
    "Fortune Wheel": "🎡💰",
    "Hi-Lo": "🃏⬆️",
    "Keno": "🎯🔢",
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
    "Jurassic World": "🦕🌿",
    "Agent Jane Blonde": "🕵️💋",
    "Mermaids Millions": "🧜💎",
    "Thunderstruck Wild Lightning": "⚡🌩️",
    "Lucky Twins": "🐉🐉",
    "Aztec Gold": "🏺💛",
    "Book of Egypt": "📖🐱",
    "Cleopatra Jewels": "👸💎",
    "Lucky Farm": "🌾🍀",
    "Pirate Gold": "🏴‍☠️💛",
    "Magic Forest": "🌲✨",
    "Safari Heat": "🦁🔥",
    "Thai Flower": "🌸💐",
    "Wolf Moon": "🐺🌙",
    "Panda Panda": "🐼🎋",
    "Lucky Panda": "🐼🍀",
    "Panda Gold": "🐼💛",
    "Ox Fortune": "🐂💰",
    "Mouse Fortune": "🐭💰",
    "Rabbit Fortune": "🐰💰",
    "Tiger Fortune": "🐯💰",
    "Dragon Fortune": "🐉💰",
    "Book of Ra": "📖☀️",
    "Lucky Lady's Charm": "🍀💋",
    "Sizzling Hot": "🔥🍒",
    "Racing King": "🏎️🏆",
    "White Tiger": "🐯⬜",
    "Golden Koi Rise": "🐟💛",
    "Plinko UFO": "🛸💰",
    "Football Strike": "⚽🎯",
    "Lucky Dragons": "🐉🍀",
    "Fortune Fish": "🐟💰",
    "Golden Wheel": "🎡💛",
    "Tiger Boom": "🐯💥",
    "Phoenix Rise": "🦅🔥",
    "Wild Panda": "🐼🌿",
    "Gold Rush": "⛏️💛",
    "Ocean Dragon": "🌊🐉",
    "Buffalo Thunder": "🦬⚡",
    "Aztec Temple": "🏺🌿",
    "Viking Glory": "⚔️🛡️",
    "Revenge of Medusa": "🐍👑",
    "Pirate's Revenge": "🏴‍☠️⚔️",
    "Viking's Revenge": "⚔️🔥",
    "Dragon's Revenge": "🐉💢",
    "Warrior's Revenge": "⚔️💪",
    "Penalty Shootout": "⚽🥅",
    "Virtual Horse Racing": "🏇🏆",
    "Golden Tiger": "🐯💛",
    "Lucky Coins": "🪙🍀",
    "Lucky Sevens": "7️⃣✨",
    "Wild West": "🤠🌵",
    "Devil Fire Twins": "😈🔥",
    "Bone Fortune": "💀🎰",
    "Fortune Hook Boom": "🎣💥",
    "Fortune Hook": "🎣",
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
    "God Hand": "🙏⚡",
    "Infinity Tower": "🗼♾️",
    "Rise of the Mighty Gods": "⚡👑",
    "Magic Ace": "🃏✨",
    "Mjolnir": "⚡🔨",
    "Prosperity Tiger": "🐯💰",
    "Treasure Bowl": "🏺💎",
    "Alibaba's Cave": "🪔💰",
    "Cash Mania": "💵🎰",
    "Doomsday Rampage": "💥🌋",
    "Double Fortune": "🍀🍀",
    "Forbidden Alchemy": "⚗️🔮",
    "Fortune Ganesha": "🐘🙏",
    "Inferno Mayhem": "🔥💀",
    "Eternal Kiss": "💋🌹",
    "Electro Fiesta": "⚡🎉",
    "Halloween Meow": "🎃🐱",
    "Magic Scroll": "📜✨",
    "Futebol Fever": "⚽🔥",
    "Joker Coins": "🃏🪙",
    "Cowboys": "🤠🌵",
    "Chihuahua": "🐕",
    "Elves Town": "🧝🏘️",
    "Bank Robbers": "🏦🦹",
    "Golden Genie": "🧞💛",
    "Poker Win": "♠️💰",
}

LISTA_JOGOS = list(JOGOS.keys())

enviados = {}
escala_cache = {}


def gerar_mensagem(nome_jogo):
    emoji = JOGOS.get(nome_jogo, "🎰")
    estrategia = random.choice(ESTRATEGIAS)
    cabecalho = random.choice(CABECALHOS)
    rodape = random.choice(RODAPES)
    separador = "═" * 22

    return f"""{cabecalho}

🎮 {nome_jogo} {emoji}

{separador}
{estrategia}
{separador}

{rodape}"""


def horario_para_minutos(horario):
    hora, minuto = horario.split(":")
    return int(hora) * 60 + int(minuto)


def minutos_para_horario(total_minutos):
    hora = (total_minutos // 60) % 24
    minuto = total_minutos % 60
    return f"{hora:02d}:{minuto:02d}"


def gerar_escala_do_dia(data_str):
    random.seed(data_str)

    jogos = LISTA_JOGOS.copy()
    random.shuffle(jogos)

    total = len(jogos)
    if total == 0:
        return []

    intervalo = 1440 / total
    horarios_usados = set()
    escala = []

    for i, jogo in enumerate(jogos):
        inicio_faixa = int(i * intervalo)
        fim_faixa = int((i + 1) * intervalo) - 1

        if fim_faixa < inicio_faixa:
            fim_faixa = inicio_faixa

        minuto_total = random.randint(inicio_faixa, fim_faixa)

        while minuto_total in horarios_usados:
            minuto_total = (minuto_total + 1) % 1440

        horarios_usados.add(minuto_total)
        horario = minutos_para_horario(minuto_total)
        escala.append((jogo, horario))

    escala.sort(key=lambda x: horario_para_minutos(x[1]))
    return escala


def obter_escala_diaria():
    hoje = datetime.now(FUSO).strftime("%Y-%m-%d")

    if hoje not in escala_cache:
        escala_cache.clear()
        escala_cache[hoje] = gerar_escala_do_dia(hoje)

    return escala_cache[hoje]


def limpar_enviados_antigos():
    hoje = datetime.now(FUSO).strftime("%Y-%m-%d")
    chaves_para_remover = []

    for chave in enviados:
        if not chave.startswith(f"{hoje}_"):
            chaves_para_remover.append(chave)

    for chave in chaves_para_remover:
        enviados.pop(chave, None)


def ja_enviado(data, jogo, horario):
    return enviados.get(f"{data}_{jogo}_{horario}", False)


def registrar_envio(data, jogo, horario):
    enviados[f"{data}_{jogo}_{horario}"] = True


def enviar_telegram(texto):
    if not TOKEN or not CHAT_ID:
        print("TOKEN ou CHAT_ID não configurados.")
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        resposta = requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": texto},
            timeout=30
        )
        print(f"Telegram respondeu: {resposta.status_code}")
    except Exception as e:
        print(f"Erro ao enviar para o Telegram: {e}")


HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel Rainha Games</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: Arial, sans-serif;
            background: #0b0b0f;
            color: #ffffff;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        h1 {
            color: #d4af37;
            text-align: center;
            font-size: 30px;
            margin-bottom: 6px;
        }

        .sub {
            text-align: center;
            color: #b8b8b8;
            margin-bottom: 20px;
        }

        .hora-box {
            text-align: center;
            background: linear-gradient(135deg, #d4af37, #f3d36b);
            color: #000;
            padding: 12px;
            border-radius: 12px;
            font-weight: bold;
            margin-bottom: 20px;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat {
            background: #15151d;
            border: 1px solid #d4af37;
            border-radius: 14px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 0 12px rgba(212, 175, 55, 0.08);
        }

        .stat-num {
            font-size: 30px;
            font-weight: bold;
            color: #d4af37;
        }

        .stat-label {
            color: #bbbbbb;
            font-size: 13px;
            margin-top: 8px;
        }

        .info-box {
            background: #15151d;
            border: 1px solid #d4af37;
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 0 12px rgba(212, 175, 55, 0.08);
        }

        .info-box strong {
            color: #d4af37;
        }

        .info-box p {
            color: #c2c2c2;
            font-size: 14px;
            line-height: 1.5;
            margin-top: 8px;
        }

        .card {
            background: #15151d;
            border: 1px solid #d4af37;
            border-radius: 14px;
            padding: 20px;
            box-shadow: 0 0 12px rgba(212, 175, 55, 0.08);
        }

        .card h2 {
            color: #d4af37;
            margin-bottom: 15px;
            font-size: 19px;
        }

        .table-wrap {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }

        th {
            background: #d4af37;
            color: #000;
            padding: 12px;
            text-align: left;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #2b2b35;
        }

        tr:hover {
            background: #1b1b24;
        }

        .enviado {
            color: #4caf50;
            font-weight: bold;
        }

        .pendente {
            color: #f3d36b;
            font-weight: bold;
        }

        .proximo {
            background: rgba(212, 175, 55, 0.12) !important;
        }

        .status-proximo {
            color: #66ccff;
            font-weight: bold;
        }

        @media (max-width: 800px) {
            .stats {
                grid-template-columns: 1fr;
            }

            h1 {
                font-size: 24px;
            }

            .card, .info-box, .stat {
                padding: 16px;
            }

            table {
                font-size: 13px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>👑 Painel Rainha Games</h1>
        <p class="sub">Sistema automático ativo 24 horas por dia</p>

        <div class="hora-box">🕐 Horário atual do Brasil: {{ agora }}</div>

        <div class="stats">
            <div class="stat">
                <div class="stat-num">{{ total_jogos }}</div>
                <div class="stat-label">Jogos no sistema</div>
            </div>
            <div class="stat">
                <div class="stat-num" style="color:#4caf50;">{{ enviados_hoje }}</div>
                <div class="stat-label">✅ Enviados hoje</div>
            </div>
            <div class="stat">
                <div class="stat-num">{{ pendentes_hoje }}</div>
                <div class="stat-label">⏳ Pendentes hoje</div>
            </div>
        </div>

        <div class="info-box">
            <strong>🤖 Sistema 24h Ativo</strong>
            <p>
                Os jogos são distribuídos automaticamente ao longo das 24 horas do dia.<br>
                À meia-noite a escala reinicia sozinha e continua rodando sem parar.
            </p>
        </div>

        <div class="card">
            <h2>📅 Escala de hoje — {{ data_hoje }}</h2>
            <div class="table-wrap">
                <table>
                    <tr>
                        <th>Horário</th>
                        <th>Jogo</th>
                        <th>Status</th>
                    </tr>
                    {% for item in escala %}
                    <tr class="{{ 'proximo' if item.proximo else '' }}">
                        <td>{{ item.horario }}</td>
                        <td>{{ item.emoji }} {{ item.jogo }}</td>
                        <td class="{% if item.enviado %}enviado{% elif item.proximo %}status-proximo{% else %}pendente{% endif %}">
                            {% if item.enviado %}
                                ✅ Enviado
                            {% elif item.proximo %}
                                👉 Próximo
                            {% else %}
                                ⏳ Pendente
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def painel():
    limpar_enviados_antigos()

    agora_dt = datetime.now(FUSO)
    agora = agora_dt.strftime("%H:%M")
    data_hoje = agora_dt.strftime("%Y-%m-%d")
    agora_minutos = agora_dt.hour * 60 + agora_dt.minute

    escala_raw = obter_escala_diaria()
    escala = []
    enviados_count = 0
    proximo_marcado = False

    for jogo, horario in escala_raw:
        horario_minutos = horario_para_minutos(horario)
        enviado = ja_enviado(data_hoje, jogo, horario)

        if enviado:
            enviados_count += 1

        proximo = False
        if not enviado and not proximo_marcado and horario_minutos >= agora_minutos:
            proximo = True
            proximo_marcado = True

        escala.append({
            "horario": horario,
            "jogo": jogo,
            "emoji": JOGOS.get(jogo, "🎰"),
            "enviado": enviado,
            "proximo": proximo,
        })

    if not proximo_marcado:
        for item in escala:
            if not item["enviado"]:
                item["proximo"] = True
                break

    return render_template_string(
        HTML,
        agora=agora,
        data_hoje=data_hoje,
        escala=escala,
        total_jogos=len(LISTA_JOGOS),
        enviados_hoje=enviados_count,
        pendentes_hoje=len(LISTA_JOGOS) - enviados_count
    )


def verificar_e_enviar():
    ultimo_dia = None

    while True:
        try:
            agora = datetime.now(FUSO)
            data_hoje = agora.strftime("%Y-%m-%d")
            hora_atual = agora.strftime("%H:%M")

            if ultimo_dia != data_hoje:
                limpar_enviados_antigos()
                escala_cache.clear()
                obter_escala_diaria()
                ultimo_dia = data_hoje
                print(f"Nova escala criada para {data_hoje}")

            escala = obter_escala_diaria()

            for jogo, horario in escala:
                if horario == hora_atual and not ja_enviado(data_hoje, jogo, horario):
                    texto = gerar_mensagem(jogo)
                    enviar_telegram(texto)
                    registrar_envio(data_hoje, jogo, horario)
                    print(f"Enviado: {jogo} às {horario}")

            time.sleep(15)

        except Exception as e:
            print(f"Erro no loop principal: {e}")
            time.sleep(15)


threading.Thread(target=verificar_e_enviar, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
