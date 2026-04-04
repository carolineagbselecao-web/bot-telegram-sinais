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
    "⚡ Entre com bet baixo por 5 rodadas\n🚀 Aumente na 6ª se não saiu\n📊 Limite de 3 martingales\n💰 Stop loss: 20% da banca",
    "🎯 Aguarde 3 rodadas sem ganho\n🚀 Entre na 4ª rodada\n💎 Stop gain: 30%\n🛑 Stop loss: 20% da banca",
    "💎 Observe 5 rodadas antes de entrar\n🎰 3 entradas com 10% da banca\n⚡ Pare ao primeiro green\n🛑 Stop loss: 15%",
    "🌟 Aposte fixo por 6 rodadas\n💰 Dobre apenas 2 vezes\n🔄 Pare ao primeiro green\n🛑 Stop loss: 15% da banca",
    "⚡ ENTRADA CONFIRMADA — bet baixo por 5 rodadas\n🚀 Aumente na 6ª se não saiu\n📊 Limite de 3 martingales\n💰 Stop gain: 35%",
    "🎰 Observe 3 rodadas antes de entrar\n💎 Aposte 8% da banca por entrada\n🔥 Máximo 4 tentativas\n🛑 Stop loss: 25%",
    "🌈 Entre após 4 rodadas sem ganho\n💰 Bet progressivo: 5%, 8%, 12%\n⚡ Stop gain: 25% de lucro",
    "🃏 Jogue leve nas primeiras 8 rodadas\n🚀 Entre na 9ª rodada\n📊 3 martingales e pare\n🛑 Stop loss: 20%",
    "🎯 Entre após 3 perdas seguidas\n💰 Aposte 6% da banca\n🔥 Stop gain: 40%\n🛑 Stop loss: 18%",
    "⚡ Aguarde o bônus aparecer 1 vez\n🚀 Entre nas próximas 3 rodadas\n💎 Aposte 5% da banca\n🛑 Stop loss: 20%",
    "🎲 Comece com 3% da banca\n💰 Aumente 1% a cada perda\n🏆 Pare ao atingir 25% de lucro\n🛑 Stop loss: 15%",
    "🔥 Aposte valor fixo\n💎 Máximo 10 rodadas seguidas\n⚡ Dobre apenas uma vez\n🛑 Stop loss: 20%",
    "💥 Entre com 5% da banca\n🎯 3 tentativas no máximo\n💰 Stop gain: 30%\n🛑 Stop loss: 15%",
    "🚀 Entre com bet médio\n🔄 Se perder, aguarde 3 rodadas e entre de novo\n💎 Stop gain: 25%\n🛑 Stop loss: 20%",
    "⚡ Bet fixo por 8 rodadas\n💰 Dobre na 9ª se não saiu\n🏆 Stop gain: 35%\n🛑 Stop loss: 20%",
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
    "Fortune Tiger": "🐯", "Fortune Rabbit": "🐰", "Fortune Dragon": "🐉",
    "Fortune Mouse": "🐭", "Fortune Ox": "🐂", "Fortune Horse": "🐴",
    "Fortune Snake": "🐍", "Mahjong Ways": "🀄", "Wild Bandito": "🤠💥",
    "Treasures of Aztec": "🏺⚡", "Candy Bonanza": "🍬💥", "Leprechaun Riches": "🍀💛",
    "Gates of Olympus": "⚡", "Sweet Bonanza": "🍬", "Big Bass Bonanza": "🐟",
    "The Dog House": "🐕", "Starlight Princess": "⭐", "Sugar Rush": "🍭",
    "Floating Dragon": "🐉🌊", "Bigger Bass Bonanza": "🐟💰", "Wild West Gold": "🤠🌵",
    "Joker's Jewels": "🃏💎", "Fire in the Hole 3": "💣🔥", "San Quentin xWays": "🔒⚡",
    "Tombstone RIP": "💀🪦", "Deadwood xNudge": "🤠💀", "Mental": "🧠💥",
    "Punk Rocker": "🎸🤘", "Book of Shadows": "📖🌑", "Infectious 5 xWays": "🦠⚡",
    "Folsom Prison": "🔒🏛️", "Brute Force": "💪💥", "Dragon's Fire": "🐉🔥",
    "Rainbow Jackpots": "🌈💰", "Golden Leprechaun Megaways": "🍀💛",
    "Primate King": "🦍👑", "Thor's Lightning": "⚡🔨", "Pirates Plenty": "🏴‍☠️💎",
    "Mystery Reels Megaways": "🎰✨", "Vault of Anubis": "⚱️👁️",
    "God of Wealth": "🙏💰", "Ali Baba's Luck": "🪔💎",
    "Age of the Gods": "⚡👑", "Buffalo Blitz": "🦬💨", "Gladiator": "⚔️🏛️",
    "Great Blue": "🌊🐳", "Heart of the Frontier": "🤠❤️", "Kingdoms Rise": "⚔️🏰",
    "Circus Delight": "🎪🎠", "Emoji Riches": "😍💰", "Wild Ape": "🦍🌴",
    "Ninja vs Samurai": "🥷⚔️", "Charge Buffalo": "🦬⚡",
    "Book of Myth": "📖🔮", "Lucky Goldenfish": "🐟💛", "Dragon Treasure": "🐉💎",
    "Fishing War": "🎣⚔️", "Super Bonus Slot": "🎰💥",
    "Lucky Drink": "🍹🍀", "Piggy Bank": "🐷💰", "Cleo's Book": "📖👸",
    "Big Wild Buffalo": "🦬💥", "Dragon's Bonanza": "🐉💎", "Mummyland Treasures": "⚱️🏺",
    "Tiger Gold": "🐯💛", "Dragon Pearl": "🐉🔮", "Lucky Fortune": "🍀💰",
    "Aviator": "✈️💰", "Plinko": "🎯💸", "Mines": "💣⚠️", "Dice": "🎲💰",
    "Fishing God": "🎣🙏", "Dragon Legend": "🐉✨", "Lucky Koi": "🐠🍀",
    "Golden Toad": "🐸💛", "Jungle King": "🌿🦁",
    "Fruit Super Nova": "🍎⭐", "Lucky Wheel": "🎡🍀", "Space Catcher": "🚀🎯",
    "Coin Flip": "🪙🔄", "Fruit Party": "🍇🎉", "Lucky Stars": "⭐🍀",
    "Ocean Fortune": "🌊💰", "Dragon Ball CP": "🐉⚽", "Golden Fish": "🐟💛",
    "Lucky Charm": "🍀✨", "Fortune Bull": "🐂💰", "Dragon Palace": "🐉🏯",
    "Tiger King": "🐯👑", "Ocean King": "🌊👑", "Lucky Dragon": "🐉🍀",
    "Caishen Riches": "🧧💰", "Dragon Gold": "🐉💛", "Fortune Wheel": "🎡💰",
    "Hi-Lo": "🃏⬆️", "Keno": "🎯🔢",
    "Wild Tiger": "🐯⚡", "Bonanza Billion": "💎💰", "Fruit Million": "🍎🎰",
    "Burning Chilli X": "🌶️🔥", "Wild Clusters": "🍇✨",
    "777 Strike": "7️⃣🎰", "Aztec Fire": "🔥🏺", "Cash Bonanza": "💰🎊",
    "Fire and Gold": "🔥💛", "Lucky Piggy": "🐷🍀",
    "Book of Aztec": "📖🏺", "Twerk": "💃🎵", "Satoshi's Secret": "💻🔐",
    "Fruitmania": "🍓🎰", "Vegas Nights": "🌃🎲",
    "Solar Queen": "☀️👑", "Book of Gold": "📖💛", "Burning Wins": "🔥🏆",
    "Pearl River": "💧🐲", "Legend of Cleopatra": "👸🏺",
    "Wanted Dead or a Wild": "🤠🔫", "Stick Em": "🎯💥", "Chaos Crew": "🦹💣",
    "Cubes": "🧊⚡", "Pizza Pays": "🍕💰",
    "Hot Triple Sevens": "7️⃣🔥", "Candy Boom": "🍬💥", "Gold Express": "🚂💛",
    "Mighty Kong": "🦍💪", "Book of Tattoo": "📖🎨",
    "Mega Moolah": "🦁💰", "Thunderstruck II": "⚡🔨", "Immortal Romance": "🧛💕",
    "Break da Bank Again": "🏦💥", "Avalon II": "⚔️🏰", "Jurassic World": "🦕🌿",
    "Agent Jane Blonde": "🕵️💋", "Mermaids Millions": "🧜💎",
    "Thunderstruck Wild Lightning": "⚡🌩️", "Lucky Twins": "🐉🐉",
    "Aztec Gold": "🏺💛", "Book of Egypt": "📖🐱", "Cleopatra Jewels": "👸💎",
    "Lucky Farm": "🌾🍀", "Pirate Gold": "🏴‍☠️💛", "Magic Forest": "🌲✨",
    "Safari Heat": "🦁🔥", "Thai Flower": "🌸💐", "Wolf Moon": "🐺🌙",
    "Panda Panda": "🐼🎋", "Lucky Panda": "🐼🍀", "Panda Gold": "🐼💛",
    "Ox Fortune": "🐂💰", "Mouse Fortune": "🐭💰", "Rabbit Fortune": "🐰💰",
    "Tiger Fortune": "🐯💰", "Dragon Fortune": "🐉💰",
    "Book of Ra": "📖☀️", "Lucky Lady's Charm": "🍀💋", "Sizzling Hot": "🔥🍒",
    "Racing King": "🏎️🏆", "White Tiger": "🐯⬜", "Golden Koi Rise": "🐟💛",
    "Plinko UFO": "🛸💰", "Football Strike": "⚽🎯",
    "Lucky Dragons": "🐉🍀", "Fortune Fish": "🐟💰", "Golden Wheel": "🎡💛",
    "Tiger Boom": "🐯💥", "Phoenix Rise": "🦅🔥", "Wild Panda": "🐼🌿",
    "Gold Rush": "⛏️💛", "Ocean Dragon": "🌊🐉",
    "Buffalo Thunder": "🦬⚡", "Aztec Temple": "🏺🌿", "Viking Glory": "⚔️🛡️",
    "Revenge of Medusa": "🐍👑", "Pirate's Revenge": "🏴‍☠️⚔️",
    "Viking's Revenge": "⚔️🔥", "Dragon's Revenge": "🐉💢", "Warrior's Revenge": "⚔️💪",
    "Penalty Shootout": "⚽🥅", "Virtual Horse Racing": "🏇🏆",
    "Golden Tiger": "🐯💛", "Lucky Coins": "🪙🍀",
    "Lucky Sevens": "7️⃣✨", "Wild West": "🤠🌵",
    "Devil Fire Twins": "😈🔥", "Bone Fortune": "💀🎰", "Fortune Hook Boom": "🎣💥",
    "Fortune Hook": "🎣", "Lucky Jaguar 500": "🐆", "Money Pot": "🍀💰",
    "Pirate Queen 2": "🏴‍☠️👑", "Caribbean Queen": "🌊👑", "Poseidon": "🔱",
    "Monkey Boom": "🐒💥", "Cybercats 500x": "🤖🐱", "Hamsta": "🐹",
    "Athens Megaways": "🏛️", "Bass Boss": "🐟👑", "Cake and Ice Cream": "🎂🍦",
    "Clover Craze": "🍀", "God Hand": "🙏⚡", "Infinity Tower": "🗼♾️",
    "Rise of the Mighty Gods": "⚡👑", "Magic Ace": "🃏✨", "Mjolnir": "⚡🔨",
    "Prosperity Tiger": "🐯💰", "Treasure Bowl": "🏺💎", "Alibaba's Cave": "🪔💰",
    "Cash Mania": "💵🎰", "Doomsday Rampage": "💥🌋", "Double Fortune": "🍀🍀",
    "Forbidden Alchemy": "⚗️🔮", "Fortune Ganesha": "🐘🙏", "Inferno Mayhem": "🔥💀",
    "Eternal Kiss": "💋🌹", "Electro Fiesta": "⚡🎉", "Halloween Meow": "🎃🐱",
    "Magic Scroll": "📜✨", "Futebol Fever": "⚽🔥", "Joker Coins": "🃏🪙",
    "Cowboys": "🤠🌵", "Chihuahua": "🐕", "Elves Town": "🧝🏘️",
    "Bank Robbers": "🏦🦹", "Golden Genie": "🧞💛", "Poker Win": "♠️💰",
}

LISTA_JOGOS = list(JOGOS.keys())

enviados = {}
escala_cache = {}


def limpar_texto_estrategia(texto):
    texto = texto.replace("ESTRATÉGIA CONFIRMADA —", "")
    texto = texto.replace("ESTRATÉGIA CONFIRMADA -", "")
    texto = texto.replace("ESTRATÉGIA CONFIRMADA", "")
    texto = texto.replace("ESTRATÉGIA DO DIA:", "")
    texto = texto.replace("ESTRATÉGIA DO DIA", "")
    return texto.strip()


def gerar_mensagem(nome_jogo):
    emoji = JOGOS.get(nome_jogo, "🎰")
    estrategia = limpar_texto_estrategia(random.choice(ESTRATEGIAS))
    cabecalho = random.choice(CABECALHOS)
    rodape = random.choice(RODAPES)
    separador = "═" * 22

    return f"""{cabecalho}

🎮 {nome_jogo} {emoji}

{separador}
📊 ESTRATÉGIA:
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
    agora = datetime.now(FUSO)
    data_hoje = agora.strftime("%Y-%m-%d")

    if data_hoje not in escala_cache:
        escala_cache.clear()
        escala_cache[data_hoje] = gerar_escala_do_dia(data_hoje)

    return escala_cache[data_hoje]


def limpar_enviados_antigos():
    hoje = datetime.now(FUSO).strftime("%Y-%m-%d")
    chaves_para_remover = []

    for chave in enviados.keys():
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
        resultado = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": texto
            },
            timeout=30
        )
        print(f"Telegram respondeu: {resultado.status_code}")
    except Exception as e:
        print(f"Erro ao enviar: {e}")


HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Painel Rainha Games</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #0d0d0d; color: #fff; padding: 20px; }
        h1 { color: #d4af37; text-align: center; font-size: 28px; margin-bottom: 6px; }
        .sub { text-align: center; color: #bdbdbd; margin-bottom: 18px; }
        .hora-box {
            text-align: center;
            background: linear-gradient(135deg, #d4af37, #f5d76e);
            color: #000;
            padding: 10px;
            border-radius: 10px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat {
            background: #151515;
            border: 1px solid #d4af37;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 0 10px rgba(212,175,55,0.08);
        }
        .stat-num {
            font-size: 30px;
            font-weight: bold;
            color: #d4af37;
        }
        .stat-label {
            color: #bdbdbd;
            font-size: 12px;
            margin-top: 6px;
        }
        .info-box {
            background: #151515;
            border: 1px solid #d4af37;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 0 10px rgba(212,175,55,0.08);
        }
        .info-box p {
            color: #bdbdbd;
            font-size: 13px;
            margin-top: 8px;
            line-height: 1.5;
        }
        .card {
            background: #151515;
            border: 1px solid #d4af37;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 0 12px rgba(212,175,55,0.08);
        }
        .card h2 {
            color: #d4af37;
            margin-bottom: 15px;
            font-size: 18px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th {
            background: #d4af37;
            color: #000;
            padding: 10px;
            text-align: left;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #2d2d2d;
        }
        tr:hover {
            background: #1c1c1c;
        }
        .enviado {
            color: #4caf50;
            font-weight: bold;
        }
        .pendente {
            color: #f5d76e;
        }
        .proximo {
            background: rgba(212,175,55,0.12) !important;
        }
        @media(max-width:700px){
            .stats { grid-template-columns: 1fr; }
            table { font-size: 12px; }
        }
    </style>
</head>
<body>
    <h1>👑 Painel Rainha Games</h1>
    <p class="sub">Sistema automático ativo 24 horas por dia</p>

    <div class="hora-box">🕐 Horário atual Brasil: {{ agora }}</div>

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
        <strong style="color:#d4af37;">🤖 Sistema 24h Ativo</strong>
        <p>
            Os jogos são distribuídos automaticamente ao longo das 24 horas do dia.<br>
            À meia-noite a escala reinicia sozinha e continua rodando sem parar.
        </p>
    </div>

    <div class="card">
        <h2>📅 Escala de hoje — {{ data_hoje }}</h2>
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
                <td class="{{ 'enviado' if item.enviado else 'pendente' }}">
                    {{ '✅ Enviado' if item.enviado else ('👉 Próximo' if item.proximo else '⏳ Pendente') }}
                </td>
            </tr>
            {% endfor %}
        </table>
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
        env = ja_enviado(data_hoje, jogo, horario)

        if env:
            enviados_count += 1

        proximo = False
        if not env and not proximo_marcado and horario_minutos >= agora_minutos:
            proximo = True
            proximo_marcado = True

        escala.append({
            "horario": horario,
            "jogo": jogo,
            "emoji": JOGOS.get(jogo, "🎰"),
            "enviado": env,
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
    ultimo_dia_verificado = None

    while True:
        try:
            agora = datetime.now(FUSO)
            data_hoje = agora.strftime("%Y-%m-%d")
            hora_atual = agora.strftime("%H:%M")

            if ultimo_dia_verificado != data_hoje:
                limpar_enviados_antigos()
                escala_cache.clear()
                obter_escala_diaria()
                ultimo_dia_verificado = data_hoje
                print(f"Nova escala carregada para {data_hoje}")

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
