from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import psycopg2
import psycopg2.extras
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
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

TOKEN = os.getenv("TOKEN", "").strip()
CHAT_ID = os.getenv("CHAT_ID", "").strip()

DEFAULT_ADMIN_USER = os.getenv("ADMIN_USER", "admin").strip()
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123456").strip()
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

AUTO_START_TIME = "00:00"
AUTO_END_TIME = "23:59"
SEND_INTERVAL_MINUTES = 3

SCHEDULER_SLEEP_SECONDS = 10
MAX_LATE_MINUTES = 10

# Tempo máximo de lock em segundos — se travado há mais que isso, considera morto e ignora
LOCK_TIMEOUT_SECONDS = 60

# Lease do scheduler: apenas UMA instância por vez vira líder e pode enviar sinais
SCHEDULER_LEASE_SECONDS = 45
SCHEDULER_INSTANCE_ID = f"{os.getenv('RENDER_INSTANCE_ID') or os.getenv('HOSTNAME') or 'local'}:{os.getpid()}"

DEFAULT_FOOTER_LINK = "https://beacons.ai/rainhagames"
DEFAULT_FOOTER_TEXT = "👑 A RAINHA JOGA AQUI"

app = Flask(__name__)
app.secret_key = SECRET_KEY

# =========================================================
# CATÁLOGO BASE
# =========================================================
PROVIDER_GAMES = {
    "PG Soft": [
        ("Fortune Tiger", "96.81%", "🐯"),
        ("Fortune Ox", "96.75%", "🐂"),
        ("Fortune Rabbit", "96.75%", "🐰"),
        ("Fortune Mouse", "96.72%", "🐭"),
        ("Fortune Dragon", "96.83%", "🐉"),
        ("Fortune Snake", "96.70%", "🐍"),
        ("Fortune Gods", "96.74%", "💰"),
        ("Fortune Horse", "96.72%", "🐎"),
        ("Mahjong Ways", "96.92%", "🀄"),
        ("Mahjong Ways 2", "96.95%", "🀄"),
        ("Wild Bandito", "97.00%", "🤠"),
        ("Medusa", "96.58%", "🐍"),
        ("Medusa II", "96.58%", "🐍"),
        ("Ganesha Gold", "96.49%", "🐘"),
        ("Ganesha Fortune", "96.71%", "🐘"),
        ("Caishen Wins", "96.92%", "💰"),
        ("Dragon Hatch", "96.83%", "🐉"),
        ("Dragon Hatch 2", "96.83%", "🐉"),
        ("Dragon Legend", "96.50%", "🐉"),
        ("Rave Party Fever", "96.32%", "🎧"),
        ("Cocktail Nights", "96.20%", "🍸"),
        ("Speed Winner", "96.53%", "🏎️"),
        ("Bikini Paradise", "96.20%", "👙"),
        ("Galactic Gems", "98.13%", "💎"),
        ("Galaxy Miner", "96.32%", "🚀"),
        ("Crypto Gold", "96.12%", "₿"),
        ("Safari Wilds", "96.31%", "🦁"),
        ("Jurassic Kingdom", "96.18%", "🦖"),
        ("Rise of Apollo", "96.20%", "⚡"),
        ("Totem Wonders", "96.71%", "🗿"),
        ("Opera Dynasty", "96.52%", "🎭"),
        ("Muay Thai Champion", "96.86%", "🥊"),
        ("Ninja vs Samurai", "97.44%", "⚔️"),
        ("Legend of Perseus", "96.31%", "🛡️"),
        ("Legend of Hou Yi", "96.95%", "🏹"),
        ("Lucky Neko", "96.73%", "🐱"),
        ("Lucky Piggy", "96.44%", "🐷"),
        ("Leprechaun Riches", "97.35%", "🍀"),
        ("Shark Bounty", "96.71%", "🦈"),
        ("Wings of Iguazu", "96.29%", "🦜"),
        ("Yakuza Honor", "96.11%", "🕴️"),
        ("Zombie Outbreak", "96.20%", "🧟"),
        ("Mafia Mayhem", "", "🕵️"),
        ("Dragon Tiger Luck", "", "🐉"),
        ("The Great Icescape", "", "❄️"),
        ("Candy Burst", "", "🍬"),
        ("Mystic Potion", "", "🧪"),
        ("Wild Bounty Showdown", "", "🤠"),
        ("Werewolf's Hunt", "", "🐺"),
        ("Flirting Scholar", "", "📜"),
        ("Hip Hop Panda", "", "🐼"),
        ("Tree of Fortune", "", "🌳"),
        ("Three Monkeys", "", "🐒"),
        ("Emperor's Favour", "", "👑"),
        ("Tomb of Treasure", "", "🏺"),
        ("Prosperity Lion", "", "🦁"),
        ("Three Crazy Pigs", "", "🐷"),
        ("Honey Trap of Diao Chan", "", "👸"),
        ("Grimms' Bounty Hansel & Gretel", "", "🍭"),
        ("Sushi Oishi", "", "🍣"),
        ("Vampire's Charm", "", "🧛"),
        ("Double Fortune", "", "🍀"),
        ("Jungle Delight", "", "🌿"),
        ("Golden Genie", "", "🧞"),
        ("Poker Win", "", "♠️"),
        ("Cowboys", "", "🤠"),
        ("Chihuahua", "", "🐕"),
        ("Elves Town", "", "🧝"),
        ("Eternal Kiss", "", "💋"),
        ("Bank Robbers", "", "🏦"),
        ("Big Wild Buffalo", "", "🦬"),
        ("Electro Fiesta", "", "⚡"),
        ("Halloween Meow", "", "🎃"),
        ("Magic Scroll", "", "📜"),
        ("Futebol Fever", "", "⚽"),
        ("Treasure Bowl", "", "🏺"),
        ("Fortune Ganesha", "", "🐘"),
        ("Dragon Treasure Quest", "", "🐉"),
        ("Forbidden Alchemy", "", "⚗️"),
        ("Graffiti Rush", "", "🎨"),
        ("Hansel and Gretel", "", "🍬"),
        ("Inferno Mayhem", "", "🔥"),
        ("Jack the Giant Hunter", "", "🪓"),
        ("Alibaba's Cave of Fortune", "", "🪔"),
        ("Cash Mania", "", "💵"),
        ("Diner Delights", "", "🍔"),
        ("Diner Frenzy Spins", "", "🍕"),
        ("Doomsday Rampage", "", "💥"),
    ],
    "Pragmatic Play": [
        ("Gates of Olympus", "96.50%", "⚡"),
        ("Gates of Olympus 1000", "96.50%", "⚡"),
        ("Sweet Bonanza", "96.51%", "🍭"),
        ("Sweet Bonanza Xmas", "96.48%", "🎄"),
        ("Sweet Bonanza 1000", "96.50%", "🍭"),
        ("Starlight Princess", "96.50%", "⭐"),
        ("Starlight Princess 1000", "96.50%", "⭐"),
        ("Big Bass Bonanza", "96.71%", "🎣"),
        ("Big Bass Splash", "96.71%", "🎣"),
        ("Big Bass Bonanza Megaways", "96.70%", "🎣"),
        ("Big Bass Halloween", "96.50%", "🎃"),
        ("Big Bass Christmas Bash", "96.50%", "🎄"),
        ("Big Bass Day at the Races", "", "🏇"),
        ("Big Bass Amazon Xtreme", "", "🌿"),
        ("The Dog House", "96.51%", "🐶"),
        ("The Dog House Megaways", "96.55%", "🐶"),
        ("Fruit Party", "96.50%", "🍓"),
        ("Fruit Party 2", "96.50%", "🍓"),
        ("Fruit Party 1000", "96.50%", "🍓"),
        ("Sugar Rush", "96.50%", "🍬"),
        ("Sugar Rush 1000", "96.50%", "🍬"),
        ("Wolf Gold", "96.01%", "🐺"),
        ("Wolf Gold Ultimate", "96.50%", "🐺"),
        ("Buffalo King", "96.06%", "🦬"),
        ("Buffalo King Megaways", "96.78%", "🦬"),
        ("Buffalo King Untamed", "96.50%", "🦬"),
        ("Great Rhino", "95.97%", "🦏"),
        ("Great Rhino Megaways", "96.58%", "🦏"),
        ("Extra Juicy", "96.50%", "🍉"),
        ("Extra Juicy Megaways", "96.52%", "🍉"),
        ("Juicy Fruits", "96.50%", "🍓"),
        ("Hot Fiesta", "96.08%", "🌶️"),
        ("Chili Heat", "96.50%", "🌶️"),
        ("Release the Kraken", "96.50%", "🐙"),
        ("Hand of Midas", "96.50%", "✋"),
        ("Power of Thor", "96.55%", "⚡"),
        ("Power of Thor Megaways", "96.55%", "⚡"),
        ("5 Lions", "96.50%", "🦁"),
        ("5 Lions Megaways", "96.50%", "🦁"),
        ("5 Lions Gold", "", "🦁"),
        ("Aztec Gems", "96.50%", "🏺"),
        ("Aztec Gems Deluxe", "96.50%", "🏺"),
        ("Aztec King Megaways", "", "👑"),
        ("Wild West Gold", "96.51%", "🤠"),
        ("Wild West Gold Megaways", "96.54%", "🤠"),
        ("Pirate Gold", "96.50%", "🏴‍☠️"),
        ("Pirate Gold Deluxe", "", "🏴‍☠️"),
        ("Queen of Gold", "96.50%", "👑"),
        ("Emerald King", "96.50%", "💎"),
        ("Cyber Heist", "96.50%", "🤖"),
        ("Spaceman", "96.50%", "🚀"),
        ("Zeus Unleashed", "96.50%", "⚡"),
        ("Hades Inferno", "96.50%", "🔥"),
        ("Fire Strike", "", "🔥"),
        ("Book of Tut", "", "📖"),
        ("Cash Elevator", "", "🛗"),
        ("Wild Wild Riches", "", "🤠"),
        ("Eye of Cleopatra", "", "👁️"),
        ("Piggy Bankers", "", "🐷"),
        ("Joker's Jewels", "", "🃏"),
        ("Idol Pop Fever", "", "🎤"),
        ("Snow Party", "", "❄️"),
        ("Jelly Express", "", "🍬"),
        ("Triple Pot Diamond", "", "💎"),
        ("Happy Dragon", "", "🐉"),
        ("Steamin' Reels", "", "🚂"),
        ("CULT", "", "🔮"),
        ("Lucky's Wild Pub 2", "", "🍺"),
        ("Big Bass Raceday Repeat", "", "🏇"),
        ("Diamond Strike", "", "💎"),
        ("Vegas Nights", "", "🎰"),
        ("Book of Kingdoms", "", "📖"),
        ("Book of Aztec", "", "📖"),
        ("Queen of Atlantis", "", "🌊"),
        ("Octobeer", "", "🍺"),
        ("Vikings Unleashed", "", "⚔️"),
        ("Gladiator Legends", "", "🛡️"),
        ("Zombie Carnival", "", "🧟"),
        ("Curse of the Werewolf", "", "🐺"),
        ("Magician's Secret", "", "🎩"),
    ],
    "Hacksaw": [
        ("Wanted Dead or a Wild", "96.38%", "🤠"),
        ("The Bowery Boys", "96.41%", "🦹"),
        ("Frutz", "96.40%", "🍓"),
        ("Aztec Twist", "96.36%", "🏺"),
        ("Joker Bombs", "96.48%", "🃏"),
        ("Cash Compass", "96.42%", "🧭"),
        ("Densho", "96.40%", "⛩️"),
        ("RIP City", "96.22%", "💀"),
        ("Cubes 2", "96.38%", "🧊"),
        ("Hand of Anubis", "96.24%", "🐺"),
        ("Eye of Medusa", "96.20%", "👁️"),
        ("Chaos Crew 2", "96.30%", "💥"),
        ("Chaos Crew 3", "96.30%", "💥"),
        ("Beam Boys", "96.30%", "⚡"),
        ("Le Bandit", "96.30%", "🎭"),
        ("Donut Division", "96.30%", "🍩"),
        ("2 Wild 2 Die", "96.30%", "💥"),
        ("Duel at Dawn", "96.30%", "🌅"),
        ("Bullets and Bounty", "96.30%", "🎯"),
        ("The Luxe", "96.30%", "💎"),
        ("Le Cowboy", "96.28%", "🤠"),
        ("Marlin Masters", "96.28%", "🐟"),
        ("Fist of Destruction", "96.30%", "👊"),
        ("Slayers Inc", "96.30%", "⚔️"),
        ("Benny the Beer", "96.30%", "🍺"),
        ("Keep Em", "96.27%", "🥫"),
        ("King Carrot", "96.30%", "🥕"),
        ("Klowns", "96.30%", "🤡"),
        ("Hounds of Hell", "96.30%", "🐕"),
        ("Le Viking", "96.30%", "🛡️"),
        ("Wings of Horus", "96.30%", "🦅"),
        ("Rise of Ymir", "96.30%", "🧊"),
        ("Shaolin Master", "96.30%", "🥋"),
        ("Stormborn", "96.30%", "⛈️"),
        ("Tiger Legends", "96.30%", "🐯"),
        ("Le Zeus", "96.30%", "⚡"),
        ("Fire My Laser", "96.30%", "🔫"),
    ],
    "Spribe": [
        ("Aviator", "", "✈️"),
        ("Mines", "", "💣"),
        ("Plinko", "", "🔴"),
        ("Dice", "", "🎲"),
        ("HiLo", "", "🃏"),
        ("Goal", "", "⚽"),
        ("Balloon", "", "🎈"),
        ("Keno", "", "🔢"),
    ],
    "Microgaming": [
        ("Immortal Romance", "", "🧛"),
        ("Thunderstruck II", "", "⚡"),
        ("Break da Bank Again", "", "🏦"),
        ("Ladies Nite", "", "🌙"),
        ("Jurassic Park", "", "🦖"),
        ("Mayan Princess", "", "👑"),
        ("Lucky Riches Hyperspins", "", "💰"),
        ("Game of Thrones", "", "🐉"),
        ("Dead or Alive 2", "", "🤠"),
        ("Book of Oz", "", "📖"),
    ],
    "BGaming": [
        ("Wild Tiger", "", "🐯"),
        ("Bonanza Billion", "", "💰"),
        ("Fruit Million", "", "🍎"),
        ("Burning Chilli X", "", "🌶️"),
        ("Wild Clusters", "", "🍇"),
        ("Lucky Lady Moon", "", "🌙"),
        ("Elvis Frog in Vegas", "", "🐸"),
        ("Merge Up", "", "🧩"),
        ("Space XY", "", "🚀"),
        ("Alice WonderLuck", "", "🐇"),
    ],
    "Ruby Play": [
        ("Diamond Explosion 7s", "", "💎"),
        ("Mayan Cache", "", "🏺"),
        ("Go High Panda", "", "🐼"),
        ("Shake Shake Money Tree", "", "🌳"),
        ("Immortal Ways Diamonds", "", "💠"),
    ],
    "Playson": [
        ("Coin Strike Hold and Win", "", "🪙"),
        ("Buffalo Power Hold and Win", "", "🦬"),
        ("Royal Coins 2 Hold and Win", "", "👑"),
        ("Luxor Gold Hold and Win", "", "🏺"),
        ("Book del Sol", "", "📖"),
    ],
    "Endorphina": [
        ("Lucky Streak 1000", "", "🍀"),
        ("2027 ISS", "", "🚀"),
        ("Hell Hot 100", "", "🔥"),
        ("Minotaurus", "", "🐂"),
        ("Book of Santa", "", "🎅"),
    ],
    "3 Oaks Gaming": [
        ("Coin Volcano", "", "🌋"),
        ("Sun of Egypt 3", "", "☀️"),
        ("3 Hot Chillies", "", "🌶️"),
        ("Lucky Penny", "", "🪙"),
        ("Grab the Gold", "", "🥇"),
    ],
    "Red Tiger": [
        ("Dragon's Fire Megaways", "", "🐉"),
        ("Athens Megaways", "", "🏛️"),
        ("Cash Volt", "", "⚡"),
        ("Gonzo's Quest Megaways", "", "🗺️"),
        ("Pirates' Plenty Battle for Gold", "", "🏴‍☠️"),
    ],
    "Spirit": [
        ("Ox Fortune Spirit", "", "🐂"),
        ("Mouse Fortune Spirit", "", "🐭"),
        ("Rabbit Fortune Spirit", "", "🐰"),
        ("Tiger Fortune Spirit", "", "🐯"),
        ("Dragon Fortune Spirit", "", "🐉"),
    ],
    "Original": [
        ("Aviator", "97.00%", "✈️"),
        ("Classic Dice", "99.00%", "🎲"),
        ("Dice", "99.00%", "🎲"),
        ("Doctor Rocket", "97.00%", "🚀"),
        ("Football Scratch", "97.00%", "⚽"),
        ("Heads Tails", "97.00%", "🪙"),
        ("HiLo", "99.00%", "🃏"),
        ("Limbo", "99.00%", "🎯"),
        ("Lucky Wheel", "97.00%", "🎡"),
        ("Mines", "99.00%", "💣"),
        ("Mines2", "99.00%", "💣"),
        ("Penalty Shootout", "97.00%", "⚽"),
        ("Plinko", "99.00%", "🔴"),
        ("Tower", "97.00%", "🗼"),
    ],
    "Betby": [
        ("Betby Dice", "", "🎲"),
        ("Betby Mines", "", "💣"),
        ("Betby Crash", "", "💥"),
    ],
    "Easybet": [
        ("Easy Crash", "", "💥"),
        ("Easy Dice", "", "🎲"),
        ("Easy Mines", "", "💣"),
    ],
    "1Bet": [
        ("1Bet Crash", "", "💥"),
        ("1Bet Dice", "", "🎲"),
        ("1Bet Mines", "", "💣"),
    ],
    "BB Games": [
        ("Book of Darkness", "", "📖"),
        ("Candy Boom", "", "🍬"),
        ("Golden Riches", "", "💰"),
    ],
    "Pateplay": [
        ("Pate Crash", "", "💥"),
        ("Pate Dice", "", "🎲"),
        ("Pate Fortune", "", "🍀"),
    ],
    "759 Gaming": [
        ("Fortune Gems", "", "💎"),
        ("Super Ace", "", "🂡"),
        ("Lucky Panda 759", "", "🐼"),
        ("Golden Dragon 759", "", "🐉"),
        ("Wild Phoenix", "", "🔥"),
        ("Monkey Riches", "", "🐒"),
        ("Fortune Queen", "", "👑"),
        ("Treasure Spin", "", "🏺"),
        ("Lucky Lantern", "", "🏮"),
        ("Cash Wheel", "", "💵"),
    ],
    "Revenge Games": [
        ("Revenge of Medusa", "", "🐍"),
        ("Revenge Crash", "", "💥"),
        ("Revenge Fortune", "", "🍀"),
        ("Revenge Joker", "", "🃏"),
        ("Revenge Dragon", "", "🐉"),
    ],
    "Rectangle Games": [
        ("Rectangle Fortune", "", "🍀"),
        ("Rectangle Wilds", "", "🃏"),
        ("Rectangle Dragon", "", "🐉"),
        ("Rectangle Tiger", "", "🐯"),
        ("Rectangle Queen", "", "👑"),
        ("Rectangle Riches", "", "💰"),
        ("Rectangle Bonanza", "", "🎰"),
        ("Rectangle 7s", "", "7️⃣"),
        ("Rectangle Pirate", "", "🏴‍☠️"),
        ("Rectangle Aztec", "", "🏺"),
    ],
    "Fat Panda": [
        ("Panda Panda", "", "🐼"),
        ("Lucky Panda", "", "🐼"),
        ("Panda Gold", "", "🐼"),
    ],
    "Funky Games": [
        ("Funky Fruits", "", "🍓"),
        ("Funky Spins", "", "🎰"),
        ("Funky Fortune", "", "🍀"),
    ],
    "Playtech": [
        ("Buffalo Blitz", "", "🦬"),
        ("Age of the Gods", "", "⚡"),
        ("Gladiator Jackpot", "", "🛡️"),
        ("Blue Wizard", "", "🧙"),
        ("Great Blue", "", "🦈"),
    ],
    "Belatra": [
        ("Mummyland Treasures", "", "🏺"),
        ("Make it Gold", "", "🥇"),
        ("Golden Øks", "", "🪓"),
    ],
    "TaDa Gaming": [
        ("Lucky Jaguar", "", "🐆"),
        ("Fortune Gems TaDa", "", "💎"),
        ("Treasure Pot", "", "🏺"),
        ("Dragon Bounty", "", "🐉"),
        ("Zeus Rush", "", "⚡"),
    ],
    "OneTouch": [
        ("Lucky Bounty", "", "🍀"),
        ("Sherwood Gold", "", "🏹"),
        ("Golden Lion", "", "🦁"),
    ],
}

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
    "slots_leve": [
        "💎 Estilo Premium Leve:\n• 3 giros em bet baixa no normal\n• 5 giros no turbo mantendo a bet\n• Se não responder, faça mais 15 giros no automático\n• Sem insistir além disso",
        "💎 Estilo Premium Leve:\n• Comece com 3 giros em bet baixa\n• Depois faça 5 giros no turbo\n• Finalize com 15 giros no automático\n• Se não encaixar, aguarde a próxima",
    ],
    "slots_media": [
        "💎 Estilo Premium Média:\n• 3 giros em bet baixa no normal\n• 5 giros no turbo\n• Sem resposta? suba 1 nível de bet\n• Faça +15 giros no automático",
        "💎 Estilo Premium Média:\n• Inicie com 3 giros em bet baixa\n• Vá para 5 giros no turbo\n• Suba 1 nível com controle\n• Feche com 15 giros no automático",
    ],
    "slots_agressiva": [
        "💎 Estilo Premium Agressiva:\n• 3 giros em bet baixa no normal\n• 5 giros no turbo\n• Sem resposta? subir a bet com controle\n• Fazer +15 giros no automático\n• Limite máximo: 6% da banca",
        "💎 Estilo Premium Agressiva:\n• Comece leve com 3 giros no normal\n• Faça 5 giros no turbo\n• Suba a bet de forma controlada\n• Finalize com 15 giros no automático\n• Nunca ultrapasse 6% da banca",
    ],
    "crash": [
        "💎 Estilo Premium Crash:\n• Entrar com 3% da banca\n• Buscar saída entre 1.5x e 2x\n• Não perseguir multiplicador alto\n• Se perder 3 seguidas, pausar 5 minutos",
        "💎 Estilo Premium Crash:\n• Entrada pequena e fixa\n• Saída antecipada sem hesitar\n• No máximo 5 rodadas por sessão\n• Stop loss: 15% da banca",
    ],
    "aviator": [
        "💎 Estilo Premium Aviator:\n• Entre com 3% da banca\n• Retire entre 1.5x e 2x sem hesitar\n• Não persiga multiplicadores altos\n• Stop loss: 3 derrotas seguidas = pausa de 5 min",
        "💎 Estilo Premium Aviator:\n• Bet fixa e pequena\n• Saída disciplinada antes de 2x\n• Máximo 5 rodadas por sessão\n• Se perder 3 seguidas, encerre a sessão",
    ],
    "mines": [
        "💎 Estilo Premium Mines:\n• Configurar 5 minas\n• Abrir no máximo 4 campos\n• Sair na 3ª ou 4ª abertura\n• Pare ao perder 3 rodadas seguidas",
        "💎 Estilo Premium Mines:\n• Gestão leve no início\n• Não forçar quinta abertura\n• Sessão curta\n• Controle total da banca",
    ],
    "dice": [
        "💎 Estilo Premium Dice:\n• Entrada pequena e fixa\n• Não aumentar agressivamente após perda\n• Trabalhar sessões curtas\n• Meta curta e pausa",
        "💎 Estilo Premium Dice:\n• Buscar constância, não emoção\n• Stop loss curto\n• Stop win rápido\n• Evite maratonar",
    ],
    "hilo": [
        "💎 Estilo Premium HiLo:\n• Bet fixa e pequena por rodada\n• Máximo 8 rodadas por sessão\n• Não dobre após perda\n• Stop loss: 5 erros seguidos = encerra",
        "💎 Estilo Premium HiLo:\n• Escolha sempre a mesma direção por sessão\n• Gestão rigorosa da banca\n• Sessão curta com meta definida\n• Pare ao atingir o stop win",
    ],
    "limbo": [
        "💎 Estilo Premium Limbo:\n• Entre com aposta fixa e pequena\n• Defina o multiplicador alvo antes de jogar\n• Não altere o alvo no meio da sessão\n• Stop loss: 15% da banca",
        "💎 Estilo Premium Limbo:\n• Multiplicador alvo entre 1.5x e 3x\n• Bet fixa sem progressão\n• Máximo 10 rodadas por sessão\n• Encerre ao atingir o objetivo",
    ],
    "plinko": [
        "💎 Estilo Premium Plinko:\n• Use risco baixo ou médio\n• Bet fixa por lançamento\n• Máximo 15 lançamentos por sessão\n• Não aumente a bet após sequência negativa",
        "💎 Estilo Premium Plinko:\n• Prefira as colunas centrais\n• Sessão curta com stop definido\n• Bet constante sem variação\n• Stop loss: 20% da banca",
    ],
    "scratch": [
        "💎 Estilo Premium Football Scratch:\n• Jogue em bet baixa e fixa\n• Máximo 5 raspadinhas por sessão\n• Não aumente a bet após perda\n• Se ganhar, pare — não reinvista tudo",
        "💎 Estilo Premium Football Scratch:\n• Sessão curta e controlada\n• Bet mínima para mais volume de jogadas\n• Stop win: dobrou a banca = encerra\n• Stop loss: 5 tentativas sem retorno",
    ],
    "coin_flip": [
        "💎 Estilo Premium Heads Tails:\n• Escolha sempre o mesmo lado por sessão\n• Bet fixa sem dobrar após perda\n• Máximo 8 rodadas por sessão\n• Stop loss: 5 derrotas seguidas = encerra",
        "💎 Estilo Premium Heads Tails:\n• Não troque de lado no meio da sessão\n• Gestão fixa sem martingale\n• Sessão disciplinada e curta\n• Lucro pequeno e consistente",
    ],
    "wheel": [
        "💎 Estilo Premium Lucky Wheel:\n• Aposte nos campos de menor multiplicador\n• Bet fixa e pequena\n• Máximo 10 giros por sessão\n• Não persiga o multiplicador máximo",
        "💎 Estilo Premium Lucky Wheel:\n• Foque nos campos com maior frequência\n• Bet constante sem variação\n• Sessão curta com meta definida\n• Stop loss: 30% da banca",
    ],
    "penalty": [
        "💎 Estilo Premium Penalty Shootout:\n• Escolha sempre o mesmo canto por sessão\n• Bet fixa sem progressão\n• Máximo 8 cobranças por sessão\n• Stop loss: 4 erros seguidos = pausa",
        "💎 Estilo Premium Penalty Shootout:\n• Não mude o canto no meio da sessão\n• Gestão disciplinada da banca\n• Sessão curta e objetiva\n• Encerre ao atingir a meta",
    ],
    "tower": [
        "💎 Estilo Premium Tower:\n• Suba no máximo 4 andares por rodada\n• Retire antes do 5º andar\n• Bet fixa e pequena\n• Pare ao perder 3 rodadas seguidas",
        "💎 Estilo Premium Tower:\n• Não force andares altos\n• Saída disciplinada no 3º ou 4º andar\n• Sessão curta com stop definido\n• Stop loss: 20% da banca",
    ],
}

CRASH_PROVIDERS = {"Spribe", "Original", "Betby", "Easybet", "1Bet", "Pateplay"}

# =========================================================
# DB
# =========================================================
def db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = False
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
    cur.execute("SELECT id FROM settings WHERE key = %s", (key,))
    if not cur.fetchone():
        cur.execute("INSERT INTO settings (key, value) VALUES (%s, %s)", (key, value))


def set_setting(key, value):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings (key, value) VALUES (%s, %s)
        ON CONFLICT(key) DO UPDATE SET value = EXCLUDED.value
    """, (key, value))
    conn.commit()
    cur.close()
    conn.close()


def get_setting(key, default=""):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = %s", (key,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["value"] if row else default


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            price TEXT NOT NULL,
            features TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            provider TEXT NOT NULL,
            rtp TEXT DEFAULT '',
            emoji TEXT DEFAULT '🎰',
            game_type TEXT DEFAULT 'slot',
            created_at TEXT NOT NULL,
            UNIQUE(name, provider)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_plan (
            id SERIAL PRIMARY KEY,
            plan_date TEXT NOT NULL,
            position INTEGER NOT NULL,
            game_id INTEGER NOT NULL,
            send_at TEXT NOT NULL,
            sent INTEGER DEFAULT 0,
            sent_at TEXT DEFAULT '',
            telegram_status TEXT DEFAULT '',
            telegram_response TEXT DEFAULT '',
            locked_at TEXT DEFAULT '',
            UNIQUE(plan_date, position)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent_log (
            id SERIAL PRIMARY KEY,
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
    seed_setting(cur, "send_interval_minutes", str(SEND_INTERVAL_MINUTES))
    seed_setting(cur, "max_late_minutes", str(MAX_LATE_MINUTES))
    seed_setting(cur, "scheduler_owner", "")
    seed_setting(cur, "scheduler_lease_until", "")

    cur.execute("SELECT id FROM users WHERE username = %s", (DEFAULT_ADMIN_USER,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (username, password, role, plan, brand_name, created_at)
            VALUES (%s, %s, 'admin', 'Premium', 'Rainha Games', %s)
        """, (DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASSWORD, now_br_str()))

    plans = [
        (
            "Free",
            "R$ 0,00",
            "Acesso a alguns sinais do dia|Estratégias padrão (simplificadas)|Acesso ao grupo|Sem prioridade nas entradas|Suporte exclusivo para VIP e Premium"
        ),
        (
            "VIP",
            "R$ 97,00",
            "Acesso completo aos sinais|Estratégias completas estilo premium|Prioridade nas entradas|Acesso ao grupo VIP|Método validado na prática"
        ),
        (
            "Premium",
            "R$ 297,00",
            "Tudo do VIP|Acesso antecipado aos sinais|Estratégias agressivas exclusivas|Suporte prioritário|White label e personalização total"
        ),
    ]
    for name, price, features in plans:
        cur.execute("SELECT id FROM plans WHERE name = %s", (name,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO plans (name, price, features, active)
                VALUES (%s, %s, %s, 1)
            """, (name, price, features))

    conn.commit()
    conn.close()
    seed_initial_games()


def infer_game_type(provider: str, name: str):
    n = name.lower()
    p = provider.lower()

    if "mines" in n:
        return "mines"
    if "aviator" in n:
        return "aviator"
    if "hilo" in n or "hi lo" in n:
        return "hilo"
    if "limbo" in n:
        return "limbo"
    if "plinko" in n:
        return "plinko"
    if "scratch" in n:
        return "scratch"
    if "heads tails" in n or "heads & tails" in n:
        return "coin_flip"
    if "lucky wheel" in n or "wheel" in n:
        return "wheel"
    if "penalty" in n:
        return "penalty"
    if "tower" in n:
        return "tower"
    if "dice" in n or "keno" in n or "goal" in n or "balloon" in n or "crash" in n or "rocket" in n:
        return "crash"
    if p in {x.lower() for x in CRASH_PROVIDERS}:
        return "crash"
    return "slot"


def add_game_if_missing(name: str, provider: str, rtp: str = "", emoji: str = "🎰"):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO games (name, provider, rtp, emoji, game_type, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT(name, provider) DO NOTHING
    """, (
        name.strip(),
        provider.strip(),
        (rtp or "").strip(),
        (emoji or "🎰").strip(),
        infer_game_type(provider, name),
        now_br_str()
    ))
    conn.commit()
    cur.close()
    conn.close()


def seed_initial_games():
    for provider, items in PROVIDER_GAMES.items():
        for name, rtp, emoji in items:
            add_game_if_missing(name, provider, rtp, emoji)

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
# LÓGICA DE MENSAGEM
# =========================================================
def stable_seed_for_day(day_str: str):
    digest = hashlib.sha256(day_str.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def choose_variant(items, plan_date: str, game_id: int, salt: str):
    raw = f"{plan_date}|{game_id}|{salt}"
    idx = int(hashlib.sha256(raw.encode("utf-8")).hexdigest(), 16) % len(items)
    return items[idx]


def choose_strategy_key(game_type: str, position: int):
    mapping = {
        "mines":     "mines",
        "crash":     "crash",
        "aviator":   "aviator",
        "hilo":      "hilo",
        "limbo":     "limbo",
        "plinko":    "plinko",
        "scratch":   "scratch",
        "coin_flip": "coin_flip",
        "wheel":     "wheel",
        "penalty":   "penalty",
        "tower":     "tower",
        "dice":      "dice",
    }
    if game_type in mapping:
        return mapping[game_type]
    modes = ["slots_leve", "slots_media", "slots_agressiva"]
    return modes[position % len(modes)]


def build_message_for_game(plan_date: str, position: int, game_row):
    intro = choose_variant(INTRO_VARIANTS, plan_date, game_row["id"], "intro")
    closing = choose_variant(CLOSING_VARIANTS, plan_date, game_row["id"], "closing")
    strategy_key = choose_strategy_key(game_row["game_type"], position)
    strategy_text = choose_variant(
        STRATEGY_VARIANTS[strategy_key],
        plan_date,
        game_row["id"],
        "strategy"
    )

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

def acquire_scheduler_leadership() -> bool:
    """
    Garante que apenas uma instância/processo fique responsável pelos envios.
    Funciona mesmo se houver mais de um worker/import da aplicação.
    """
    now_dt = now_br()
    lease_until = (now_dt + timedelta(seconds=SCHEDULER_LEASE_SECONDS)).strftime("%Y-%m-%d %H:%M:%S")
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    conn = db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT value FROM settings WHERE key = 'scheduler_owner'")
        owner_row = cur.fetchone()
        cur.execute("SELECT value FROM settings WHERE key = 'scheduler_lease_until'")
        lease_row = cur.fetchone()

        current_owner = owner_row["value"] if owner_row else ""
        current_lease = lease_row["value"] if lease_row else ""

        can_take = (
            not current_owner
            or not current_lease
            or current_lease <= now_str
            or current_owner == SCHEDULER_INSTANCE_ID
        )

        if can_take:
            cur.execute("UPDATE settings SET value = %s WHERE key = 'scheduler_owner'", (SCHEDULER_INSTANCE_ID,))
            cur.execute("UPDATE settings SET value = %s WHERE key = 'scheduler_lease_until'", (lease_until,))
            conn.commit()
            cur.close()
            conn.close()
            return True

        conn.rollback()
        cur.close()
        conn.close()
        return False
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            cur.close()
            conn.close()
        except Exception:
            pass
        return False


# =========================================================
# PLANEJAMENTO
# =========================================================
def get_interval_minutes():
    raw = get_setting("send_interval_minutes", str(SEND_INTERVAL_MINUTES)).strip()
    try:
        value = int(raw)
        return max(1, value)
    except Exception:
        return SEND_INTERVAL_MINUTES


def get_max_late_minutes():
    raw = get_setting("max_late_minutes", str(MAX_LATE_MINUTES)).strip()
    try:
        value = int(raw)
        return max(1, value)
    except Exception:
        return MAX_LATE_MINUTES


def get_day_window(day_str: str):
    start_time = get_setting("auto_start_time", AUTO_START_TIME)
    end_time = get_setting("auto_end_time", AUTO_END_TIME)

    day_obj = datetime.strptime(day_str, "%Y-%m-%d").date()
    sh, sm = parse_hhmm(start_time)
    eh, em = parse_hhmm(end_time)

    start_dt = datetime(day_obj.year, day_obj.month, day_obj.day, sh, sm, 0, tzinfo=APP_TZ)
    end_dt = datetime(day_obj.year, day_obj.month, day_obj.day, eh, em, 0, tzinfo=APP_TZ)

    if end_dt <= start_dt:
        end_dt = start_dt + timedelta(hours=24)

    return start_dt, end_dt


def build_send_slots_for_day(day_str: str):
    start_dt, end_dt = get_day_window(day_str)
    step = timedelta(minutes=get_interval_minutes())
    slots = []
    current = start_dt

    while current <= end_dt:
        slots.append(current)
        current += step

    return slots


def ensure_daily_plan(day_str: str):
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM daily_plan WHERE plan_date = %s", (day_str,))
    existing = cur.fetchone()["total"]

    if existing > 0:
        cur.close()
        conn.close()
        return

    cur.execute("SELECT * FROM games ORDER BY provider, name")
    games = cur.fetchall()

    if not games:
        cur.close()
        conn.close()
        return

    slots = build_send_slots_for_day(day_str)
    if not slots:
        cur.close()
        conn.close()
        return

    games_list = list(games)
    rng = random.Random(stable_seed_for_day(day_str))
    rng.shuffle(games_list)

    needed = len(slots)
    selected_games = []
    while len(selected_games) < needed:
        local = list(games_list)
        rng.shuffle(local)
        selected_games.extend(local)

    selected_games = selected_games[:needed]

    for position, game_row in enumerate(selected_games, start=1):
        send_at = slots[position - 1].strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            INSERT INTO daily_plan
            (plan_date, position, game_id, send_at, sent, sent_at, telegram_status, telegram_response, locked_at)
            VALUES (%s, %s, %s, %s, 0, '', '', '', '')
            ON CONFLICT(plan_date, position) DO NOTHING
        """, (day_str, position, game_row["id"], send_at))

    conn.commit()
    cur.close()
    conn.close()


def get_due_unsent_items(limit=1):
    day_str = today_str()
    ensure_daily_plan(day_str)

    now_dt = now_br()
    cutoff_dt = now_dt - timedelta(minutes=get_max_late_minutes())
    # Itens travados há mais que LOCK_TIMEOUT_SECONDS são considerados mortos (processo travou)
    lock_cutoff = (now_dt - timedelta(seconds=LOCK_TIMEOUT_SECONDS)).strftime("%Y-%m-%d %H:%M:%S")

    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT dp.*, g.name AS game_name, g.provider, g.rtp, g.emoji, g.game_type
        FROM daily_plan dp
        JOIN games g ON g.id = dp.game_id
        WHERE dp.plan_date = %s
          AND dp.sent = 0
          AND dp.send_at <= %s
          AND dp.send_at >= %s
          AND (dp.locked_at = '' OR dp.locked_at <= %s)
        ORDER BY dp.position ASC
        LIMIT %s
    """, (
        day_str,
        now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        cutoff_dt.strftime("%Y-%m-%d %H:%M:%S"),
        lock_cutoff,
        limit
    ))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def try_lock_item(item_id: int) -> bool:
    """
    Tenta travar o item atomicamente.
    NÃO marca como enviado aqui.
    Só trava o item para impedir duplicidade até o envio terminar.
    """
    now_dt = now_br()
    lock_cutoff = (now_dt - timedelta(seconds=LOCK_TIMEOUT_SECONDS)).strftime("%Y-%m-%d %H:%M:%S")
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    conn = db()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE daily_plan
            SET locked_at = %s
            WHERE id = %s
              AND sent = 0
              AND (locked_at = '' OR locked_at <= %s)
        """, (now_str, item_id, lock_cutoff))
        conn.commit()
        rowcount = cur.rowcount
        cur.close()
        conn.close()
        return rowcount == 1
    except Exception:
        try:
            conn.rollback()
            cur.close()
            conn.close()
        except Exception:
            pass
        return False


def finalize_send_log(plan_row, ok, response):
    sent_now = now_br_str()
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE daily_plan
        SET sent = %s,
            sent_at = %s,
            telegram_status = %s,
            telegram_response = %s,
            locked_at = ''
        WHERE id = %s
    """, (
        1 if ok else 0,
        sent_now if ok else '',
        "ok" if ok else "erro",
        (response or "")[:1000],
        plan_row["id"]
    ))

    cur.execute("""
        INSERT INTO sent_log
        (send_date, send_time, game_id, game_name, provider, sent_at, telegram_status, telegram_response)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        today_str(),
        datetime.strptime(plan_row["send_at"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M"),
        plan_row["game_id"],
        plan_row["game_name"],
        plan_row["provider"],
        sent_now,
        "ok" if ok else "erro",
        (response or "")[:1000]
    ))

    conn.commit()
    cur.close()
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
            # Só a instância líder pode montar agenda e enviar sinais
            if not acquire_scheduler_leadership():
                time.sleep(SCHEDULER_SLEEP_SECONDS)
                continue

            ensure_daily_plan(today_str())
            tomorrow = (today_date() + timedelta(days=1)).strftime("%Y-%m-%d")
            ensure_daily_plan(tomorrow)

            due_items = get_due_unsent_items(limit=1)
            hero_image_url = get_setting("hero_image_url", "").strip()

            for item in due_items:
                locked = try_lock_item(item["id"])
                if not locked:
                    continue

                msg = build_message_for_game(
                    plan_date=item["plan_date"],
                    position=item["position"],
                    game_row={
                        "id": item["game_id"],
                        "name": item["game_name"],
                        "provider": item["provider"],
                        "rtp": item["rtp"],
                        "emoji": item["emoji"],
                        "game_type": item["game_type"],
                    }
                )

                ok, response = telegram_send(msg, hero_image_url)
                finalize_send_log(item, ok, response)

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
    max-width:1400px;
    margin:0 auto;
    padding:24px;
}
.grid{
    display:grid;
    gap:18px;
}
.grid-2{
    grid-template-columns:1.1fr .9fr;
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
    min-height:140px;
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
.small{
    font-size:12px;
    color:#cfcfcf;
}
@media (max-width: 980px){
    .grid-2, .grid-3{
        grid-template-columns:1fr;
    }
}
</style>
<script>
// Auto-refresh do painel a cada 20 segundos via AJAX (só na página do painel)
(function(){
    function isDashboard(){
        return window.location.pathname === '/' || window.location.pathname === '';
    }
    if(!isDashboard()) return;

    function updateDashboard(){
        fetch('/api/dashboard-stats')
            .then(function(r){ return r.json(); })
            .then(function(d){
                // KPIs
                var els = {
                    'kpi-jogos': d.total_games,
                    'kpi-providers': d.total_providers,
                    'kpi-sent': d.sent_today,
                    'kpi-pending': d.pending_today,
                    'kpi-hora': d.hora_atual,
                    'kpi-first': d.first_time,
                    'kpi-last': d.last_time,
                    'kpi-last-game': d.last_game,
                    'kpi-last-time': d.last_send_time,
                    'kpi-last-status': d.last_status,
                };
                Object.keys(els).forEach(function(id){
                    var el = document.getElementById(id);
                    if(el && els[id] !== undefined) el.textContent = els[id];
                });

                // Preview próxima mensagem
                var prev = document.getElementById('preview-next');
                if(prev && d.preview) prev.textContent = d.preview;

                // Tabela de últimos envios
                var tbody = document.getElementById('tbody-logs');
                if(tbody && d.logs){
                    tbody.innerHTML = d.logs.map(function(row){
                        var badge = row.status === 'ok'
                            ? '<span class="badge badge-success">ok</span>'
                            : '<span class="badge badge-gold">' + (row.status || '-') + '</span>';
                        return '<tr><td>'+row.date+'</td><td>'+row.time+'</td><td>'+row.game+'</td><td>'+row.provider+'</td><td>'+badge+'</td></tr>';
                    }).join('');
                }

                // Indicador visual discreto
                var ind = document.getElementById('refresh-indicator');
                if(ind){
                    ind.style.opacity = '1';
                    setTimeout(function(){ ind.style.opacity = '0'; }, 800);
                }
            })
            .catch(function(){});
    }

    // Primeira atualização após 20s, depois repete
    setInterval(updateDashboard, 20000);
})();
</script>
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
                <a href="{{ url_for('admin_catalog') }}">Catálogo</a>
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
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM users
            WHERE username = %s AND password = %s AND is_active = 1
            LIMIT 1
        """, (username, password))
        user = cur.fetchone()
        cur.close()
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
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM games")
    total_games = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(DISTINCT provider) AS total FROM games")
    total_providers = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) AS total FROM daily_plan WHERE plan_date = %s AND telegram_status = 'ok'", (today_str(),))
    sent_today = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) AS total FROM daily_plan WHERE plan_date = %s AND sent = 0", (today_str(),))
    pending_today = cur.fetchone()["total"]
    cur.execute("SELECT send_at FROM daily_plan WHERE plan_date = %s ORDER BY position ASC LIMIT 1", (today_str(),))
    first_time = cur.fetchone()
    cur.execute("SELECT send_at FROM daily_plan WHERE plan_date = %s ORDER BY position DESC LIMIT 1", (today_str(),))
    last_time = cur.fetchone()
    cur.execute("SELECT * FROM sent_log ORDER BY id DESC LIMIT 1")
    last_log = cur.fetchone()
    cur.execute("""
        SELECT dp.*, g.name AS game_name, g.provider, g.rtp, g.emoji, g.game_type
        FROM daily_plan dp
        JOIN games g ON g.id = dp.game_id
        WHERE dp.plan_date = %s AND dp.sent = 0
        ORDER BY dp.position ASC
        LIMIT 1
    """, (today_str(),))
    next_item = cur.fetchone()
    cur.execute("SELECT * FROM sent_log ORDER BY id DESC LIMIT 12")
    recent_logs = cur.fetchall()
    cur.close()
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
                "game_type": next_item["game_type"],
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
    <div style="display:flex;justify-content:flex-end;align-items:center;margin-bottom:10px;gap:10px;">
        <span id="refresh-indicator" style="font-size:12px;color:#39d98a;opacity:0;transition:opacity .4s;">● atualizado</span>
        <span class="muted" style="font-size:12px;">⟳ Painel atualiza automaticamente a cada 20s</span>
    </div>

    <div class="grid grid-3">
        <div class="card">
            <div class="sub">Jogos no catálogo</div>
            <div class="kpi" id="kpi-jogos">{total_games}</div>
        </div>
        <div class="card">
            <div class="sub">Provedoras</div>
            <div class="kpi" id="kpi-providers">{total_providers}</div>
        </div>
        <div class="card">
            <div class="sub">Envios feitos hoje</div>
            <div class="kpi" id="kpi-sent">{sent_today}</div>
        </div>
    </div>

    <div class="grid grid-2" style="margin-top:18px;">
        <div class="card">
            <h2>Próxima mensagem automática</h2>
            <div class="preview" id="preview-next">{preview}</div>
            <div class="muted" style="margin-top:12px;">
                O botão "{get_setting("footer_text", DEFAULT_FOOTER_TEXT)}" é enviado automaticamente em todas as mensagens.
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Status do sistema</h3>
                <div class="sub">Horário atual Brasil</div>
                <div class="kpi" id="kpi-hora">{now_br().strftime("%H:%M:%S")}</div>

                <div class="sub" style="margin-top:12px;">Janela automática</div>
                <div class="preview">{get_setting("auto_start_time", AUTO_START_TIME)} até {get_setting("auto_end_time", AUTO_END_TIME)}</div>

                <div class="sub" style="margin-top:12px;">Intervalo entre envios</div>
                <div>{get_interval_minutes()} minutos</div>

                <div class="sub" style="margin-top:12px;">Tolerância máxima de atraso</div>
                <div>{get_max_late_minutes()} minutos</div>

                <div class="sub" style="margin-top:12px;">Primeiro horário de hoje</div>
                <div id="kpi-first">{first_time_text}</div>

                <div class="sub" style="margin-top:12px;">Último horário de hoje</div>
                <div id="kpi-last">{last_time_text}</div>

                <div class="sub" style="margin-top:12px;">Pendentes hoje</div>
                <div id="kpi-pending">{pending_today}</div>
            </div>

            <div class="card">
                <h3>Último envio</h3>
                <div class="sub">Jogo</div>
                <div id="kpi-last-game">{last_log["game_name"] if last_log else "Ainda não houve envio"}</div>

                <div class="sub" style="margin-top:10px;">Hora</div>
                <div id="kpi-last-time">{last_log["send_time"] if last_log else "-"}</div>

                <div class="sub" style="margin-top:10px;">Status</div>
                <div id="kpi-last-status">{last_log["telegram_status"] if last_log else "-"}</div>
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
                <tbody id="tbody-logs">{rows_html}</tbody>
            </table>
        </div>
    </div>
    """
    return render_page("Painel", html)


@app.route("/planos")
@require_admin
def sales_plans():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM plans WHERE active = 1 ORDER BY id ASC")
    rows = cur.fetchall()
    cur.close()
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
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "client").strip()
        plan = request.form.get("plan", "Free").strip()
        brand_name = request.form.get("brand_name", "Rainha Games").strip()

        if username and password:
            conn = db()
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO users (username, password, role, plan, brand_name, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (username, password, role, plan, brand_name, now_br_str()))
                conn.commit()
                flash("Usuário criado com sucesso.")
            except Exception as e:
                conn.rollback()
                flash(f"Erro ao criar usuário: {e}")
            finally:
                cur.close()
                conn.close()

        return redirect(url_for("admin_users"))

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id DESC")
    users = cur.fetchall()
    cur.close()
    conn.close()

    rows = ""
    for u in users:
        rows += f"""
        <tr>
            <td>{u['id']}</td>
            <td>{u['username']}</td>
            <td>{u['role']}</td>
            <td>{u['plan']}</td>
            <td>{"Ativo" if u['is_active'] else "Inativo"}</td>
        </tr>
        """

    html = f"""
    <div class="grid grid-2">
        <div class="card">
            <h2>Criar usuário</h2>
            <form method="post">
                <label>Usuário</label>
                <input name="username" required>

                <label>Senha</label>
                <input name="password" required>

                <label>Tipo</label>
                <select name="role">
                    <option value="client">Cliente</option>
                    <option value="admin">Admin</option>
                </select>

                <label>Plano</label>
                <select name="plan">
                    <option value="Free">Free</option>
                    <option value="VIP">VIP</option>
                    <option value="Premium">Premium</option>
                </select>

                <label>Marca</label>
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
                            <th>Tipo</th>
                            <th>Plano</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return render_page("Usuários", html)


@app.route("/admin/catalog", methods=["GET", "POST"])
@require_admin
def admin_catalog():
    if request.method == "POST":
        mode = request.form.get("mode", "").strip()

        if mode == "single":
            provider = request.form.get("provider", "").strip()
            name = request.form.get("name", "").strip()
            rtp = request.form.get("rtp", "").strip()
            emoji = request.form.get("emoji", "🎰").strip()
            if provider and name:
                add_game_if_missing(name, provider, rtp, emoji)
                flash("Jogo adicionado com sucesso.")
            else:
                flash("Preencha provedora e nome do jogo.")
            return redirect(url_for("admin_catalog"))

        if mode == "bulk":
            bulk_text = request.form.get("bulk_text", "").strip()
            added = 0

            for raw_line in bulk_text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue

                parts = [p.strip() for p in line.split("|")]
                provider = parts[0] if len(parts) > 0 else ""
                name = parts[1] if len(parts) > 1 else ""
                rtp = parts[2] if len(parts) > 2 else ""
                emoji = parts[3] if len(parts) > 3 else "🎰"

                if provider and name:
                    add_game_if_missing(name, provider, rtp, emoji)
                    added += 1

            flash(f"Importação concluída. Linhas processadas: {added}")
            return redirect(url_for("admin_catalog"))

    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT provider, COUNT(*) AS total
        FROM games
        GROUP BY provider
        ORDER BY total DESC, provider ASC
    """)
    provider_rows = cur.fetchall()
    cur.execute("SELECT * FROM games ORDER BY id DESC LIMIT 40")
    recent_games = cur.fetchall()
    cur.close()
    conn.close()

    provider_table = ""
    for row in provider_rows:
        provider_table += f"""
        <tr>
            <td>{row['provider']}</td>
            <td>{row['total']}</td>
        </tr>
        """

    recent_table = ""
    for row in recent_games:
        recent_table += f"""
        <tr>
            <td>{row['name']}</td>
            <td>{row['provider']}</td>
            <td>{row['rtp'] or "Verificado ✅"}</td>
            <td>{row['emoji']}</td>
            <td>{row['game_type']}</td>
        </tr>
        """

    html = f"""
    <div class="grid grid-2">
        <div class="card">
            <h2>Adicionar jogo manual</h2>
            <form method="post">
                <input type="hidden" name="mode" value="single">

                <label>Provedora</label>
                <input name="provider" placeholder="Ex.: PG Soft">

                <label>Nome do jogo</label>
                <input name="name" placeholder="Ex.: Fortune Tiger">

                <label>RTP (opcional)</label>
                <input name="rtp" placeholder="Ex.: 96.81%">

                <label>Emoji (opcional)</label>
                <input name="emoji" value="🎰">

                <button type="submit">Adicionar jogo</button>
            </form>
        </div>

        <div class="card">
            <h2>Importação em massa FULL PESADO</h2>
            <div class="small" style="margin-bottom:10px;">
                Formato por linha: <b>Provedora | Nome do jogo | RTP opcional | Emoji opcional</b>
            </div>
            <form method="post">
                <input type="hidden" name="mode" value="bulk">
                <textarea name="bulk_text" placeholder="PG Soft | Fortune Tiger | 96.81% | 🐯&#10;Pragmatic Play | Gates of Olympus | 96.50% | ⚡"></textarea>
                <button type="submit">Importar em massa</button>
            </form>
        </div>
    </div>

    <div class="grid grid-2" style="margin-top:18px;">
        <div class="card">
            <h2>Provedoras no catálogo</h2>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Provedora</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>{provider_table}</tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>Últimos jogos cadastrados</h2>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Jogo</th>
                            <th>Provedora</th>
                            <th>RTP</th>
                            <th>Emoji</th>
                            <th>Tipo</th>
                        </tr>
                    </thead>
                    <tbody>{recent_table}</tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return render_page("Catálogo", html)


@app.route("/admin/settings", methods=["GET", "POST"])
@require_admin
def admin_settings():
    if request.method == "POST":
        set_setting("brand_name", request.form.get("brand_name", "").strip() or "Rainha Games")
        set_setting("footer_text", request.form.get("footer_text", "").strip() or DEFAULT_FOOTER_TEXT)
        set_setting("footer_link", request.form.get("footer_link", "").strip() or DEFAULT_FOOTER_LINK)
        set_setting("hero_image_url", request.form.get("hero_image_url", "").strip())
        set_setting("theme_primary", request.form.get("theme_primary", "").strip() or "#B3001B")
        set_setting("theme_secondary", request.form.get("theme_secondary", "").strip() or "#D4AF37")
        set_setting("theme_dark", request.form.get("theme_dark", "").strip() or "#0B0B0F")

        interval = request.form.get("send_interval_minutes", "").strip()
        late = request.form.get("max_late_minutes", "").strip()
        start_time = request.form.get("auto_start_time", "").strip()
        end_time = request.form.get("auto_end_time", "").strip()

        if interval:
            set_setting("send_interval_minutes", interval)
        if late:
            set_setting("max_late_minutes", late)
        if start_time:
            set_setting("auto_start_time", start_time)
        if end_time:
            set_setting("auto_end_time", end_time)

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

            <label>Horário inicial automático</label>
            <input name="auto_start_time" value="{get_setting('auto_start_time', AUTO_START_TIME)}">

            <label>Horário final automático</label>
            <input name="auto_end_time" value="{get_setting('auto_end_time', AUTO_END_TIME)}">

            <label>Intervalo entre envios (minutos)</label>
            <input name="send_interval_minutes" value="{get_setting('send_interval_minutes', str(SEND_INTERVAL_MINUTES))}">

            <label>Tolerância máxima de atraso (minutos)</label>
            <input name="max_late_minutes" value="{get_setting('max_late_minutes', str(MAX_LATE_MINUTES))}">

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
    cur = conn.cursor()
    cur.execute("""
        SELECT dp.*, g.name AS game_name, g.provider, g.rtp, g.emoji, g.game_type
        FROM daily_plan dp
        JOIN games g ON g.id = dp.game_id
        WHERE dp.plan_date = %s AND dp.sent = 0
        ORDER BY dp.position ASC
        LIMIT 1
    """, (today_str(),))
    next_item = cur.fetchone()
    cur.close()
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
            "game_type": next_item["game_type"],
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
    cur = conn.cursor()
    cur.execute("DELETE FROM daily_plan WHERE plan_date = %s AND sent = 0", (today_str(),))
    conn.commit()
    cur.close()
    conn.close()

    ensure_daily_plan(today_str())
    flash("Agenda automática de hoje foi regerada.")
    return redirect(url_for("dashboard"))

# =========================================================
# API — DASHBOARD STATS (usado pelo auto-refresh AJAX)
# =========================================================
@app.route("/api/dashboard-stats")
@require_login
def api_dashboard_stats():
    from flask import jsonify
    ensure_daily_plan(today_str())

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM games")
    total_games = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(DISTINCT provider) AS total FROM games")
    total_providers = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) AS total FROM daily_plan WHERE plan_date = %s AND telegram_status = 'ok'", (today_str(),))
    sent_today = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) AS total FROM daily_plan WHERE plan_date = %s AND sent = 0", (today_str(),))
    pending_today = cur.fetchone()["total"]
    cur.execute("SELECT send_at FROM daily_plan WHERE plan_date = %s ORDER BY position ASC LIMIT 1", (today_str(),))
    first_time = cur.fetchone()
    cur.execute("SELECT send_at FROM daily_plan WHERE plan_date = %s ORDER BY position DESC LIMIT 1", (today_str(),))
    last_time = cur.fetchone()
    cur.execute("SELECT * FROM sent_log ORDER BY id DESC LIMIT 1")
    last_log = cur.fetchone()
    cur.execute("""
        SELECT dp.*, g.name AS game_name, g.provider, g.rtp, g.emoji, g.game_type
        FROM daily_plan dp
        JOIN games g ON g.id = dp.game_id
        WHERE dp.plan_date = %s AND dp.sent = 0
        ORDER BY dp.position ASC
        LIMIT 1
    """, (today_str(),))
    next_item = cur.fetchone()
    cur.execute("SELECT * FROM sent_log ORDER BY id DESC LIMIT 12")
    recent_logs = cur.fetchall()
    cur.close()
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
                "game_type": next_item["game_type"],
            }
        )

    first_time_text = datetime.strptime(first_time["send_at"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M") if first_time else "-"
    last_time_text = datetime.strptime(last_time["send_at"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M") if last_time else "-"

    logs_data = []
    for row in recent_logs:
        logs_data.append({
            "date": row["send_date"],
            "time": row["send_time"],
            "game": row["game_name"] or "-",
            "provider": row["provider"] or "-",
            "status": row["telegram_status"] or "-",
        })

    return jsonify({
        "total_games": total_games,
        "total_providers": total_providers,
        "sent_today": sent_today,
        "pending_today": pending_today,
        "hora_atual": now_br().strftime("%H:%M:%S"),
        "first_time": first_time_text,
        "last_time": last_time_text,
        "last_game": last_log["game_name"] if last_log else "Ainda não houve envio",
        "last_send_time": last_log["send_time"] if last_log else "-",
        "last_status": last_log["telegram_status"] if last_log else "-",
        "preview": preview,
        "logs": logs_data,
    })


# =========================================================
# START
# =========================================================
_scheduler_started = False


def start_scheduler():
    global _scheduler_started
    if _scheduler_started:
        return
    _scheduler_started = True
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()


init_db()
start_scheduler()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
