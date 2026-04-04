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
    """💎 ESTILO PREMIUM — LEVE

🎯 Momento da entrada:
Aguarde 3 rodadas sem bônus ou destaque.

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
Entre após 4 perdas seguidas.

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
Se não responder, pare sem tentar recuperar.""",

    """💎 ESTILO PREMIUM — AGRESSIVA

🎯 Momento da entrada:
Entre quando o jogo estiver apagado por várias rodadas.

🎰 Execução:
➡️ 5 giros no normal
➡️ 5 giros no turbo
➡️ Aumente a bet em 1 nível
➡️ 15 giros no automático
➡️ Feche com 10 giros no automático

🛑 Encerramento:
Estratégia agressiva exige limite definido antes de entrar.""",

    """💎 ESTILO PREMIUM — LEVE

🎯 Momento da entrada:
Entre após observar 5 rodadas mornas.

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

    """💎 ESTILO PREMIUM — AGRESSIVA

🎯 Momento da entrada:
Aguarde 3 perdas seguidas e entre sem pular etapas.

🎰 Execução:
➡️ 4 giros no normal
➡️ 6 giros no turbo
➡️ Suba a bet
➡️ 18 giros no automático
➡️ Se houver pagamento parcial, mantenha a sequência

🛑 Encerramento:
Nunca faça mais de 2 aumentos na mesma entrada.""",
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
    "⚠️ Jogue com responsabilidade!\n💪 GESTÃO É TUDO!\n🔥 BORA PRA CIMA!",
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


def gerar_escala_diaria():
    agora = datetime.now(FUSO)
    data_hoje = agora.strftime("%Y-%m-%d")
    random.seed(data_hoje)
    jogos = LISTA_JOGOS.copy()
    random.shuffle(jogos)
    total = len(jogos)

    if data_hoje == "2026-04-04":
        minuto_inicio = 14 * 60 + 40
        minutos_disponiveis = (24 * 60) - minuto_inicio
    else:
        minuto_inicio = 0
        minutos_disponiveis = 24 * 60

    intervalo = minutos_disponiveis // total
    escala = []
    for i, jogo in enumerate(jogos):
        minuto_total = minuto_inicio + (i * intervalo) + random.randint(0, max(1, intervalo - 1))
        minuto_total = min(minuto_total, 23 * 60 + 59)
        hora = (minuto_total // 60) % 24
        minuto = minuto_total % 60
        horario = f"{hora:02d}:{minuto:02d}"
        escala.append((jogo, horario))

    escala.sort(key=lambda x: x[1])
    return escala


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
        resultado = requests.post(url, data={"chat_id": CHAT_ID, "text": texto}, timeout=30)
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
        body { font-family: Arial; background: #1a1a2e; color: #fff; padding: 20px; }
        h1 { color: #f5c542; text-align: center; font-size: 26px; margin-bottom: 5px; }
        .sub { text-align: center; color: #aaa; margin-bottom: 15px; }
        .hora-box { text-align: center; background: #f5c542; color: #000; padding: 8px; border-radius: 8px; font-weight: bold; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .stat { background: #16213e; border: 1px solid #f5c542; border-radius: 10px; padding: 15px; text-align: center; }
        .stat-num { font-size: 28px; font-weight: bold; color: #f5c542; }
        .stat-label { color: #aaa; font-size: 12px; margin-top: 5px; }
        .info-box { background: #16213e; border: 1px solid #f5c542; border-radius: 10px; padding: 15px; margin-bottom: 20px; text-align: center; }
        .info-box p { color: #aaa; font-size: 13px; margin-top: 8px; }
        .card { background: #16213e; border: 1px solid #f5c542; border-radius: 10px; padding: 20px; }
        .card h2 { color: #f5c542; margin-bottom: 15px; font-size: 17px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { background: #f5c542; color: #000; padding: 8px; text-align: left; }
        td { padding: 8px; border-bottom: 1px solid #333; }
        tr:hover { background: #0f3460; }
        .enviado { color: #4caf50; font-weight: bold; }
        .pendente { color: #f5c542; }
        .proximo { background: #0f3460 !important; }
        @media(max-width:700px){ .stats { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <h1>👑 Painel Rainha Games</h1>
    <p class="sub">Sistema 100% automático — zero configuração manual!</p>
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
        <strong style="color:#f5c542;">🤖 Sistema Automático Ativo</strong>
        <p>{{ total_jogos }} jogos distribuídos automaticamente nas 24 horas.<br>
        Horários e estratégias mudam sozinhos todo dia. Nenhuma ação necessária!</p>
    </div>
    <div class="card">
        <h2>📅 Escala de hoje — {{ data_hoje }}</h2>
        <table>
            <tr><th>Horário</th><th>Jogo</th><th>Status</th></tr>
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
    agora_dt = datetime.now(FUSO)
    agora = agora_dt.strftime("%H:%M")
    data_hoje = agora_dt.strftime("%Y-%m-%d")
    escala_raw = gerar_escala_diaria()
    escala = []
    enviados_count = 0
    proximo_marcado = False
    for jogo, horario in escala_raw:
        env = ja_enviado(data_hoje, jogo, horario)
        if env:
            enviados_count += 1
        proximo = False
        if not env and not proximo_marcado and horario >= agora:
            proximo = True
            proximo_marcado = True
        escala.append({
            "horario": horario,
            "jogo": jogo,
            "emoji": JOGOS.get(jogo, "🎰"),
            "enviado": env,
            "proximo": proximo,
        })
    return render_template_string(HTML,
        agora=agora,
        data_hoje=data_hoje,
        escala=escala,
        total_jogos=len(LISTA_JOGOS),
        enviados_hoje=enviados_count,
        pendentes_hoje=len(LISTA_JOGOS) - enviados_count
    )


def verificar_e_enviar():
    while True:
        agora = datetime.now(FUSO)
        hora_atual = agora.strftime("%H:%M")
        data_hoje = agora.strftime("%Y-%m-%d")
        escala = gerar_escala_diaria()
        for jogo, horario in escala:
            if horario == hora_atual and not ja_enviado(data_hoje, jogo, horario):
                texto = gerar_mensagem(jogo)
                enviar_telegram(texto)
                registrar_envio(data_hoje, jogo, horario)
                print(f"Enviado: {jogo} às {horario}")
        time.sleep(20)


threading.Thread(target=verificar_e_enviar, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
