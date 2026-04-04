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

# Formato: "Nome do Jogo": ("emoji", "RTP ou None")
JOGOS = {
    # ── PG Soft ──────────────────────────────────────────
    "Fortune Tiger":                ("🐯",      "96.81%"),
    "Fortune Rabbit":               ("🐰",      "96.75%"),
    "Fortune Dragon":               ("🐉",      "96.74%"),
    "Fortune Mouse":                ("🐭",      "96.96%"),
    "Fortune Ox":                   ("🐂",      "96.80%"),
    "Fortune Horse":                ("🐴",      "96.81%"),
    "Fortune Snake":                ("🐍",      "96.75%"),
    "Mahjong Ways":                 ("🀄",      "96.95%"),
    "Mahjong Ways 2":               ("🀄✨",    "96.95%"),
    "Wild Bandito":                 ("🤠💥",    "96.75%"),
    "Treasures of Aztec":           ("🏺⚡",    "96.71%"),
    "Candy Bonanza":                ("🍬💥",    "96.75%"),
    "Leprechaun Riches":            ("🍀💛",    "97.35%"),
    "Dragon Hatch":                 ("🐉🥚",    "96.81%"),
    "Lucky Neko":                   ("🐱🍀",    "96.73%"),
    "Ganesha Gold":                 ("🐘💛",    "96.08%"),
    "Mafia Mayhem":                 ("🕵️💥",   "96.76%"),
    "Yakuza Honour":                ("⚔️🎌",    "96.80%"),
    "Dragon Tiger Luck":            ("🐉🐯",    "96.80%"),
    "The Great Icescape":           ("❄️🏔️",   "96.77%"),
    "Candy Burst":                  ("🍬⭐",    "96.95%"),
    "Mystic Potion":                ("🧪✨",    "96.71%"),
    "Muay Thai Champion":           ("🥊🏆",    "97.38%"),
    "Wild Bounty Showdown":         ("🤠🎯",    "96.74%"),
    "Bikini Paradise":              ("👙🌴",    "96.81%"),
    "Medusa II":                    ("🐍👑",    "96.95%"),
    "Werewolf's Hunt":              ("🐺🌕",    "96.71%"),
    "Flirting Scholar":             ("📜💕",    "97.44%"),
    "Ninja vs Samurai":             ("🥷⚔️",    "97.44%"),
    "Hip Hop Panda":                ("🐼🎤",    "95.75%"),
    "Tree of Fortune":              ("🌳🍀",    "96.75%"),
    "Three Monkeys":                ("🐒🐒🐒",  None),
    "Cocktail Nights":              ("🍹🌙",    "96.75%"),
    "Emperor's Favour":             ("👸🏛️",   None),
    "Tomb of Treasure":             ("⚱️💎",    None),
    "Prosperity Lion":              ("🦁💰",    None),
    "Safari Wilds":                 ("🦁🌿",    None),
    "Three Crazy Pigs":             ("🐷💥",    None),
    "Honey Trap of Diao Chan":      ("👸💝",    "96.96%"),
    "Grimms Bounty Hansel Gretel":  ("🧁🌲",    None),
    "Piggy Gold":                   ("🐷💛",    None),
    "Jungle Delight":               ("🌿🐒",    "96.03%"),
    "Bakery Bonanza":               ("🍰🎊",    None),
    "Battleground Royale":          ("⚔️🏆",    None),
    "Asgardian Rising":             ("⚡🛡️",   None),
    "Anubis Wrath":                 ("⚱️😤",   None),
    "Incan Wonders":                ("🏺🌄",    None),
    "Buffalo Win":                  ("🦬💰",    None),
    "Caishen Wins":                 ("🧧🪙",    None),
    "Win Win Won":                  ("🏆🥇",    None),
    "Chicky Run":                   ("🐥🏃",    None),
    "Cruise Royale":                ("🚢👑",    None),
    "Knockout Riches":              ("🥊💰",    None),
    "Galaxy Miner":                 ("🚀⛏️",   None),
    "Jack the Giant Hunter":        ("🪓👹",    None),
    "Chocolate Deluxe":             ("🍫✨",    None),
    "Graffiti Rush":                ("🎨💥",    None),
    "Geisha's Revenge":             ("👘⚔️",    None),
    "Alchemy Gold":                 ("⚗️💛",    None),
    "Rio Fantasia":                 ("🎭🌴",    None),
    "Bali Vacation":                ("🏝️🌺",   None),
    "Butterfly Blossom":            ("🦋🌸",    None),
    # ── Pragmatic Play ───────────────────────────────────
    "Gates of Olympus":             ("⚡👑",    "96.50%"),
    "Gates of Olympus 1000":        ("⚡🔥",    "96.50%"),
    "Gates of Heaven":              ("🌤️👑",   "96.50%"),
    "Sweet Bonanza":                ("🍬🎉",    "96.48%"),
    "Sugar Rush":                   ("🍭💥",    "96.50%"),
    "Sugar Rush 1000":              ("🍭⭐",    "96.50%"),
    "Starlight Princess":           ("⭐👸",    "96.50%"),
    "Big Bass Bonanza":             ("🐟🎣",    "96.71%"),
    "Bigger Bass Bonanza":          ("🐟💰",    "96.71%"),
    "Big Bass Bonanza 1000":        ("🐟🔥",    "96.71%"),
    "Big Bass Splash":              ("🐟🌊",    "96.71%"),
    "Big Bass Day at the Races":    ("🐟🏇",    "96.71%"),
    "The Dog House":                ("🐕🏠",    "96.51%"),
    "The Dog House Megaways":       ("🐕⚡",    "96.51%"),
    "Wild West Gold":               ("🤠🌵",    "96.51%"),
    "Joker's Jewels":               ("🃏💎",    "96.50%"),
    "Floating Dragon":              ("🐉🌊",    "96.81%"),
    "Floating Dragon Hold and Spin":("🐉💫",    "96.81%"),
    "Fruit Party":                  ("🍇🎉",    "96.47%"),
    "Fruit Party 2":                ("🍇✨",    "96.47%"),
    "Gems Bonanza":                 ("💎🎊",    "96.51%"),
    "Release the Kraken":           ("🦑⚡",    "96.52%"),
    "Release the Kraken Megaways":  ("🦑🌊",    "96.52%"),
    "Fortune of Olympus":           ("⚡💰",    "96.50%"),
    "Wolf Gold":                    ("🐺💰",    "96.01%"),
    "Buffalo King Megaways":        ("🦬👑",    "96.52%"),
    "Power of Thor Megaways":       ("⚡🔨",    "96.45%"),
    "Great Rhino Megaways":         ("🦏💥",    "96.58%"),
    "5 Lions Gold":                 ("🦁💛",    "96.47%"),
    "Fire Strike":                  ("🔥7️⃣",   "96.37%"),
    "Aztec Gems Deluxe":            ("💎🏺",    "96.52%"),
    "Spaceman":                     ("🚀👨‍🚀", "96.50%"),
    "Pirate Gold Deluxe":           ("🏴‍☠️💎", "96.48%"),
    "Emerald King":                 ("👑💚",    "96.50%"),
    "Cash Elevator":                ("💰🛗",    "96.50%"),
    "Book of Tut":                  ("📖👑",    "96.50%"),
    "Wild Wild Riches":             ("🤠💰",    "96.77%"),
    "Eye of Cleopatra":             ("👁️👸",   "96.50%"),
    "Candy Blitz Bombs":            ("🍬💣",    "96.47%"),
    "John Hunter Book of Tut":      ("🗺️📖",   "96.50%"),
    "Aztec King Megaways":          ("👑🏺",    "96.50%"),
    # ── Nolimit City ─────────────────────────────────────
    "Fire in the Hole 3":           ("💣🔥",    None),
    "San Quentin xWays":            ("🔒⚡",    None),
    "Tombstone RIP":                ("💀🪦",    None),
    "Deadwood xNudge":              ("🤠💀",    None),
    "Mental":                       ("🧠💥",    None),
    "Punk Rocker":                  ("🎸🤘",    None),
    "Book of Shadows":              ("📖🌑",    None),
    "Infectious 5 xWays":           ("🦠⚡",    None),
    "Folsom Prison":                ("🔒🏛️",   None),
    "Brute Force":                  ("💪💥",    None),
    # ── Red Tiger ────────────────────────────────────────
    "Dragon's Fire":                ("🐉🔥",    None),
    "Rainbow Jackpots":             ("🌈💰",    None),
    "Golden Leprechaun Megaways":   ("🍀💛",    None),
    "Primate King":                 ("🦍👑",    None),
    "Thor's Lightning":             ("⚡🔨",    None),
    "Pirates Plenty":               ("🏴‍☠️💎", None),
    "Mystery Reels Megaways":       ("🎰✨",    None),
    "Vault of Anubis":              ("⚱️👁️",   None),
    "God of Wealth":                ("🙏💰",    None),
    "Ali Baba's Luck":              ("🪔💎",    None),
    # ── Playtech ─────────────────────────────────────────
    "Age of the Gods":              ("⚡👑",    None),
    "Buffalo Blitz":                ("🦬💨",    None),
    "Gladiator":                    ("⚔️🏛️",   None),
    "Great Blue":                   ("🌊🐳",    None),
    "Heart of the Frontier":        ("🤠❤️",    None),
    "Kingdoms Rise":                ("⚔️🏰",    None),
    # ── Fa Chai ──────────────────────────────────────────
    "Circus Delight":               ("🎪🎠",    None),
    "Emoji Riches":                 ("😍💰",    None),
    "Wild Ape":                     ("🦍🌴",    None),
    "Charge Buffalo":               ("🦬⚡",    None),
    # ── JDB ──────────────────────────────────────────────
    "Book of Myth":                 ("📖🔮",    None),
    "Lucky Goldenfish":             ("🐟💛",    None),
    "Dragon Treasure":              ("🐉💎",    None),
    "Fishing War":                  ("🎣⚔️",    None),
    "Super Bonus Slot":             ("🎰💥",    None),
    # ── Belatra ──────────────────────────────────────────
    "Lucky Drink":                  ("🍹🍀",    None),
    "Piggy Bank":                   ("🐷💰",    None),
    "Cleo's Book":                  ("📖👸",    None),
    "Big Wild Buffalo":             ("🦬💥",    None),
    "Dragon's Bonanza":             ("🐉💎",    None),
    "Mummyland Treasures":          ("⚱️🏺",    None),
    # ── Spribe ───────────────────────────────────────────
    "Aviator":                      ("✈️💰",    "97.00%"),
    "Plinko":                       ("🎯💸",    None),
    "Mines":                        ("💣⚠️",    None),
    "Dice":                         ("🎲💰",    None),
    # ── TaDa Gaming ──────────────────────────────────────
    "Fishing God":                  ("🎣🙏",    None),
    "Dragon Legend":                ("🐉✨",    None),
    "Lucky Koi":                    ("🐠🍀",    None),
    "Golden Toad":                  ("🐸💛",    None),
    # ── BGaming ──────────────────────────────────────────
    "Wild Tiger":                   ("🐯⚡",    None),
    "Bonanza Billion":              ("💎💰",    None),
    "Fruit Million":                ("🍎🎰",    None),
    "Burning Chilli X":             ("🌶️🔥",   None),
    "Wild Clusters":                ("🍇✨",    None),
    # ── Hacksaw Gaming ───────────────────────────────────
    "Wanted Dead or a Wild":        ("🤠🔫",    None),
    "Stick Em":                     ("🎯💥",    None),
    "Chaos Crew":                   ("🦹💣",    None),
    "Cubes":                        ("🧊⚡",    None),
    "Pizza Pays":                   ("🍕💰",    None),
    # ── Microgaming ──────────────────────────────────────
    "Mega Moolah":                  ("🦁💰",    "88.12%"),
    "Thunderstruck II":             ("⚡🔨",    "96.65%"),
    "Immortal Romance":             ("🧛💕",    "96.86%"),
    "Break da Bank Again":          ("🏦💥",    "95.43%"),
    "Avalon II":                    ("⚔️🏰",    "97.00%"),
    "Mermaids Millions":            ("🧜💎",    "96.56%"),
    "Thunderstruck Wild Lightning": ("⚡🌩️",   "96.10%"),
    # ── Endorphina ───────────────────────────────────────
    "Book of Aztec":                ("📖🏺",    "96.00%"),
    "Twerk":                        ("💃🎵",    "96.00%"),
    "Satoshi's Secret":             ("💻🔐",    "96.00%"),
    "Fruitmania":                   ("🍓🎰",    None),
    "Vegas Nights":                 ("🌃🎲",    None),
    # ── Playson ──────────────────────────────────────────
    "Solar Queen":                  ("☀️👑",    None),
    "Book of Gold":                 ("📖💛",    None),
    "Burning Wins":                 ("🔥🏆",    None),
    "Pearl River":                  ("💧🐲",    None),
    "Legend of Cleopatra":          ("👸🏺",    None),
    # ── 3 Oaks Gaming ────────────────────────────────────
    "Hot Triple Sevens":            ("7️⃣🔥",   None),
    "Candy Boom":                   ("🍬💥",    None),
    "Gold Express":                 ("🚂💛",    None),
    "Mighty Kong":                  ("🦍💪",    None),
    "Book of Tattoo":               ("📖🎨",    None),
    # ── Outros ───────────────────────────────────────────
    "Devil Fire Twins":             ("😈🔥",    None),
    "Bone Fortune":                 ("💀🎰",    None),
    "Fortune Hook Boom":            ("🎣💥",    None),
    "Fortune Hook":                 ("🎣",      None),
    "Lucky Jaguar 500":             ("🐆",      None),
    "Money Pot":                    ("🍀💰",    None),
    "Pirate Queen 2":               ("🏴‍☠️👑", None),
    "Caribbean Queen":              ("🌊👑",    None),
    "Poseidon":                     ("🔱",      None),
    "Monkey Boom":                  ("🐒💥",    None),
    "Cybercats 500x":               ("🤖🐱",    None),
    "Hamsta":                       ("🐹",      None),
    "Athens Megaways":              ("🏛️",     None),
    "Bass Boss":                    ("🐟👑",    None),
    "Cake and Ice Cream":           ("🎂🍦",    None),
    "Clover Craze":                 ("🍀",      None),
    "God Hand":                     ("🙏⚡",    None),
    "Infinity Tower":               ("🗼♾️",    None),
    "Rise of the Mighty Gods":      ("⚡👑",    None),
    "Magic Ace":                    ("🃏✨",    None),
    "Mjolnir":                      ("⚡🔨",    None),
    "Prosperity Tiger":             ("🐯💰",    None),
    "Treasure Bowl":                ("🏺💎",    None),
    "Cash Mania":                   ("💵🎰",    None),
    "Doomsday Rampage":             ("💥🌋",    None),
    "Double Fortune":               ("🍀🍀",    None),
    "Fortune Ganesha":              ("🐘🙏",    None),
    "Inferno Mayhem":               ("🔥💀",    None),
    "Eternal Kiss":                 ("💋🌹",    None),
    "Electro Fiesta":               ("⚡🎉",    None),
    "Halloween Meow":               ("🎃🐱",    None),
    "Magic Scroll":                 ("📜✨",    None),
    "Futebol Fever":                ("⚽🔥",    None),
    "Joker Coins":                  ("🃏🪙",    None),
    "Cowboys":                      ("🤠🌵",    None),
    "Chihuahua":                    ("🐕",      None),
    "Elves Town":                   ("🧝🏘️",   None),
    "Bank Robbers":                 ("🏦🦹",    None),
    "Golden Genie":                 ("🧞💛",    None),
    "Poker Win":                    ("♠️💰",    None),
    "Racing King":                  ("🏎️🏆",   None),
    "White Tiger":                  ("🐯⬜",    None),
    "Golden Koi Rise":              ("🐟💛",    None),
    "Plinko UFO":                   ("🛸💰",    None),
    "Football Strike":              ("⚽🎯",    None),
    "Lucky Dragons":                ("🐉🍀",    None),
    "Fortune Fish":                 ("🐟💰",    None),
    "Golden Wheel":                 ("🎡💛",    None),
    "Tiger Boom":                   ("🐯💥",    None),
    "Phoenix Rise":                 ("🦅🔥",    None),
    "Wild Panda":                   ("🐼🌿",    None),
    "Gold Rush":                    ("⛏️💛",    None),
    "Ocean Dragon":                 ("🌊🐉",    None),
    "Buffalo Thunder":              ("🦬⚡",    None),
    "Aztec Temple":                 ("🏺🌿",    None),
    "Viking Glory":                 ("⚔️🛡️",   None),
    "Pirate's Revenge":             ("🏴‍☠️⚔️", None),
    "Viking's Revenge":             ("⚔️🔥",    None),
    "Dragon's Revenge":             ("🐉💢",    None),
    "Warrior's Revenge":            ("⚔️💪",    None),
    "Penalty Shootout":             ("⚽🥅",    None),
    "Lucky Coins":                  ("🪙🍀",    None),
    "Lucky Sevens":                 ("7️⃣✨",   None),
    "Wild West":                    ("🤠🌵",    None),
    "Lucky Wheel":                  ("🎡🍀",    None),
    "Space Catcher":                ("🚀🎯",    None),
    "Coin Flip":                    ("🪙🔄",    None),
    "Ocean Fortune":                ("🌊💰",    None),
    "Golden Fish":                  ("🐟💛",    None),
    "Lucky Charm":                  ("🍀✨",    None),
    "Fortune Bull":                 ("🐂💰",    None),
    "Dragon Palace":                ("🐉🏯",    None),
    "Tiger King":                   ("🐯👑",    None),
    "Ocean King":                   ("🌊👑",    None),
    "Lucky Dragon":                 ("🐉🍀",    None),
    "Caishen Riches":               ("🧧💰",    None),
    "Dragon Gold":                  ("🐉💛",    None),
    "Fortune Wheel":                ("🎡💰",    None),
    "Hi-Lo":                        ("🃏⬆️",    None),
    "Keno":                         ("🎯🔢",    None),
    "777 Strike":                   ("7️⃣🎰",   None),
    "Aztec Fire":                   ("🔥🏺",    None),
    "Cash Bonanza":                 ("💰🎊",    None),
    "Fire and Gold":                ("🔥💛",    None),
    "Lucky Piggy":                  ("🐷🍀",    None),
    "Alibaba's Cave":               ("🪔💰",    None),
    "Forbidden Alchemy":            ("⚗️🔮",    None),
}

LISTA_JOGOS = list(JOGOS.keys())
enviados = {}


def gerar_mensagem(nome_jogo):
    dados = JOGOS.get(nome_jogo, ("🎰", None))
    emoji, rtp = dados
    estrategia = random.choice(ESTRATEGIAS)
    cabecalho = random.choice(CABECALHOS)
    rodape = random.choice(RODAPES)
    separador = "═" * 22

    linha_rtp = f"📊 RTP: {rtp}\n" if rtp else ""

    return f"""{cabecalho}

🎮 {nome_jogo} {emoji}
{linha_rtp}
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
            <tr><th>Horário</th><th>Jogo</th><th>RTP</th><th>Status</th></tr>
            {% for item in escala %}
            <tr class="{{ 'proximo' if item.proximo else '' }}">
                <td>{{ item.horario }}</td>
                <td>{{ item.emoji }} {{ item.jogo }}</td>
                <td>{{ item.rtp if item.rtp else '—' }}</td>
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
        dados = JOGOS.get(jogo, ("🎰", None))
        escala.append({
            "horario": horario,
            "jogo": jogo,
            "emoji": dados[0],
            "rtp": dados[1],
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
