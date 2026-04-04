from flask import Flask
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
    "⚡ ENTRADA CONFIRMADA — jogue leve 8 rodadas e entre na 9ª\n🛑 Stop loss: 20%",
    "⚡ ENTRADA CONFIRMADA — após 3 perdas seguidas\n💰 Aposte 6% da banca",
    "⚡ ENTRADA CONFIRMADA — após bônus aparecer 1x\n🚀 Entre nas próximas 3 rodadas",
]

CABECALHOS = [
    "╔══════════════════╗\n🎰  SINAL CONFIRMADO  🎰\n╚══════════════════╝",
    "🔥━━━━━━━━━━━━━━━━━🔥\n⚡   SINAL LIBERADO   ⚡\n🔥━━━━━━━━━━━━━━━━━🔥",
    "┌─────────────────────┐\n💎     ENTRADA VIP     💎\n└─────────────────────┘",
    "🌟══════════════════🌟\n🎯  SINAL EXCLUSIVO  🎯\n🌟══════════════════🌟",
    "╭──────────────────────╮\n👑   RAINHA GAMES   👑\n╰──────────────────────╯",
]

RODAPES = [
    "⚠️ Nunca aposte mais do que pode perder!\n💪 GESTÃO É TUDO!\n🔥 BORA PRA CIMA!",
    "🛑 Respeite o stop loss!\n💡 Quem tem gestão, tem lucro!\n👑 RAINHA GAMES",
]

JOGOS = {
    "Dragon Ball CP": "🐉⚽",
    "Mental": "🧠💥",
    "Great Blue": "🌊🐳",
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


def gerar_escala_do_dia(data_str):
    random.seed(data_str)
    jogos = LISTA_JOGOS.copy()
    random.shuffle(jogos)

    total = len(jogos)
    intervalo = 1440 // total

    escala = []
    for i, jogo in enumerate(jogos):
        minuto_total = (i * intervalo) + random.randint(0, intervalo - 1)
        minuto_total = min(minuto_total, 1439)

        hora = minuto_total // 60
        minuto = minuto_total % 60
        horario = f"{hora:02d}:{minuto:02d}"

        escala.append((jogo, horario))

    escala.sort(key=lambda x: x[1])
    return escala


def obter_escala():
    hoje = datetime.now(FUSO).strftime("%Y-%m-%d")

    if hoje not in escala_cache:
        escala_cache.clear()
        escala_cache[hoje] = gerar_escala_do_dia(hoje)

    return escala_cache[hoje]


def ja_enviado(data, jogo, horario):
    return enviados.get(f"{data}_{jogo}_{horario}", False)


def registrar_envio(data, jogo, horario):
    enviados[f"{data}_{jogo}_{horario}"] = True


def enviar_telegram(texto):
    if not TOKEN or not CHAT_ID:
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": texto})
    except:
        pass


def verificar_e_enviar():
    while True:
        agora = datetime.now(FUSO)
        data = agora.strftime("%Y-%m-%d")
        hora = agora.strftime("%H:%M")

        escala = obter_escala()

        for jogo, horario in escala:
            if horario == hora and not ja_enviado(data, jogo, horario):
                texto = gerar_mensagem(jogo)
                enviar_telegram(texto)
                registrar_envio(data, jogo, horario)

        time.sleep(20)


threading.Thread(target=verificar_e_enviar, daemon=True).start()

@app.route("/")
def home():
    return "Sistema rodando 24h 🚀"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
