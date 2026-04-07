from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import sqlite3
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
DB_PATH = os.getenv("DB_PATH", "/tmp/rainha_games_auto.db")
TOKEN = os.getenv("TOKEN", "").strip()
CHAT_ID = os.getenv("CHAT_ID", "").strip()
DEFAULT_ADMIN_USER = os.getenv("ADMIN_USER", "admin").strip()
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123456").strip()
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

AUTO_START_TIME = "00:00"
AUTO_END_TIME = "23:59"
SEND_INTERVAL_MINUTES = 3
ALLOW_REPEAT_GAMES_SAME_DAY = True
SCHEDULER_SLEEP_SECONDS = 10

DEFAULT_FOOTER_LINK = "https://beacons.ai/rainhagames"
DEFAULT_FOOTER_TEXT = "👑 A RAINHA JOGA AQUI"

app = Flask(__name__)
app.secret_key = SECRET_KEY

# =========================================================
# CATÁLOGO COMPLETO
# formato: (nome, provedora, rtp_ou_None, emoji, grupo)
# grupos: slots | crash | turbo | classico | megaways | pesca | mesa | bingo | sport
# =========================================================
SEED_GAMES = [
    # ── PG SOFT ──────────────────────────────────────────────
    ("Fortune Tiger",               "PG Soft",    "96.81%", "🐯",   "slots"),
    ("Fortune Ox",                  "PG Soft",    "96.75%", "🐂",   "slots"),
    ("Fortune Rabbit",              "PG Soft",    "96.75%", "🐰",   "slots"),
    ("Fortune Mouse",               "PG Soft",    "96.72%", "🐭",   "slots"),
    ("Fortune Dragon",              "PG Soft",    "96.83%", "🐉",   "slots"),
    ("Fortune Snake",               "PG Soft",    "96.70%", "🐍",   "slots"),
    ("Fortune Horse",               "PG Soft",    "96.72%", "🐴",   "slots"),
    ("Fortune Gods",                "PG Soft",    "96.74%", "💰",   "slots"),
    ("Mahjong Ways",                "PG Soft",    "96.92%", "🀄",   "slots"),
    ("Mahjong Ways 2",              "PG Soft",    "96.95%", "🀄",   "slots"),
    ("Wild Bandito",                "PG Soft",    "97.00%", "🤠",   "slots"),
    ("Medusa",                      "PG Soft",    "96.58%", "🐍",   "slots"),
    ("Medusa II",                   "PG Soft",    "96.58%", "🐍",   "slots"),
    ("Ganesha Gold",                "PG Soft",    "96.49%", "🐘",   "slots"),
    ("Ganesha Fortune",             "PG Soft",    "96.71%", "🐘",   "slots"),
    ("Caishen Wins",                "PG Soft",    "96.92%", "💰",   "slots"),
    ("Dragon Hatch",                "PG Soft",    "96.83%", "🐉",   "slots"),
    ("Lucky Neko",                  "PG Soft",    "96.73%", "🐱",   "slots"),
    ("Mafia Mayhem",                "PG Soft",    "96.76%", "🕵️",  "slots"),
    ("Yakuza Honour",               "PG Soft",    "96.80%", "⚔️",   "slots"),
    ("Dragon Tiger Luck",           "PG Soft",    "96.80%", "🐉🐯", "slots"),
    ("Candy Burst",                 "PG Soft",    "96.95%", "🍬",   "slots"),
    ("Mystic Potion",               "PG Soft",    "96.71%", "🧪",   "slots"),
    ("Muay Thai Champion",          "PG Soft",    "97.38%", "🥊",   "slots"),
    ("Wild Bounty Showdown",        "PG Soft",    "96.74%", "🤠",   "slots"),
    ("Bikini Paradise",             "PG Soft",    "96.81%", "👙",   "slots"),
    ("Werewolf's Hunt",             "PG Soft",    "96.71%", "🐺",   "slots"),
    ("Flirting Scholar",            "PG Soft",    "97.44%", "📜",   "slots"),
    ("Ninja vs Samurai",            "PG Soft",    "97.44%", "🥷",   "slots"),
    ("Hip Hop Panda",               "PG Soft",    "95.75%", "🐼",   "slots"),
    ("Tree of Fortune",             "PG Soft",    "96.75%", "🌳",   "slots"),
    ("Cocktail Nights",             "PG Soft",    "96.75%", "🍹",   "slots"),
    ("Honey Trap of Diao Chan",     "PG Soft",    "96.96%", "👸",   "slots"),
    ("Jungle Delight",              "PG Soft",    "96.03%", "🌿",   "slots"),
    ("Bakery Bonanza",              "PG Soft",    None,     "🍰",   "slots"),
    ("Battleground Royale",         "PG Soft",    None,     "⚔️",   "slots"),
    ("Leprechaun Riches",           "PG Soft",    "97.35%", "🍀",   "slots"),
    ("Treasures of Aztec",          "PG Soft",    "96.71%", "🏺",   "slots"),
    ("Candy Bonanza",               "PG Soft",    "96.75%", "🍬",   "slots"),
    ("The Great Icescape",          "PG Soft",    "96.77%", "❄️",   "slots"),
    ("Prosperity Lion",             "PG Soft",    None,     "🦁",   "slots"),
    ("Safari Wilds",                "PG Soft",    None,     "🦁",   "slots"),
    ("Galaxy Miner",                "PG Soft",    None,     "🚀",   "slots"),
    ("Jack the Giant Hunter",       "PG Soft",    None,     "🪓",   "slots"),
    ("Asgardian Rising",            "PG Soft",    None,     "⚡",   "slots"),
    ("Buffalo Win",                 "PG Soft",    None,     "🦬",   "slots"),
    ("Cruise Royale",               "PG Soft",    None,     "🚢",   "slots"),
    ("Butterfly Blossom",           "PG Soft",    None,     "🦋",   "slots"),
    ("Win Win Won",                 "PG Soft",    None,     "🏆",   "slots"),
    ("Graffiti Rush",               "PG Soft",    None,     "🎨",   "slots"),
    ("Alchemy Gold",                "PG Soft",    None,     "⚗️",   "slots"),
    ("Rio Fantasia",                "PG Soft",    None,     "🎭",   "slots"),

    # ── PRAGMATIC PLAY ────────────────────────────────────────
    ("Gates of Olympus",            "Pragmatic",  "96.50%", "⚡",   "slots"),
    ("Gates of Olympus 1000",       "Pragmatic",  "96.50%", "⚡🔥", "slots"),
    ("Sweet Bonanza",               "Pragmatic",  "96.48%", "🍬",   "slots"),
    ("Sugar Rush",                  "Pragmatic",  "96.50%", "🍭",   "slots"),
    ("Sugar Rush 1000",             "Pragmatic",  "96.50%", "🍭⭐", "slots"),
    ("Starlight Princess",          "Pragmatic",  "96.50%", "⭐",   "slots"),
    ("Big Bass Bonanza",            "Pragmatic",  "96.71%", "🐟",   "slots"),
    ("Bigger Bass Bonanza",         "Pragmatic",  "96.71%", "🐟💰", "slots"),
    ("Big Bass Bonanza 1000",       "Pragmatic",  "96.71%", "🐟🔥", "slots"),
    ("Big Bass Splash",             "Pragmatic",  "96.71%", "🐟🌊", "slots"),
    ("Big Bass Day at the Races",   "Pragmatic",  "96.71%", "🐟🏇", "slots"),
    ("The Dog House",               "Pragmatic",  "96.51%", "🐕",   "slots"),
    ("The Dog House Megaways",      "Pragmatic",  "96.51%", "🐕⚡", "megaways"),
    ("Wild West Gold",              "Pragmatic",  "96.51%", "🤠",   "slots"),
    ("Joker's Jewels",              "Pragmatic",  "96.50%", "🃏",   "slots"),
    ("Floating Dragon",             "Pragmatic",  "96.81%", "🐉",   "slots"),
    ("Fruit Party",                 "Pragmatic",  "96.47%", "🍇",   "slots"),
    ("Fruit Party 2",               "Pragmatic",  "96.47%", "🍇✨", "slots"),
    ("Gems Bonanza",                "Pragmatic",  "96.51%", "💎",   "slots"),
    ("Release the Kraken",          "Pragmatic",  "96.52%", "🦑",   "slots"),
    ("Release the Kraken Megaways", "Pragmatic",  "96.52%", "🦑🌊", "megaways"),
    ("Fortune of Olympus",          "Pragmatic",  "96.50%", "⚡💰", "slots"),
    ("Wolf Gold",                   "Pragmatic",  "96.01%", "🐺",   "slots"),
    ("Fire Strike",                 "Pragmatic",  "96.37%", "🔥",   "slots"),
    ("Aztec Gems Deluxe",           "Pragmatic",  "96.52%", "💎",   "slots"),
    ("Pirate Gold Deluxe",          "Pragmatic",  "96.48%", "🏴‍☠️","slots"),
    ("Emerald King",                "Pragmatic",  "96.50%", "👑",   "slots"),
    ("Cash Elevator",               "Pragmatic",  "96.50%", "💰",   "slots"),
    ("Book of Tut",                 "Pragmatic",  "96.50%", "📖",   "slots"),
    ("Wild Wild Riches",            "Pragmatic",  "96.77%", "🤠",   "slots"),
    ("Eye of Cleopatra",            "Pragmatic",  "96.50%", "👁️",  "slots"),
    ("Candy Blitz Bombs",           "Pragmatic",  "96.47%", "🍬💣", "slots"),
    ("Buffalo King Megaways",       "Pragmatic",  "96.52%", "🦬",   "megaways"),
    ("Power of Thor Megaways",      "Pragmatic",  "96.45%", "⚡🔨", "megaways"),
    ("Great Rhino Megaways",        "Pragmatic",  "96.58%", "🦏",   "megaways"),
    ("Aztec King Megaways",         "Pragmatic",  "96.50%", "👑🏺", "megaways"),
    ("5 Lions Gold",                "Pragmatic",  "96.47%", "🦁",   "slots"),
    ("Spaceman",                    "Pragmatic",  "96.50%", "🚀",   "crash"),

    # ── FAT PANDA STUDIOS ────────────────────────────────────
    ("Lucky Tiger",                 "Fat Panda",  "96.50%", "🐯",   "slots"),
    ("Lucky Tiger 1000",            "Fat Panda",  "96.50%", "🐯🔥", "slots"),
    ("Lucky Mouse",                 "Fat Panda",  "96.57%", "🐭",   "slots"),
    ("Lucky Phoenix",               "Fat Panda",  "96.50%", "🦅",   "slots"),
    ("Lucky Dog",                   "Fat Panda",  "96.50%", "🐕",   "slots"),
    ("Lucky Ox",                    "Fat Panda",  "96.50%", "🐂",   "slots"),
    ("Lucky Monkey",                "Fat Panda",  "96.50%", "🐒",   "slots"),
    ("Lucky Dice",                  "Fat Panda",  "96.50%", "🎲",   "turbo"),
    ("Lucky Fortune Tree",          "Fat Panda",  "96.50%", "🌳",   "slots"),
    ("Starlight Wins",              "Fat Panda",  "96.50%", "⭐",   "slots"),
    ("Pig Farm",                    "Fat Panda",  "96.50%", "🐷",   "slots"),
    ("Emotiwins",                   "Fat Panda",  "96.50%", "😄",   "slots"),
    ("Jelly Candy",                 "Fat Panda",  "96.52%", "🍬",   "slots"),
    ("Plushie Wins",                "Fat Panda",  "96.50%", "🧸",   "slots"),
    ("Wealthy Frog",                "Fat Panda",  "96.50%", "🐸",   "slots"),
    ("Fortunes of Aztec",           "Fat Panda",  "96.50%", "🏺",   "slots"),
    ("Olympus Wins",                "Fat Panda",  "96.50%", "⚡",   "slots"),
    ("Master Gems",                 "Fat Panda",  "96.50%", "💎",   "slots"),
    ("777 Rush",                    "Fat Panda",  "96.50%", "7️⃣",  "classico"),
    ("Code of Cairo",               "Fat Panda",  "96.50%", "📜",   "slots"),
    ("Dino Drop",                   "Fat Panda",  "96.50%", "🦕",   "slots"),
    ("Mystic Wishes",               "Fat Panda",  "96.50%", "🔮",   "slots"),
    ("Happy Nets",                  "Fat Panda",  "96.50%", "🎣",   "pesca"),
    ("DJ Neko",                     "Fat Panda",  "96.50%", "🐱",   "slots"),
    ("Sweet Burst",                 "Fat Panda",  "96.50%", "🍭",   "slots"),

    # ── SPIRIT ───────────────────────────────────────────────
    ("Ace Wild",                    "Spirit",     None,     "🃏",   "slots"),
    ("Carnival Spirit",             "Spirit",     None,     "🎭",   "slots"),
    ("Coming Money",                "Spirit",     None,     "💰",   "slots"),
    ("Gems Fortune",                "Spirit",     None,     "💎",   "slots"),
    ("Gems Fortune 2",              "Spirit",     None,     "💎🎡", "slots"),
    ("God of Wealth Spirit",        "Spirit",     None,     "🙏",   "slots"),
    ("Ice Princess",                "Spirit",     None,     "❄️",   "slots"),
    ("Joker Spin",                  "Spirit",     None,     "🃏",   "slots"),
    ("Merry Christmas",             "Spirit",     None,     "🎅",   "slots"),
    ("Mouse Fortune",               "Spirit",     None,     "🐭",   "slots"),
    ("Ox Fortune",                  "Spirit",     None,     "🐂",   "slots"),
    ("Rabbit Fortune",              "Spirit",     None,     "🐰",   "slots"),
    ("Tiger Fortune",               "Spirit",     None,     "🐯",   "slots"),
    ("Wild Buffalo Spirit",         "Spirit",     None,     "🦬",   "slots"),
    ("Wild Lion",                   "Spirit",     None,     "🦁",   "slots"),
    ("Wrath of Olympus",            "Spirit",     None,     "⚡",   "slots"),

    # ── RECTANGLE GAMES ──────────────────────────────────────
    ("AFun Firecrackers Fortune",   "Rectangle",  None,     "🧨",   "slots"),
    ("Aquarius Fortune Wheel",      "Rectangle",  None,     "🌊🎡","slots"),
    ("Aztec's Mystery",             "Rectangle",  None,     "🏺",   "slots"),
    ("Battle Ship",                 "Rectangle",  None,     "⚓",   "slots"),
    ("Black Assassin",              "Rectangle",  None,     "🗡️",  "slots"),
    ("Capricorn's Orb of Fortune",  "Rectangle",  None,     "🐐",   "slots"),
    ("Chicken Uncrossable",         "Rectangle",  None,     "🐔",   "slots"),
    ("Disco Fever",                 "Rectangle",  None,     "🕺",   "slots"),
    ("Dragon Crash",                "Rectangle",  None,     "🐉",   "crash"),
    ("Eggy Pop",                    "Rectangle",  None,     "🥚",   "slots"),
    ("Farmageddon",                 "Rectangle",  None,     "🐄",   "slots"),
    ("Fiesta Blue",                 "Rectangle",  None,     "🎉💙", "slots"),
    ("Fiesta Green",                "Rectangle",  None,     "🎉💚", "slots"),
    ("Fiesta Magenta",              "Rectangle",  None,     "🎉💜", "slots"),
    ("Fiesta Red",                  "Rectangle",  None,     "🎉❤️","slots"),
    ("Firecrackers Fortune",        "Rectangle",  None,     "🧨💰","slots"),
    ("Firecrackers Fortune 100",    "Rectangle",  None,     "🧨💯","slots"),
    ("Fortune Pig",                 "Rectangle",  None,     "🐷",   "slots"),
    ("Gold Diggers",                "Rectangle",  None,     "⛏️",  "slots"),
    ("Golden Koi Trail",            "Rectangle",  None,     "🐟✨", "slots"),
    ("The Inmate Outcuss",          "Rectangle",  None,     "🔫",   "slots"),
    ("Iron Valor",                  "Rectangle",  None,     "⚔️",   "slots"),
    ("Lucky Caramelo",              "Rectangle",  None,     "🍬",   "slots"),
    ("Lucky Caramelo 1000",         "Rectangle",  None,     "🍬🔥","slots"),
    ("Lucky Duck",                  "Rectangle",  None,     "🦆",   "slots"),
    ("Lucky Fox",                   "Rectangle",  None,     "🦊",   "slots"),
    ("Lucky Panda",                 "Rectangle",  None,     "🐼",   "slots"),
    ("Lucky Snake",                 "Rectangle",  None,     "🐍",   "slots"),
    ("Lucky Turtle",                "Rectangle",  None,     "🐢",   "slots"),
    ("Magic Circus",                "Rectangle",  None,     "🎪",   "slots"),
    ("Money Mania",                 "Rectangle",  None,     "💵",   "slots"),
    ("Piggy Mines",                 "Rectangle",  None,     "🐷⛏️","turbo"),
    ("Pirate's Treasure Reel",      "Rectangle",  None,     "🏴‍☠️","slots"),
    ("Pisces Realm of Fortune",     "Rectangle",  None,     "🐟🌊","slots"),
    ("Prosperity Clash",            "Rectangle",  None,     "🐉⚔️","slots"),
    ("Prosperity Dragon",           "Rectangle",  None,     "🐉",   "slots"),
    ("Prosperity Dragon Golden Reel","Rectangle", None,     "🐉🌟","slots"),
    ("Prosperity Horse",            "Rectangle",  None,     "🐴",   "slots"),
    ("Prosperity Mouse",            "Rectangle",  None,     "🐭",   "slots"),
    ("Prosperity Ox",               "Rectangle",  None,     "🐂",   "slots"),
    ("Prosperity Rabbit",           "Rectangle",  None,     "🐰",   "slots"),
    ("Prosperity Tiger",            "Rectangle",  None,     "🐯",   "slots"),
    ("Realm of Thunder",            "Rectangle",  None,     "⚡",   "slots"),
    ("Rudolf's Gifts",              "Rectangle",  None,     "🦌",   "slots"),
    ("Semana Santa Treasures",      "Rectangle",  None,     "✝️",   "slots"),
    ("Shapes of Fortune",           "Rectangle",  None,     "🔷",   "slots"),
    ("Shapes of Fortune Xmas",      "Rectangle",  None,     "🔷🎄","slots"),
    ("Smash Fury",                  "Rectangle",  None,     "💪",   "slots"),
    ("Solar Pong",                  "Rectangle",  None,     "☀️",   "slots"),
    ("Swaggy Caramelo",             "Rectangle",  None,     "🦊🍬","slots"),
    ("Swaggy Caramelo Super Prize", "Rectangle",  None,     "🦊🏆","slots"),
    ("The Lone Fireball",           "Rectangle",  None,     "🔥",   "slots"),
    ("The Lucky Year",              "Rectangle",  None,     "🐍🎊","slots"),
    ("Tinkering Box",               "Rectangle",  None,     "🔧",   "slots"),
    ("Topfly Pirate's Treasure",    "Rectangle",  None,     "🏴‍☠️🪙","slots"),
    ("Treasures of Hades",          "Rectangle",  None,     "💀💎","slots"),
    ("Wheel of Wealth",             "Rectangle",  None,     "🎡",   "slots"),
    ("Year of the Golden Horse",    "Rectangle",  None,     "🐴🌟","slots"),

    # ── HACKSAW GAMING ────────────────────────────────────────
    ("Wanted Dead or a Wild",       "Hacksaw",    "96.38%", "🤠🔫","slots"),
    ("Stick Em",                    "Hacksaw",    "96.40%", "🎯",   "slots"),
    ("Chaos Crew",                  "Hacksaw",    "96.30%", "🦹",   "slots"),
    ("Cubes",                       "Hacksaw",    "96.38%", "🧊",   "slots"),
    ("Pizza Pays",                  "Hacksaw",    "96.30%", "🍕",   "slots"),
    ("The Bowery Boys",             "Hacksaw",    "96.41%", "🦹🏙️","slots"),
    ("Frutz",                       "Hacksaw",    "96.40%", "🍓",   "slots"),
    ("Aztec Twist",                 "Hacksaw",    "96.36%", "🏺",   "slots"),
    ("Joker Bombs",                 "Hacksaw",    "96.48%", "🃏💣","slots"),
    ("Cash Compass",                "Hacksaw",    "96.42%", "🧭",   "slots"),
    ("Densho",                      "Hacksaw",    "96.40%", "⛩️",  "slots"),
    ("RIP City",                    "Hacksaw",    "96.22%", "💀🏙️","slots"),
    ("Cubes 2",                     "Hacksaw",    "96.38%", "🧊💥","slots"),
    ("Hand of Anubis",              "Hacksaw",    "96.24%", "🐺⚖️","slots"),
    ("Eye of Medusa",               "Hacksaw",    "96.20%", "🐍👁️","slots"),
    ("Chaos Crew 2",                "Hacksaw",    "96.30%", "🦹💥","slots"),
    ("Chaos Crew 3",                "Hacksaw",    "96.30%", "🦹🔥","slots"),
    ("Beam Boys",                   "Hacksaw",    "96.30%", "😺⚡","slots"),
    ("Le Bandit",                   "Hacksaw",    "96.30%", "🎭",   "slots"),
    ("Donut Division",              "Hacksaw",    "96.30%", "🍩",   "slots"),
    ("2 Wild 2 Die",                "Hacksaw",    "96.30%", "🤠💥","slots"),
    ("Duel at Dawn",                "Hacksaw",    "96.30%", "🔫🌅","slots"),
    ("Bullets and Bounty",          "Hacksaw",    "96.30%", "🤠🎯","slots"),
    ("The Luxe",                    "Hacksaw",    "96.30%", "💎",   "slots"),
    ("Le Cowboy",                   "Hacksaw",    "96.28%", "🦝🤠","slots"),
    ("Marlin Masters",              "Hacksaw",    "96.28%", "🐟🎣","slots"),
    ("Fist of Destruction",         "Hacksaw",    "96.30%", "👊",   "slots"),
    ("Slayers Inc",                 "Hacksaw",    "96.30%", "⚔️",   "slots"),
    ("Benny the Beer",              "Hacksaw",    "96.30%", "🍺",   "slots"),
    ("Keep Em",                     "Hacksaw",    "96.27%", "🥫",   "slots"),
    ("King Carrot",                 "Hacksaw",    "96.30%", "🥕👑","slots"),
    ("Klowns",                      "Hacksaw",    "96.30%", "🤡",   "slots"),
    ("Hounds of Hell",              "Hacksaw",    "96.30%", "🐕🔥","slots"),
    ("Le Viking",                   "Hacksaw",    "96.30%", "⚔️🛡️","slots"),
    ("Wings of Horus",              "Hacksaw",    "96.30%", "🦅",   "slots"),
    ("Rise of Ymir",                "Hacksaw",    "96.30%", "🧊👹","slots"),
    ("Tiger Legends",               "Hacksaw",    "96.30%", "🐯⚔️","slots"),
    ("Le Zeus",                     "Hacksaw",    "96.30%", "⚡",   "slots"),

    # ── SPRIBE ───────────────────────────────────────────────
    ("Aviator",                     "Spribe",     "97.00%", "✈️",   "crash"),
    ("Balloon",                     "Spribe",     "97.00%", "🎈",   "crash"),
    ("Crash X",                     "Spribe",     "97.00%", "💥🚀","crash"),
    ("Trader",                      "Spribe",     "97.00%", "📈",   "crash"),
    ("Mines Spribe",                "Spribe",     "97.00%", "💣",   "turbo"),
    ("Plinko Spribe",               "Spribe",     "97.00%", "🎯",   "turbo"),
    ("Dice Spribe",                 "Spribe",     "97.00%", "🎲",   "turbo"),
    ("HiLo Spribe",                 "Spribe",     "97.00%", "🃏⬆️","turbo"),
    ("Goal Spribe",                 "Spribe",     "97.00%", "⚽",   "turbo"),
    ("Keno Spribe",                 "Spribe",     "97.00%", "🎯🔢","turbo"),
    ("Keno 80",                     "Spribe",     "97.00%", "🎱",   "turbo"),
    ("Mini Roulette Spribe",        "Spribe",     "97.00%", "🎡🔴","turbo"),
    ("HotLine Spribe",              "Spribe",     "97.00%", "🔥📞","turbo"),

    # ── TURBO GAMES ───────────────────────────────────────────
    ("Ball & Ball",                 "Turbo Games", None,    "⚽🏀","sport"),
    ("Bayraktar",                   "Turbo Games", None,    "✈️💥","crash"),
    ("Catanza",                     "Turbo Games", None,    "🐱🎰","crash"),
    ("Crash X Turbo",               "Turbo Games", None,    "🚀💥","crash"),
    ("Crash X Football",            "Turbo Games", None,    "⚽🚀","crash"),
    ("Dice Twice",                  "Turbo Games", None,    "🎲🎲","turbo"),
    ("Double Roll",                 "Turbo Games", None,    "🎡",   "crash"),
    ("Fruit Towers",                "Turbo Games", None,    "🍉🏗️","slots"),
    ("Fury Stairs",                 "Turbo Games", None,    "😤🪜","slots"),
    ("Hamsta",                      "Turbo Games", None,    "🐹",   "crash"),
    ("HiLo Turbo",                  "Turbo Games", None,    "🃏⬆️","turbo"),
    ("Javelin X",                   "Turbo Games", None,    "🏹💥","crash"),
    ("Limbo Rider",                 "Turbo Games", None,    "🚗🏁","crash"),
    ("Magic Keno",                  "Turbo Games", None,    "🎱✨","turbo"),
    ("Mines Turbo",                 "Turbo Games", None,    "💣",   "turbo"),
    ("Neko",                        "Turbo Games", None,    "🐱⚡","crash"),
    ("Panda Bao",                   "Turbo Games", None,    "🐼",   "crash"),
    ("Rings of Untamed",            "Turbo Games", None,    "💍⚡","crash"),
    ("Save the Princess",           "Turbo Games", None,    "👸🏰","slots"),
    ("Spin Strike",                 "Turbo Games", None,    "🏏💥","sport"),
    ("Towers",                      "Turbo Games", None,    "🏗️",  "slots"),
    ("Turbo Mines",                 "Turbo Games", None,    "💣🔥","turbo"),
    ("Turbo Plinko",                "Turbo Games", None,    "🎯💜","turbo"),
    ("Vortex",                      "Turbo Games", None,    "🌀🔥","crash"),
    ("Wicket Blast",                "Turbo Games", None,    "🏏💣","sport"),

    # ── SMARTGUYS ─────────────────────────────────────────────
    ("Capo Dei Capi",               "SmartGuys",  None,     "🎩🤵","slots"),
    ("Crypto Man",                  "SmartGuys",  None,     "💎🕵️","slots"),
    ("Cyber Cats",                  "SmartGuys",  None,     "🐱💻","slots"),
    ("CyberCats 500X",              "SmartGuys",  None,     "🐱⚡","slots"),
    ("Duck Treasure",               "SmartGuys",  None,     "🦆💰","slots"),
    ("Hot Cherry Boom",             "SmartGuys",  None,     "🍒💥","slots"),
    ("Monkey Boom",                 "SmartGuys",  None,     "🐒💥","slots"),
    ("OddX",                        "SmartGuys",  None,     "💣🎯","crash"),

    # ── TADA GAMING ───────────────────────────────────────────
    ("Crazy 777",                   "TaDa",       None,     "7️⃣",  "classico"),
    ("Crazy Hunter",                "TaDa",       None,     "🎯",   "slots"),
    ("Jackpot Joker",               "TaDa",       None,     "🃏",   "slots"),
    ("Devil Fire 2",                "TaDa",       None,     "😈🔥","slots"),
    ("Jackpot Fishing",             "TaDa",       None,     "🎣",   "pesca"),
    ("Devil Fire",                  "TaDa",       None,     "😈",   "slots"),
    ("Mega Fishing",                "TaDa",       None,     "🎣💰","pesca"),
    ("Fortune Gems 3",              "TaDa",       None,     "💎",   "slots"),
    ("3 Coin Treasures",            "TaDa",       None,     "🪙",   "slots"),
    ("Seven Seven Seven",           "TaDa",       None,     "7️⃣",  "classico"),
    ("Fortune Monkey",              "TaDa",       None,     "🐒",   "slots"),
    ("Fortune Gems 2",              "TaDa",       None,     "💎✨", "slots"),
    ("Andar Bahar",                 "TaDa",       None,     "🃏",   "mesa"),
    ("Egypt's Glow",                "TaDa",       None,     "🏺",   "slots"),
    ("European Roulette",           "TaDa",       None,     "🎡",   "mesa"),
    ("Bone Fortune",                "TaDa",       None,     "💀",   "slots"),
    ("Fortune Bingo",               "TaDa",       None,     "🎯",   "bingo"),
    ("Fortune Coins",               "TaDa",       None,     "🪙",   "slots"),
    ("Fortune Coins 2",             "TaDa",       None,     "🪙✨", "slots"),
    ("Fortune Garuda 500",          "TaDa",       None,     "🦅",   "slots"),
    ("10 Sparkling Crown",          "TaDa",       None,     "👑",   "slots"),
    ("100 Blazing Clover",          "TaDa",       None,     "🍀",   "slots"),
    ("Aztec Priestess",             "TaDa",       None,     "🏺",   "slots"),
    ("Crazy 777 2",                 "TaDa",       None,     "7️⃣✨","classico"),
    ("Crown of Fortune",            "TaDa",       None,     "👑",   "slots"),
    ("3 Coin Wild Horse",           "TaDa",       None,     "🐴🪙","slots"),
    ("3 Pot Dragons",               "TaDa",       None,     "🐉",   "slots"),
    ("Devil Fire Twins",            "TaDa",       None,     "😈😈","slots"),
    ("Diamond Party",               "TaDa",       None,     "💎🎉","slots"),
    ("Dice & Drop",                 "TaDa",       None,     "🎲",   "turbo"),
    ("Domino Go",                   "TaDa",       None,     "🁣",   "mesa"),
    ("Dragon & Tiger",              "TaDa",       None,     "🐉🐯","mesa"),
    ("Boxing King",                 "TaDa",       None,     "🥊",   "slots"),
    ("Bombing Fishing",             "TaDa",       None,     "💣🎣","pesca"),
    ("Mines TaDa",                  "TaDa",       None,     "💣⭐","turbo"),
    ("Dragon Fortune",              "TaDa",       None,     "🐉",   "slots"),
    ("Charge Buffalo",              "TaDa",       None,     "🦬⚡","slots"),
    ("Dragon Treasure",             "TaDa",       None,     "🐉💎","slots"),
    ("Golden Empire",               "TaDa",       None,     "👑🏺","slots"),
    ("3 Lucky Piggy",               "TaDa",       None,     "🐷",   "slots"),
    ("Plinko Empire",               "TaDa",       None,     "🎯",   "turbo"),
    ("Happy Fishing",               "TaDa",       None,     "🎣😊","pesca"),
    ("Boom Legend",                 "TaDa",       None,     "💥",   "slots"),
    ("Golden Joker",                "TaDa",       None,     "🃏💛","slots"),
    ("Fortune Tree",                "TaDa",       None,     "🌳",   "slots"),
    ("Super Ace",                   "TaDa",       None,     "🃏⭐","slots"),
    ("Charge Buffalo Ascent",       "TaDa",       None,     "🦬",   "slots"),
    ("Golden Bank",                 "TaDa",       None,     "🏦",   "slots"),
    ("Fa Fa Fa",                    "TaDa",       None,     "🀄",   "classico"),
    ("Dinosaur Tycoon",             "TaDa",       None,     "🦕",   "slots"),
    ("Secret Treasure",             "TaDa",       None,     "🗺️",  "slots"),
    ("Book of Gold TaDa",           "TaDa",       None,     "📖💛","slots"),
    ("Twin Wins",                   "TaDa",       None,     "🏆🏆","slots"),
    ("Ali Baba",                    "TaDa",       None,     "🪔",   "slots"),
    ("All-Star Fishing",            "TaDa",       None,     "🎣⭐","pesca"),
    ("Elf Bingo",                   "TaDa",       None,     "🧝",   "bingo"),
    ("Color Game",                  "TaDa",       None,     "🎨",   "slots"),
    ("Sweet Land",                  "TaDa",       None,     "🍬🌈","slots"),
    ("Plinko TaDa",                 "TaDa",       None,     "🎯",   "turbo"),
    ("Zeus TaDa",                   "TaDa",       None,     "⚡",   "slots"),
    ("Video Poker",                 "TaDa",       None,     "🃏",   "mesa"),
    ("Mines Gold",                  "TaDa",       None,     "💣💛","turbo"),
    ("Blackjack Lucky Ladies",      "TaDa",       None,     "♠️",   "mesa"),
    ("Chicken Dash",                "TaDa",       None,     "🐔",   "slots"),
    ("Chin Shi Huang",              "TaDa",       None,     "👑",   "slots"),
    ("Clover Coins 3x3",            "TaDa",       None,     "🍀",   "slots"),
    ("Clover Coins 4x4",            "TaDa",       None,     "🍀🍀","slots"),
    ("Clover Ladybug",              "TaDa",       None,     "🍀🐞","slots"),
    ("Lucky Jaguar 500",            "TaDa",       None,     "🐆",   "slots"),
    ("Lucky Macaw",                 "TaDa",       None,     "🦜",   "slots"),
    ("Lucky Roulette",              "TaDa",       None,     "🎡",   "mesa"),
    ("Lucky Tamarin",               "TaDa",       None,     "🐒",   "slots"),
    ("Ludo",                        "TaDa",       None,     "🎲",   "mesa"),
    ("Ludo Quick",                  "TaDa",       None,     "🎲⚡","mesa"),
    ("Magic Lamp TaDa",             "TaDa",       None,     "🪔",   "slots"),
    ("Magic Lamp Bingo",            "TaDa",       None,     "🪔🎯","bingo"),
    ("Mayan Empire",                "TaDa",       None,     "🏺",   "slots"),
    ("Medusa TaDa",                 "TaDa",       None,     "🐍",   "slots"),
    ("Mega Ace",                    "TaDa",       None,     "🃏⭐","slots"),
    ("3 Lucky Baozhu",              "TaDa",       None,     "🧧",   "slots"),
    ("Agent Ace",                   "TaDa",       None,     "🕵️",  "slots"),
    ("Bubble Beauty",               "TaDa",       None,     "🧜",   "slots"),
    ("Mines Grand",                 "TaDa",       None,     "💣👑","turbo"),
    ("Mini Flush",                  "TaDa",       None,     "🃏",   "mesa"),
    ("10 Sparkling Crown 2",        "TaDa",       None,     "👑✨","slots"),
    ("Money Coming 2",              "TaDa",       None,     "💰",   "slots"),
    ("Money Coming Expanded Bets",  "TaDa",       None,     "💰📈","slots"),
    ("Money Pot",                   "TaDa",       None,     "🍀💰","slots"),
    ("Money Pot Deluxe",            "TaDa",       None,     "🍀💎","slots"),
    ("NekoNeko",                    "TaDa",       None,     "🐱🐱","slots"),
    ("Night City",                  "TaDa",       None,     "🌃",   "slots"),
    ("Nightfall Hunting",           "TaDa",       None,     "🌙🎯","slots"),
    ("Number King",                 "TaDa",       None,     "🔢👑","slots"),
    ("Ocean Hunter",                "TaDa",       None,     "🦈",   "pesca"),
    ("Ocean King Jackpot",          "TaDa",       None,     "🌊👑","pesca"),
    ("Party Night",                 "TaDa",       None,     "🎉🌙","slots"),
    ("Party Star",                  "TaDa",       None,     "🌟🎉","slots"),
    ("Pearls of Bingo",             "TaDa",       None,     "🦪",   "bingo"),
    ("Penalty Kicks",               "TaDa",       None,     "⚽🥅","sport"),
    ("Pharaoh Treasure",            "TaDa",       None,     "🏺",   "slots"),
    ("Pirate Queen 2",              "TaDa",       None,     "🏴‍☠️","slots"),
    ("Caribbean Queen",             "TaDa",       None,     "🌊👸","slots"),
    ("Big Boss",                    "TaDa",       None,     "💪👑","slots"),
    ("Plinko of Mine",              "TaDa",       None,     "🎯💣","turbo"),
    ("Poker King",                  "TaDa",       None,     "♠️👑","mesa"),
    ("Poseidon TaDa",               "TaDa",       None,     "🔱",   "slots"),
    ("Potion Wizard",               "TaDa",       None,     "🧙",   "slots"),
    ("Rapid Gems 777",              "TaDa",       None,     "7️⃣💎","classico"),
    ("Rise of Egypt",               "TaDa",       None,     "🏺⬆️","slots"),
    ("Roma X",                      "TaDa",       None,     "⚔️🏛️","slots"),
    ("Royal Shooter",               "TaDa",       None,     "🎯👑","slots"),
    ("Shogun",                      "TaDa",       None,     "⚔️",   "slots"),
    ("Safari Mystery",              "TaDa",       None,     "🦁",   "slots"),
    ("Samba",                       "TaDa",       None,     "🎭",   "slots"),
    ("Bikini Lady",                 "TaDa",       None,     "👙",   "slots"),
    ("3 Witch's Lamp",              "TaDa",       None,     "🧙💡","slots"),
    ("Shanghai Beauty",             "TaDa",       None,     "👸",   "slots"),
    ("Sic Bo",                      "TaDa",       None,     "🎲",   "mesa"),
    ("Sin City",                    "TaDa",       None,     "🌃💰","slots"),
    ("Speed Baccarat",              "TaDa",       None,     "🃏",   "mesa"),
    ("Money Coming",                "TaDa",       None,     "💰⬆️","slots"),
    ("Fortune Gems",                "TaDa",       None,     "💎",   "slots"),
    ("Black Jack TaDa",             "TaDa",       None,     "♠️",   "mesa"),
    ("Super Bingo",                 "TaDa",       None,     "🎯",   "bingo"),
    ("Super Cockfight",             "TaDa",       None,     "🐓",   "sport"),
    ("Super Rich",                  "TaDa",       None,     "💰👑","slots"),
    ("Supernova",                   "TaDa",       None,     "🌟",   "slots"),
    ("Candyland Bingo",             "TaDa",       None,     "🍬",   "bingo"),
    ("Bounty Frenzy",               "TaDa",       None,     "🤠",   "slots"),
    ("The Pig House",               "TaDa",       None,     "🐷🏠","slots"),
    ("Thor X",                      "TaDa",       None,     "⚡🔨","slots"),
    ("Tigre da Sorte",              "TaDa",       None,     "🐯",   "slots"),
    ("Tower TaDa",                  "TaDa",       None,     "🏗️",  "slots"),
    ("Treasure Quest",              "TaDa",       None,     "🗺️💎","slots"),
    ("Trial of Phoenix",            "TaDa",       None,     "🦅🔥","slots"),
    ("Truco",                       "TaDa",       None,     "🃏🇧🇷","mesa"),
    ("Ultimate Texas Hold'em",      "TaDa",       None,     "♠️🤠","mesa"),
    ("Go Goal Bingo",               "TaDa",       None,     "⚽",   "bingo"),
    ("Go Rush",                     "TaDa",       None,     "🚀",   "crash"),
    ("Gold Rush TaDa",              "TaDa",       None,     "⛏️",  "slots"),
    ("7 Up 7 Down",                 "TaDa",       None,     "7️⃣",  "mesa"),
    ("Arena Fighter",               "TaDa",       None,     "⚔️",   "slots"),
    ("Golden Explorer",             "TaDa",       None,     "🗺️",  "slots"),
    ("Bingo Adventure",             "TaDa",       None,     "🎯",   "bingo"),
    ("Golden Land",                 "TaDa",       None,     "🌅💰","slots"),
    ("Golden Queen",                "TaDa",       None,     "👸",   "slots"),
    ("Golden Temple",               "TaDa",       None,     "🏛️",  "slots"),
    ("Golden Treasure",             "TaDa",       None,     "💰",   "slots"),
    ("HiLo TaDa",                   "TaDa",       None,     "🃏⬆️","turbo"),
    ("Baccarat TaDa",               "TaDa",       None,     "🃏",   "mesa"),
    ("Happy Fishing Lightning",     "TaDa",       None,     "🎣⚡","pesca"),
    ("Happy Taxi",                  "TaDa",       None,     "🚕",   "slots"),
    ("Jackpot Bingo",               "TaDa",       None,     "🎯💰","bingo"),
    ("3 Coin Treasures 2",          "TaDa",       None,     "🪙🪙","slots"),
    ("3 Coin Golden Ox",            "TaDa",       None,     "🐂🪙","slots"),
    ("Jackpot Joker Fever",         "TaDa",       None,     "🃏🔥","slots"),
    ("Jhandi Munda",                "TaDa",       None,     "🎲",   "mesa"),
    ("Jogo do Bicho",               "TaDa",       None,     "🐾",   "mesa"),
    ("Joker Coins TaDa",            "TaDa",       None,     "🃏🪙","slots"),
    ("Joker's Fortune",             "TaDa",       None,     "🃏💰","slots"),
    ("Jungle King TaDa",            "TaDa",       None,     "🦁👑","slots"),
    ("Keno TaDa",                   "TaDa",       None,     "🎯🔢","turbo"),
    ("Keno Bonus Number",           "TaDa",       None,     "🎱",   "turbo"),
    ("Keno Super Chance",           "TaDa",       None,     "🎱⭐","turbo"),
    ("King Arthur",                 "TaDa",       None,     "⚔️",   "slots"),
    ("Kung Fu Tiger",               "TaDa",       None,     "🐯🥋","slots"),
    ("Limbo TaDa",                  "TaDa",       None,     "🚀",   "crash"),
    ("Lucky Bingo",                 "TaDa",       None,     "🎯",   "bingo"),
    ("Lucky Coming",                "TaDa",       None,     "🍀",   "slots"),
    ("Lucky Doggy",                 "TaDa",       None,     "🐕",   "slots"),
    ("Lucky Goldbricks",            "TaDa",       None,     "💰",   "slots"),
    ("Lucky Jaguar",                "TaDa",       None,     "🐆",   "slots"),
    ("Lucky Jaguar 2",              "TaDa",       None,     "🐆✨","slots"),
    ("Fortune Gems 500",            "TaDa",       None,     "💎",   "slots"),
    ("Fortune Hook",                "TaDa",       None,     "🎣",   "pesca"),
    ("Fortune Hook Boom",           "TaDa",       None,     "🎣💥","pesca"),
    ("40 Sparkling Crown",          "TaDa",       None,     "👑",   "slots"),
    ("Fortune Roulette",            "TaDa",       None,     "🎡",   "mesa"),
    ("Bingo Empire",                "TaDa",       None,     "🎯👑","bingo"),
    ("Fortune Yuri 500",            "TaDa",       None,     "💰",   "slots"),
    ("Fortune Zombie Lightning",    "TaDa",       None,     "🧟⚡","slots"),
    ("Fortune King Jackpot",        "TaDa",       None,     "👑",   "slots"),
    ("Bingo Carnaval",              "TaDa",       None,     "🎭",   "bingo"),
    ("Frog Dash",                   "TaDa",       None,     "🐸",   "slots"),
    ("Fruity Wheel",                "TaDa",       None,     "🍎🎡","slots"),
    ("Coin Tree",                   "TaDa",       None,     "🌳🪙","slots"),
    ("Coin Infinity",               "TaDa",       None,     "🪙♾️","slots"),
    ("Coin of Lightning",           "TaDa",       None,     "🪙⚡","slots"),
    ("Candy Baby",                  "TaDa",       None,     "🍬",   "slots"),
    ("Color Prediction",            "TaDa",       None,     "🎨",   "turbo"),
    ("Crash Bonus",                 "TaDa",       None,     "💥",   "crash"),
    ("Crash Goal",                  "TaDa",       None,     "⚽💥","crash"),
    ("Crash Puck",                  "TaDa",       None,     "🏒💥","crash"),
    ("Crash Touchdown",             "TaDa",       None,     "🏈💥","crash"),
    ("3 Charge Buffalo",            "TaDa",       None,     "🦬",   "slots"),
    ("Crazy Hunter 2",              "TaDa",       None,     "🎯💥","slots"),
    ("20 Blazing Clover",           "TaDa",       None,     "🍀🔥","slots"),
    ("West Hunter Bingo",           "TaDa",       None,     "🤠🎯","bingo"),
    ("Wheel TaDa",                  "TaDa",       None,     "🎡",   "turbo"),
    ("Wild Ace",                    "TaDa",       None,     "🃏⚡","slots"),
    ("Wild Racer",                  "TaDa",       None,     "🏎️",  "slots"),
    ("Witches' Night",              "TaDa",       None,     "🧙🌙","slots"),
    ("World Cup",                   "TaDa",       None,     "⚽🌍","sport"),
    ("X7-Hot",                      "TaDa",       None,     "7️⃣🔥","classico"),
    ("Xi Yang Yang",                "TaDa",       None,     "🦁",   "slots"),
    ("Cash Coin",                   "TaDa",       None,     "🪙",   "slots"),
    ("iRich Bingo",                 "TaDa",       None,     "💰",   "bingo"),
    ("Cash Stack",                  "TaDa",       None,     "💵",   "slots"),
    ("Fortune Pig",                 "TaDa",       None,     "🐷",   "slots"),

    # ── NOLIMIT CITY ──────────────────────────────────────────
    ("Fire in the Hole 3",          "Nolimit",    None,     "💣🔥","slots"),
    ("San Quentin xWays",           "Nolimit",    None,     "🔒⚡","megaways"),
    ("Tombstone RIP",               "Nolimit",    None,     "💀",   "slots"),
    ("Deadwood xNudge",             "Nolimit",    None,     "🤠💀","slots"),
    ("Mental",                      "Nolimit",    None,     "🧠💥","slots"),
    ("Punk Rocker",                 "Nolimit",    None,     "🎸",   "slots"),
    ("Book of Shadows",             "Nolimit",    None,     "📖🌑","slots"),
    ("Infectious 5 xWays",          "Nolimit",    None,     "🦠",   "megaways"),
    ("Folsom Prison",               "Nolimit",    None,     "🔒",   "slots"),
    ("Brute Force",                 "Nolimit",    None,     "💪💥","slots"),

    # ── RED TIGER ─────────────────────────────────────────────
    ("Dragon's Fire",               "Red Tiger",  None,     "🐉🔥","slots"),
    ("Rainbow Jackpots",            "Red Tiger",  None,     "🌈💰","slots"),
    ("Golden Leprechaun Megaways",  "Red Tiger",  None,     "🍀",   "megaways"),
    ("Primate King",                "Red Tiger",  None,     "🦍👑","slots"),
    ("Thor's Lightning",            "Red Tiger",  None,     "⚡🔨","slots"),
    ("Pirates Plenty",              "Red Tiger",  None,     "🏴‍☠️","slots"),
    ("Mystery Reels Megaways",      "Red Tiger",  None,     "🎰✨","megaways"),
    ("Vault of Anubis",             "Red Tiger",  None,     "⚱️",  "slots"),
    ("God of Wealth",               "Red Tiger",  None,     "🙏💰","slots"),
    ("Ali Baba's Luck",             "Red Tiger",  None,     "🪔💎","slots"),

    # ── MICROGAMING ───────────────────────────────────────────
    ("Mega Moolah",                 "Microgaming","88.12%", "🦁",   "slots"),
    ("Thunderstruck II",            "Microgaming","96.65%", "⚡🔨","slots"),
    ("Immortal Romance",            "Microgaming","96.86%", "🧛",   "slots"),
    ("Break da Bank Again",         "Microgaming","95.43%", "🏦💥","slots"),
    ("Avalon II",                   "Microgaming","97.00%", "⚔️",   "slots"),
    ("Mermaids Millions",           "Microgaming","96.56%", "🧜",   "slots"),
    ("Thunderstruck Wild Lightning","Microgaming","96.10%", "⚡🌩️","slots"),
    ("Jurassic World",              "Microgaming",None,     "🦕",   "slots"),
    ("Agent Jane Blonde",           "Microgaming",None,     "🕵️",  "slots"),

    # ── BGAMING ───────────────────────────────────────────────
    ("Fire Lightning",              "BGaming",    "97.00%", "🔥⚡","slots"),
    ("Elvis Frog",                  "BGaming",    "96.80%", "🐸🎸","slots"),
    ("Fruit Million",               "BGaming",    "96.50%", "🍎",   "slots"),
    ("Burning Chilli X",            "BGaming",    "96.50%", "🌶️🔥","slots"),
    ("Wild Clusters",               "BGaming",    "96.50%", "🍇",   "slots"),
    ("Bonanza Billion",             "BGaming",    "96.50%", "💎",   "slots"),
    ("Lucky Lady's Clover",         "BGaming",    "97.00%", "🍀💋","slots"),

    # ── ENDORPHINA ────────────────────────────────────────────
    ("Book of Aztec",               "Endorphina", "96.00%", "📖🏺","classico"),
    ("Twerk",                       "Endorphina", "96.00%", "💃",   "slots"),
    ("Satoshi's Secret",            "Endorphina", "96.00%", "💻",   "slots"),
    ("Fruitmania",                  "Endorphina", None,     "🍓",   "classico"),
    ("Vegas Nights",                "Endorphina", None,     "🌃",   "slots"),

    # ── PLAYSON ───────────────────────────────────────────────
    ("Solar Queen",                 "Playson",    None,     "☀️",   "slots"),
    ("Book of Gold",                "Playson",    None,     "📖",   "classico"),
    ("Burning Wins",                "Playson",    None,     "🔥🏆","slots"),
    ("Pearl River",                 "Playson",    None,     "💧🐲","slots"),
    ("Legend of Cleopatra",         "Playson",    None,     "👸",   "slots"),

    # ── RUBY PLAY ─────────────────────────────────────────────
    ("777 Strike",                  "Ruby Play",  None,     "7️⃣",  "classico"),
    ("Aztec Fire",                  "Ruby Play",  None,     "🔥🏺","slots"),
    ("Cash Bonanza",                "Ruby Play",  None,     "💰",   "slots"),
    ("Fire and Gold",               "Ruby Play",  None,     "🔥💛","slots"),
    ("Lucky Piggy",                 "Ruby Play",  None,     "🐷",   "slots"),

    # ── 3 OAKS GAMING ────────────────────────────────────────
    ("Hot Triple Sevens",           "3 Oaks",     None,     "7️⃣🔥","classico"),
    ("Candy Boom",                  "3 Oaks",     None,     "🍬💥","slots"),
    ("Gold Express",                "3 Oaks",     None,     "🚂💛","slots"),
    ("Mighty Kong",                 "3 Oaks",     None,     "🦍",   "slots"),
    ("Book of Tattoo",              "3 Oaks",     None,     "📖🎨","slots"),

    # ── NOVOMATIC ─────────────────────────────────────────────
    ("Book of Ra",                  "Novomatic",  "95.10%", "📖☀️","classico"),
    ("Lucky Lady's Charm",          "Novomatic",  "95.13%", "🍀💋","classico"),
    ("Sizzling Hot",                "Novomatic",  "95.66%", "🔥🍒","classico"),
    ("Dolphin's Pearl",             "Novomatic",  "95.13%", "🐬",   "classico"),
    ("Lord of the Ocean",           "Novomatic",  "95.10%", "🔱🌊","classico"),
    ("Columbus Deluxe",             "Novomatic",  "95.02%", "⛵",   "classico"),
    ("Queen of Hearts",             "Novomatic",  "95.13%", "♥️",   "classico"),
    ("Faust",                       "Novomatic",  "95.36%", "😈",   "classico"),
    ("Ultra Hot Deluxe",            "Novomatic",  "95.18%", "🌡️",  "classico"),
    ("Golden Sevens",               "Novomatic",  "95.42%", "7️⃣💛","classico"),

    # ── BELATRA ───────────────────────────────────────────────
    ("Lucky Drink",                 "Belatra",    None,     "🍹",   "slots"),
    ("Piggy Bank Belatra",          "Belatra",    None,     "🐷",   "slots"),
    ("Cleo's Book",                 "Belatra",    None,     "📖",   "classico"),
    ("Mummyland Treasures",         "Belatra",    None,     "⚱️",  "slots"),
    ("Dragon's Bonanza",            "Belatra",    None,     "🐉",   "slots"),

    # ── PLAYTECH ──────────────────────────────────────────────
    ("Age of the Gods",             "Playtech",   None,     "⚡👑","slots"),
    ("Buffalo Blitz",               "Playtech",   None,     "🦬",   "slots"),
    ("Gladiator",                   "Playtech",   None,     "⚔️",   "slots"),
    ("Great Blue",                  "Playtech",   None,     "🌊🐳","slots"),
    ("Heart of the Frontier",       "Playtech",   None,     "🤠❤️","slots"),
    ("Kingdoms Rise",               "Playtech",   None,     "⚔️🏰","slots"),

    # ── FA CHAI ───────────────────────────────────────────────
    ("Circus Delight",              "Fa Chai",    None,     "🎪",   "slots"),
    ("Emoji Riches",                "Fa Chai",    None,     "😍",   "slots"),
    ("Wild Ape",                    "Fa Chai",    None,     "🦍",   "slots"),
    ("Charge Buffalo Fa Chai",      "Fa Chai",    None,     "🦬",   "slots"),

    # ── JDB ───────────────────────────────────────────────────
    ("Book of Myth",                "JDB",        None,     "📖🔮","slots"),
    ("Lucky Goldenfish",            "JDB",        None,     "🐟💛","pesca"),
    ("Fishing War",                 "JDB",        None,     "🎣⚔️","pesca"),
    ("Super Bonus Slot",            "JDB",        None,     "🎰",   "slots"),
]

# =========================================================
# ESTRATÉGIAS POR GRUPO
# =========================================================
ESTRATEGIAS = {
    "slots": [
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
Entre depois de 5 rodadas comuns sem destaque.

🎰 Execução:
➡️ 5 giros no normal com bet média
➡️ 5 giros no turbo
➡️ Aumente a bet em 1 nível
➡️ Faça mais 15 giros no automático

🛑 Encerramento:
Bateu lucro, encerre sem insistir.""",

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
    ],

    "crash": [
        """💎 ESTILO PREMIUM — CONSERVADOR

🎯 Entrada:
Entre com 2% a 3% da banca por rodada.

📋 Execução:
➡️ Defina sua saída ANTES de entrar: 1.5x ou 2x
➡️ Configure o auto cashout no valor escolhido
➡️ Não mude a saída depois que a rodada começar
➡️ Se perder 3 seguidas → pausa obrigatória de 5 min

🛑 Saída:
Nunca espere multiplicadores altos por impulso.
Stop loss: 15% da banca.""",

        """💎 ESTILO PREMIUM — MÉDIA

🎯 Entrada:
Entre com 3% a 5% da banca por rodada.

📋 Execução:
➡️ Divida a aposta em 2 partes
➡️ Primeira saída: 1.5x garantido
➡️ Segunda saída: alvo em 3x
➡️ Se a segunda parte perder, não dobra na próxima

🛑 Saída:
Primeira saída garante lucro parcial sempre.
Stop loss: 20% da banca.""",

        """💎 ESTILO PREMIUM — AGRESSIVA

🎯 Entrada:
Entre com 2% da banca. Aumente só após 3 vitórias seguidas.

📋 Execução:
➡️ Alvo mínimo: 2x por rodada
➡️ Após 3 vitórias seguidas, suba a aposta 1 nível
➡️ Após qualquer derrota, volte para o valor inicial
➡️ Máximo de 5x como alvo de saída

🛑 Saída:
Nunca segure além de 5x por impulso.
Stop loss: 20% da banca.""",
    ],

    "turbo": [
        """💎 ESTILO PREMIUM — CONSERVADOR

🎯 Entrada:
Aposte 2% da banca. Configure risco BAIXO.

📋 Mines:
➡️ Configure 3 minas no campo
➡️ Abra no máximo 5 estrelas por rodada
➡️ Saia após a 4ª ou 5ª revelação sem hesitar

📋 Plinko:
➡️ Risco: BAIXO | 10 bolas por sessão

📋 Keno:
➡️ Escolha 5-6 números por rodada
➡️ Pare após 3 rodadas sem acerto

🛑 Stop loss: 15% | Stop gain: 25%""",

        """💎 ESTILO PREMIUM — MÉDIA

🎯 Entrada:
Aposte 3% da banca. Configure risco MÉDIO.

📋 Mines:
➡️ Configure 5 minas no campo
➡️ Abra no máximo 4 estrelas
➡️ Saia se multiplicador acima de 2x após a 3ª

📋 Plinko:
➡️ Risco: MÉDIO | 8 bolas por sessão

📋 Keno:
➡️ Escolha 8 números por rodada
➡️ Dobre após 2 rodadas sem acerto

🛑 Stop loss: 20% | Stop gain: 30%""",

        """💎 ESTILO PREMIUM — AGRESSIVA

🎯 Entrada:
Aposte 2% da banca. Configure risco ALTO.

📋 Mines:
➡️ Configure 10 minas no campo
➡️ Abra no máximo 3 estrelas
➡️ Saia imediatamente após 2ª revelação acima de 3x

📋 Plinko:
➡️ Risco: ALTO | Máximo 5 bolas por sessão

📋 Keno:
➡️ Escolha 10 números
➡️ Pare ao primeiro acerto alto

🛑 Stop loss: 15% | Stop gain: 40%""",
    ],

    "classico": [
        """💎 ESTILO PREMIUM — CONSERVADOR

🎯 Entrada:
Aposte valor fixo baixo. Não use a função gamble.

📋 Execução:
➡️ 10 rodadas observando o comportamento do jogo
➡️ Se não sair bônus em 15 rodadas, suba 1 nível de bet
➡️ Ao acionar os giros grátis, não interrompa a sequência
➡️ Após o bônus, volte para o bet inicial imediatamente

🛑 Saída:
Nunca use a função gamble para dobrar.
Stop loss: 20% | Stop gain: 30%""",

        """💎 ESTILO PREMIUM — MÉDIA

🎯 Entrada:
Aposte valor médio fixo por rodada.

📋 Execução:
➡️ 15 rodadas no bet atual
➡️ Se o bônus não aparecer, suba 1 nível de bet
➡️ Máximo de 2 aumentos de bet por sessão
➡️ Ao ganhar giros grátis, mantenha o bet atual

🛑 Saída:
Stop loss: 20% | Stop gain: 35%""",

        """💎 ESTILO PREMIUM — AGRESSIVA

🎯 Entrada:
Inicie com bet médio-alto.

📋 Execução:
➡️ 10 rodadas iniciais no bet escolhido
➡️ Se não acionar bônus, suba 2 níveis de bet
➡️ Máximo de 3 aumentos de bet por sessão
➡️ Ao ganhar giros grátis, mantenha o bet mais alto

🛑 Saída:
Stop loss: 25% | Stop gain: 40%""",
    ],

    "megaways": [
        """💎 ESTILO PREMIUM — CONSERVADOR

🎯 Entrada:
Bet baixo fixo. Megaways têm alta volatilidade.

📋 Execução:
➡️ 20 rodadas observando frequência de cascatas
➡️ Se não houver cascatas em 15 rodadas, suba 1 nível
➡️ Ao acionar free spins, não interrompa
➡️ Volte ao bet inicial após cada bônus

🛑 Saída:
Stop loss: 20% | Stop gain: 30%""",

        """💎 ESTILO PREMIUM — MÉDIA

🎯 Entrada:
Bet médio. Foque nas cascatas da base.

📋 Execução:
➡️ 15 rodadas no bet atual
➡️ Aguarde sequência de cascatas antes de aumentar
➡️ Suba 1 nível após 10 rodadas sem bônus
➡️ Máximo 2 aumentos de bet por sessão

🛑 Saída:
Stop loss: 20% | Stop gain: 35%""",

        """💎 ESTILO PREMIUM — AGRESSIVA

🎯 Entrada:
Bet médio-alto. Alta volatilidade exige banca sólida.

📋 Execução:
➡️ 10 rodadas iniciais
➡️ Suba bet após 8 rodadas sem cascata
➡️ Máximo 3 aumentos por sessão
➡️ Ao acionar bônus Megaways, não reduza o bet

🛑 Saída:
Stop loss: 25% | Stop gain: 40%""",
    ],

    "pesca": [
        """💎 ESTILO PREMIUM — CONSERVADOR

🎯 Entrada:
Bet baixo. Mire nos peixes médios.

📋 Execução:
➡️ Não desperdice tiros em peixes pequenos
➡️ Foque nos peixes de valor médio
➡️ Evite o chefe/boss até acumular munição
➡️ Máximo 30 tiros por sessão

🛑 Saída:
Stop loss: 20% | Stop gain: 30%""",

        """💎 ESTILO PREMIUM — MÉDIA

🎯 Entrada:
Bet médio. Equilibre peixes médios e grandes.

📋 Execução:
➡️ 60% dos tiros em peixes médios
➡️ 30% em peixes grandes
➡️ 10% reservado para o chefe/boss
➡️ Ao aparecer o chefe, concentre os tiros

🛑 Saída:
Stop loss: 20% | Stop gain: 35%""",

        """💎 ESTILO PREMIUM — AGRESSIVA

🎯 Entrada:
Bet alto. Foco total no chefe/boss.

📋 Execução:
➡️ Ignore peixes pequenos completamente
➡️ Atire apenas em peixes grandes e no chefe
➡️ Concentre rajada de tiros no chefe ao aparecer
➡️ Após derrotar o chefe, reduza o bet e avalie

🛑 Saída:
Stop loss: 20% | Stop gain: 50%""",
    ],

    "mesa": [
        """💎 ESTILO PREMIUM — CONSERVADOR

🎯 Entrada:
Aposte o mínimo da mesa. Gerencie o bankroll.

📋 Execução:
➡️ Mantenha apostas fixas por 10 rodadas
➡️ Não dobre após perda seguida
➡️ Pare com 3 perdas consecutivas
➡️ Volte apenas após 5 minutos de pausa

🛑 Saída:
Stop loss: 15% | Stop gain: 20%""",

        """💎 ESTILO PREMIUM — MÉDIA

🎯 Entrada:
Aposte valor médio. Controle as emoções.

📋 Execução:
➡️ Aposte fixo por 8 rodadas
➡️ Após 2 perdas seguidas, reduza a bet
➡️ Após 3 vitórias, pode subir 1 nível
➡️ Encerre ao atingir a meta diária

🛑 Saída:
Stop loss: 20% | Stop gain: 30%""",
    ],

    "bingo": [
        """💎 ESTILO PREMIUM — LEVE

🎯 Entrada:
Compre o mínimo de cartelas por rodada.

📋 Execução:
➡️ Compre 1-2 cartelas por rodada
➡️ Observe 3 rodadas antes de entrar
➡️ Prefira rodadas com menos jogadores
➡️ Pare após 10 rodadas sem bingo

🛑 Saída:
Stop loss: 20% | Stop gain: 25%""",

        """💎 ESTILO PREMIUM — MÉDIA

🎯 Entrada:
Compre 3-4 cartelas por rodada.

📋 Execução:
➡️ Entre em rodadas com jackpot disponível
➡️ Mantenha o número de cartelas fixo
➡️ Reinvista apenas 50% dos ganhos
➡️ Encerre após alcançar a meta

🛑 Saída:
Stop loss: 20% | Stop gain: 35%""",
    ],

    "sport": [
        """💎 ESTILO PREMIUM — CONSERVADOR

🎯 Entrada:
Aposte valor fixo baixo por rodada.

📋 Execução:
➡️ Observe 2 rodadas antes de entrar
➡️ Mantenha o mesmo valor por 5 rodadas
➡️ Não dobre após erro
➡️ Pare com 4 erros consecutivos

🛑 Saída:
Stop loss: 15% | Stop gain: 25%""",

        """💎 ESTILO PREMIUM — AGRESSIVA

🎯 Entrada:
Aposte valor médio. Foco na sequência.

📋 Execução:
➡️ Entre com confiança após 3 acertos seguidos
➡️ Suba a bet gradualmente nas vitórias
➡️ Reset imediato após qualquer erro
➡️ Meta de 5 acertos por sessão

🛑 Saída:
Stop loss: 20% | Stop gain: 40%""",
    ],
}

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

# =========================================================
# BANCO DE DADOS
# =========================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            provider TEXT NOT NULL,
            rtp TEXT,
            emoji TEXT DEFAULT '🎰',
            game_group TEXT DEFAULT 'slots',
            active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS daily_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_date TEXT NOT NULL,
            game_id INTEGER NOT NULL,
            send_at TEXT NOT NULL,
            sent INTEGER DEFAULT 0,
            sent_at TEXT,
            FOREIGN KEY (game_id) REFERENCES games(id)
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)

    # Admin padrão
    pwd_hash = hashlib.sha256(DEFAULT_ADMIN_PASSWORD.encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash, is_admin) VALUES (?,?,1)",
              (DEFAULT_ADMIN_USER, pwd_hash))

    # Seed dos jogos
    existing = c.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    if existing == 0:
        for name, provider, rtp, emoji, group in SEED_GAMES:
            c.execute("INSERT INTO games (name, provider, rtp, emoji, game_group) VALUES (?,?,?,?,?)",
                      (name, provider, rtp, emoji, group))

    # Settings padrão
    defaults = {
        "footer_link": DEFAULT_FOOTER_LINK,
        "footer_text": DEFAULT_FOOTER_TEXT,
        "send_interval": str(SEND_INTERVAL_MINUTES),
        "start_time": AUTO_START_TIME,
        "end_time": AUTO_END_TIME,
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?,?)", (k, v))

    conn.commit()
    conn.close()

def get_setting(key, default=""):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

# =========================================================
# GERAÇÃO DE AGENDA
# =========================================================
def build_daily_plan(plan_date_str=None):
    tz = APP_TZ
    if plan_date_str is None:
        plan_date_str = datetime.now(tz).strftime("%Y-%m-%d")

    conn = get_db()
    existing = conn.execute(
        "SELECT COUNT(*) FROM daily_plan WHERE plan_date=?", (plan_date_str,)
    ).fetchone()[0]

    if existing > 0:
        conn.close()
        return

    games = conn.execute(
        "SELECT id FROM games WHERE active=1 ORDER BY RANDOM()"
    ).fetchall()
    game_ids = [g["id"] for g in games]

    if not game_ids:
        conn.close()
        return

    start_h, start_m = map(int, AUTO_START_TIME.split(":"))
    end_h, end_m = map(int, AUTO_END_TIME.split(":"))
    interval = int(get_setting("send_interval", str(SEND_INTERVAL_MINUTES)))

    start_total = start_h * 60 + start_m
    end_total = end_h * 60 + end_m
    minutes_available = end_total - start_total

    slots_available = minutes_available // interval
    plan_game_ids = []

    if ALLOW_REPEAT_GAMES_SAME_DAY:
        while len(plan_game_ids) < slots_available:
            shuffled = game_ids[:]
            random.shuffle(shuffled)
            plan_game_ids.extend(shuffled)
        plan_game_ids = plan_game_ids[:slots_available]
    else:
        plan_game_ids = game_ids[:slots_available]

    for i, gid in enumerate(plan_game_ids):
        total_min = start_total + i * interval
        h = (total_min // 60) % 24
        m = total_min % 60
        send_at = f"{plan_date_str} {h:02d}:{m:02d}"
        conn.execute(
            "INSERT INTO daily_plan (plan_date, game_id, send_at) VALUES (?,?,?)",
            (plan_date_str, gid, send_at)
        )

    conn.commit()
    conn.close()

# =========================================================
# ENVIO TELEGRAM
# =========================================================
def make_message(game_row, footer_text, footer_link):
    name = game_row["name"]
    provider = game_row["provider"]
    rtp = game_row["rtp"]
    emoji = game_row["emoji"]
    group = game_row["game_group"]

    strats = ESTRATEGIAS.get(group, ESTRATEGIAS["slots"])
    estrategia = random.choice(strats)
    cabecalho = random.choice(CABECALHOS)
    rodape = random.choice(RODAPES)
    sep = "═" * 22

    rtp_line = f"📊 RTP: {rtp}\n" if rtp else "📊 RTP: Verificado ✅\n"
    btn_line = f"\n🔗 {footer_link}" if footer_link else ""

    return (
        f"{cabecalho}\n\n"
        f"🎮 {name} {emoji}\n"
        f"🏢 Provedora: {provider}\n"
        f"{rtp_line}\n"
        f"{sep}\n"
        f"{estrategia}\n"
        f"{sep}\n\n"
        f"{rodape}\n\n"
        f"[{footer_text}]({footer_link}){btn_line}"
    )

def send_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("TOKEN ou CHAT_ID não configurados.")
        return False
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        r = requests.post(url, json=payload, timeout=30)
        print(f"Telegram: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"Erro Telegram: {e}")
        return False

# =========================================================
# SCHEDULER
# =========================================================
def scheduler_loop():
    print("Scheduler iniciado.")
    while True:
        try:
            now = datetime.now(APP_TZ)
            today = now.strftime("%Y-%m-%d")
            now_str = now.strftime("%Y-%m-%d %H:%M")

            build_daily_plan(today)

            conn = get_db()
            due = conn.execute("""
                SELECT dp.id, dp.game_id, g.name, g.provider, g.rtp, g.emoji, g.game_group
                FROM daily_plan dp
                JOIN games g ON g.id = dp.game_id
                WHERE dp.plan_date=? AND dp.sent=0 AND dp.send_at <= ?
                ORDER BY dp.send_at
            """, (today, now_str)).fetchall()
            conn.close()

            footer_text = get_setting("footer_text", DEFAULT_FOOTER_TEXT)
            footer_link = get_setting("footer_link", DEFAULT_FOOTER_LINK)

            for row in due:
                msg = make_message(row, footer_text, footer_link)
                ok = send_telegram(msg)
                if ok:
                    conn2 = get_db()
                    conn2.execute(
                        "UPDATE daily_plan SET sent=1, sent_at=? WHERE id=?",
                        (now_str, row["id"])
                    )
                    conn2.commit()
                    conn2.close()
                    print(f"Enviado: {row['name']} ({row['provider']})")
                time.sleep(2)

        except Exception as e:
            print(f"Erro scheduler: {e}")

        time.sleep(SCHEDULER_SLEEP_SECONDS)

def start_scheduler():
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()

# =========================================================
# AUTH
# =========================================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session or not session.get("is_admin"):
            flash("Acesso restrito ao administrador.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

# =========================================================
# TEMPLATES
# =========================================================
BASE_STYLE = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;background:#1a1a2e;color:#fff;min-height:100vh}
.topbar{background:#111;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #f5c542}
.topbar h1{color:#f5c542;font-size:20px}
.topbar a{color:#aaa;text-decoration:none;font-size:13px;margin-left:15px}
.topbar a:hover{color:#f5c542}
.container{max-width:1100px;margin:30px auto;padding:0 15px}
.card{background:#16213e;border:1px solid #f5c542;border-radius:10px;padding:20px;margin-bottom:20px}
.card h2{color:#f5c542;margin-bottom:15px;font-size:17px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:20px}
.stat{background:#16213e;border:1px solid #f5c542;border-radius:10px;padding:15px;text-align:center}
.stat-num{font-size:28px;font-weight:bold;color:#f5c542}
.stat-label{color:#aaa;font-size:12px;margin-top:5px}
.hora-box{text-align:center;background:#f5c542;color:#000;padding:10px;border-radius:8px;font-weight:bold;margin-bottom:20px;font-size:16px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#f5c542;color:#000;padding:8px;text-align:left}
td{padding:8px;border-bottom:1px solid #333;vertical-align:middle}
tr:hover{background:#0f3460}
.enviado{color:#4caf50;font-weight:bold}
.pendente{color:#f5c542}
.proximo{background:#0f3460!important}
.badge{display:inline-block;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:bold}
.badge-slots{background:#1a3a5c;color:#7cd4ff}
.badge-crash{background:#3a1a1a;color:#ff7c7c}
.badge-turbo{background:#1a3a1a;color:#7cff9a}
.badge-classico{background:#2a2a1a;color:#ffe07c}
.badge-megaways{background:#2a1a3a;color:#d07cff}
.badge-pesca{background:#1a2a3a;color:#7cccff}
.badge-mesa{background:#2a1a2a;color:#ff9cff}
.badge-bingo{background:#1a2a1a;color:#9cffbc}
.badge-sport{background:#2a1a1a;color:#ffbc9c}
label{display:block;color:#ccc;margin-bottom:5px;font-size:14px}
input,select,textarea{width:100%;padding:10px;background:#0f3460;color:#fff;border:1px solid #f5c542;border-radius:6px;margin-bottom:12px;font-size:14px}
.btn{background:#f5c542;color:#000;padding:10px 20px;border:none;border-radius:6px;cursor:pointer;font-weight:bold;font-size:14px}
.btn:hover{background:#e5b532}
.btn-red{background:#e8384f;color:#fff}
.btn-red:hover{background:#c42d41}
.btn-sm{padding:5px 12px;font-size:12px}
.flash{padding:10px 15px;border-radius:6px;margin-bottom:15px;font-size:14px}
.flash-success{background:#1a3a1a;border:1px solid #4caf50;color:#4caf50}
.flash-error{background:#3a1a1a;border:1px solid #e8384f;color:#e8384f}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:700px){.stats{grid-template-columns:1fr 1fr}.grid2{grid-template-columns:1fr}}
</style>
"""

LOGIN_HTML = BASE_STYLE + """
<div style="display:flex;align-items:center;justify-content:center;min-height:100vh">
<div style="background:#16213e;border:1px solid #f5c542;border-radius:10px;padding:40px;width:100%;max-width:380px">
  <h1 style="color:#f5c542;text-align:center;margin-bottom:25px">👑 Rainha Games</h1>
  {% for msg in get_flashed_messages() %}
  <div class="flash flash-error">{{ msg }}</div>
  {% endfor %}
  <form method="post">
    <label>Usuário</label>
    <input name="username" required>
    <label>Senha</label>
    <input name="password" type="password" required>
    <button class="btn" style="width:100%">Entrar</button>
  </form>
</div></div>
"""

DASH_HTML = BASE_STYLE + """
<div class="topbar">
  <h1>👑 Rainha Games — Painel</h1>
  <div>
    <a href="{{ url_for('dashboard') }}">Dashboard</a>
    {% if session.is_admin %}<a href="{{ url_for('admin_games') }}">Jogos</a>
    <a href="{{ url_for('admin_settings') }}">Configurações</a>{% endif %}
    <a href="{{ url_for('logout') }}">Sair</a>
  </div>
</div>
<div class="container">
  {% for msg in get_flashed_messages() %}
  <div class="flash flash-success">{{ msg }}</div>
  {% endfor %}

  <div class="hora-box">🕐 Horário Brasil: {{ agora }} — {{ data_hoje }}</div>

  <div class="stats">
    <div class="stat"><div class="stat-num">{{ total_games }}</div><div class="stat-label">Jogos Ativos</div></div>
    <div class="stat"><div class="stat-num" style="color:#4caf50">{{ sent_today }}</div><div class="stat-label">✅ Enviados Hoje</div></div>
    <div class="stat"><div class="stat-num">{{ pending_today }}</div><div class="stat-label">⏳ Pendentes</div></div>
    <div class="stat"><div class="stat-num" style="color:#e8384f">{{ total_plan }}</div><div class="stat-label">📅 Total Agenda</div></div>
  </div>

  <div class="card" style="margin-bottom:20px">
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
      <form method="post" action="{{ url_for('send_test') }}">
        <button class="btn btn-sm">🚀 Enviar Teste Agora</button>
      </form>
      <form method="post" action="{{ url_for('regen_plan') }}">
        <button class="btn btn-sm btn-red">🔄 Regerar Agenda de Hoje</button>
      </form>
    </div>
  </div>

  <div class="card">
    <h2>📅 Agenda de Hoje</h2>
    <div style="overflow-x:auto">
    <table>
      <tr><th>Horário</th><th>Jogo</th><th>Provedora</th><th>Tipo</th><th>RTP</th><th>Status</th></tr>
      {% for item in plan %}
      <tr class="{{ 'proximo' if item.is_next else '' }}">
        <td>{{ item.send_at[-5:] }}</td>
        <td>{{ item.emoji }} {{ item.name }}</td>
        <td style="color:#aaa;font-size:12px">{{ item.provider }}</td>
        <td><span class="badge badge-{{ item.group }}">{{ item.group }}</span></td>
        <td style="color:#f5c542;font-size:12px">{{ item.rtp or '✅' }}</td>
        <td class="{{ 'enviado' if item.sent else 'pendente' }}">
          {{ '✅ Enviado' if item.sent else ('👉 Próximo' if item.is_next else '⏳ Pendente') }}
        </td>
      </tr>
      {% endfor %}
    </table>
    </div>
  </div>
</div>
"""

GAMES_HTML = BASE_STYLE + """
<div class="topbar">
  <h1>👑 Rainha Games — Jogos</h1>
  <div>
    <a href="{{ url_for('dashboard') }}">Dashboard</a>
    <a href="{{ url_for('admin_settings') }}">Configurações</a>
    <a href="{{ url_for('logout') }}">Sair</a>
  </div>
</div>
<div class="container">
  {% for msg in get_flashed_messages() %}
  <div class="flash flash-success">{{ msg }}</div>
  {% endfor %}

  <div class="card">
    <h2>➕ Adicionar Jogo</h2>
    <form method="post" action="{{ url_for('admin_games') }}">
      <div class="grid2">
        <div>
          <label>Nome do Jogo</label>
          <input name="name" required>
          <label>Provedora</label>
          <input name="provider" required>
        </div>
        <div>
          <label>RTP (opcional)</label>
          <input name="rtp" placeholder="ex: 96.50%">
          <label>Emoji</label>
          <input name="emoji" value="🎰">
          <label>Tipo</label>
          <select name="game_group">
            <option value="slots">Slots</option>
            <option value="crash">Crash</option>
            <option value="turbo">Turbo/Instant</option>
            <option value="classico">Clássico</option>
            <option value="megaways">Megaways</option>
            <option value="pesca">Pesca</option>
            <option value="mesa">Mesa</option>
            <option value="bingo">Bingo</option>
            <option value="sport">Sport</option>
          </select>
        </div>
      </div>
      <button class="btn">💾 Salvar Jogo</button>
    </form>
  </div>

  <div class="card">
    <h2>📋 Jogos Cadastrados ({{ games|length }})</h2>
    <div style="overflow-x:auto">
    <table>
      <tr><th>#</th><th>Jogo</th><th>Provedora</th><th>Tipo</th><th>RTP</th><th>Ativo</th><th>Ação</th></tr>
      {% for g in games %}
      <tr>
        <td>{{ g.id }}</td>
        <td>{{ g.emoji }} {{ g.name }}</td>
        <td style="color:#aaa;font-size:12px">{{ g.provider }}</td>
        <td><span class="badge badge-{{ g.game_group }}">{{ g.game_group }}</span></td>
        <td style="font-size:12px;color:#f5c542">{{ g.rtp or '—' }}</td>
        <td>{{ '✅' if g.active else '❌' }}</td>
        <td>
          <form method="post" action="{{ url_for('toggle_game', gid=g.id) }}" style="display:inline">
            <button class="btn btn-sm {{ 'btn-red' if g.active else '' }}">
              {{ '🚫 Desativar' if g.active else '✅ Ativar' }}
            </button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </table>
    </div>
  </div>
</div>
"""

SETTINGS_HTML = BASE_STYLE + """
<div class="topbar">
  <h1>👑 Rainha Games — Configurações</h1>
  <div>
    <a href="{{ url_for('dashboard') }}">Dashboard</a>
    <a href="{{ url_for('admin_games') }}">Jogos</a>
    <a href="{{ url_for('logout') }}">Sair</a>
  </div>
</div>
<div class="container">
  {% for msg in get_flashed_messages() %}
  <div class="flash flash-success">{{ msg }}</div>
  {% endfor %}
  <div class="card">
    <h2>⚙️ Configurações do Bot</h2>
    <form method="post">
      <div class="grid2">
        <div>
          <label>Texto do Botão (rodapé)</label>
          <input name="footer_text" value="{{ s.footer_text }}">
          <label>Link do Botão</label>
          <input name="footer_link" value="{{ s.footer_link }}">
        </div>
        <div>
          <label>Intervalo entre sinais (minutos)</label>
          <input name="send_interval" type="number" value="{{ s.send_interval }}" min="1">
          <label>Horário Início</label>
          <input name="start_time" value="{{ s.start_time }}" placeholder="00:00">
          <label>Horário Fim</label>
          <input name="end_time" value="{{ s.end_time }}" placeholder="23:59">
        </div>
      </div>
      <button class="btn">💾 Salvar Configurações</button>
    </form>
  </div>
</div>
"""

# =========================================================
# ROTAS
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password_hash=?",
            (username, pwd_hash)
        ).fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = bool(user["is_admin"])
            return redirect(url_for("dashboard"))
        flash("Usuário ou senha incorretos.")
    return render_template_string(LOGIN_HTML)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET"])
@login_required
def dashboard():
    tz = APP_TZ
    now = datetime.now(tz)
    today = now.strftime("%Y-%m-%d")
    now_str = now.strftime("%Y-%m-%d %H:%M")

    build_daily_plan(today)

    conn = get_db()
    total_games = conn.execute("SELECT COUNT(*) FROM games WHERE active=1").fetchone()[0]

    plan_rows = conn.execute("""
        SELECT dp.id, dp.send_at, dp.sent,
               g.name, g.provider, g.rtp, g.emoji, g.game_group
        FROM daily_plan dp
        JOIN games g ON g.id = dp.game_id
        WHERE dp.plan_date=?
        ORDER BY dp.send_at
    """, (today,)).fetchall()

    sent_today = sum(1 for r in plan_rows if r["sent"])
    total_plan = len(plan_rows)
    pending_today = total_plan - sent_today
    conn.close()

    next_marked = False
    plan = []
    for r in plan_rows:
        is_next = False
        if not r["sent"] and not next_marked and r["send_at"] >= now_str:
            is_next = True
            next_marked = True
        plan.append({
            "send_at": r["send_at"],
            "sent": r["sent"],
            "name": r["name"],
            "provider": r["provider"],
            "rtp": r["rtp"],
            "emoji": r["emoji"],
            "group": r["game_group"],
            "is_next": is_next,
        })

    return render_template_string(DASH_HTML,
        agora=now.strftime("%H:%M"),
        data_hoje=today,
        total_games=total_games,
        sent_today=sent_today,
        pending_today=pending_today,
        total_plan=total_plan,
        plan=plan,
    )

@app.route("/send-test", methods=["POST"])
@login_required
def send_test():
    conn = get_db()
    game = conn.execute(
        "SELECT * FROM games WHERE active=1 ORDER BY RANDOM() LIMIT 1"
    ).fetchone()
    conn.close()
    if game:
        footer_text = get_setting("footer_text", DEFAULT_FOOTER_TEXT)
        footer_link = get_setting("footer_link", DEFAULT_FOOTER_LINK)
        msg = make_message(game, footer_text, footer_link)
        send_telegram(msg)
        flash(f"✅ Teste enviado: {game['name']} ({game['provider']})")
    return redirect(url_for("dashboard"))

@app.route("/regen-plan", methods=["POST"])
@login_required
def regen_plan():
    tz = APP_TZ
    today = datetime.now(tz).strftime("%Y-%m-%d")
    conn = get_db()
    conn.execute("DELETE FROM daily_plan WHERE plan_date=?", (today,))
    conn.commit()
    conn.close()
    build_daily_plan(today)
    flash("✅ Agenda de hoje regenerada com sucesso!")
    return redirect(url_for("dashboard"))

@app.route("/admin/games", methods=["GET", "POST"])
@admin_required
def admin_games():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        provider = request.form.get("provider", "").strip()
        rtp = request.form.get("rtp", "").strip() or None
        emoji = request.form.get("emoji", "🎰").strip()
        game_group = request.form.get("game_group", "slots")
        if name and provider:
            conn = get_db()
            conn.execute(
                "INSERT INTO games (name, provider, rtp, emoji, game_group) VALUES (?,?,?,?,?)",
                (name, provider, rtp, emoji, game_group)
            )
            conn.commit()
            conn.close()
            flash(f"✅ Jogo '{name}' adicionado!")
    conn = get_db()
    games = conn.execute("SELECT * FROM games ORDER BY provider, name").fetchall()
    conn.close()
    return render_template_string(GAMES_HTML, games=games)

@app.route("/admin/games/<int:gid>/toggle", methods=["POST"])
@admin_required
def toggle_game(gid):
    conn = get_db()
    game = conn.execute("SELECT active FROM games WHERE id=?", (gid,)).fetchone()
    if game:
        new_val = 0 if game["active"] else 1
        conn.execute("UPDATE games SET active=? WHERE id=?", (new_val, gid))
        conn.commit()
    conn.close()
    return redirect(url_for("admin_games"))

@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    if request.method == "POST":
        for key in ["footer_text", "footer_link", "send_interval", "start_time", "end_time"]:
            val = request.form.get(key, "").strip()
            if val:
                set_setting(key, val)
        flash("✅ Configurações salvas!")

    s = {
        "footer_text": get_setting("footer_text", DEFAULT_FOOTER_TEXT),
        "footer_link": get_setting("footer_link", DEFAULT_FOOTER_LINK),
        "send_interval": get_setting("send_interval", str(SEND_INTERVAL_MINUTES)),
        "start_time": get_setting("start_time", AUTO_START_TIME),
        "end_time": get_setting("end_time", AUTO_END_TIME),
    }
    return render_template_string(SETTINGS_HTML, s=s)

# =========================================================
# MAIN
# =========================================================
init_db()
start_scheduler()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
