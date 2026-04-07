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

LOCK_TIMEOUT_SECONDS = 60
SCHEDULER_LEASE_SECONDS = 45
SCHEDULER_INSTANCE_ID = f"{os.getenv('RENDER_INSTANCE_ID') or os.getenv('HOSTNAME') or 'local'}:{os.getpid()}"

DEFAULT_FOOTER_LINK = "https://beacons.ai/rainhagames"
DEFAULT_FOOTER_TEXT = "Jogue Aqui"

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
        # Números
        ("3 Buzzing Wilds", "96.50%", "🐝"),
        ("3 Dancing Monkeys", "96.50%", "🐒"),
        ("3 Genie Wishes", "96.50%", "🧞"),
        ("3 Kingdoms Battle of Red Cliffs", "96.50%", "⚔️"),
        ("3 Magic Eggs", "96.50%", "🥚"),
        ("5 Frozen Charms Megaways", "96.50%", "❄️"),
        ("5 Lions", "96.50%", "🦁"),
        ("5 Lions Dance", "96.50%", "🦁"),
        ("5 Lions Gold", "96.50%", "🦁"),
        ("5 Lions Megaways", "96.50%", "🦁"),
        ("5 Lions Megaways 2", "96.50%", "🦁"),
        ("5 Lions Reborn", "96.50%", "🦁"),
        ("6 Jokers", "96.50%", "🃏"),
        ("7 Clovers of Fortune", "96.50%", "🍀"),
        ("7 Monkeys", "96.50%", "🐒"),
        ("7 Piggies", "96.50%", "🐷"),
        ("777 Rush", "96.50%", "7️⃣"),
        ("8 Dragons", "96.50%", "🐉"),
        ("8 Golden Dragon Challenge", "96.50%", "🐉"),
        ("888 Dragons", "96.50%", "🐉"),
        ("888 Gold", "96.50%", "💰"),
        # A
        ("African Elephant", "96.50%", "🐘"),
        ("Aladdin and the Sorcerer", "96.50%", "🪔"),
        ("Anaconda Gold", "96.50%", "🐍"),
        ("Ancient Egypt", "96.50%", "🏺"),
        ("Ancient Egypt Classic", "96.50%", "🏺"),
        ("Ancient Island Megaways", "96.50%", "🏝️"),
        ("Angel vs Sinner", "96.50%", "😇"),
        ("Argonauts", "96.50%", "⚓"),
        ("Asgard", "96.50%", "⚡"),
        ("Aztec Blaze", "96.50%", "🔥"),
        ("Aztec Bonanza", "96.50%", "🏺"),
        ("Aztec Gems", "96.50%", "🏺"),
        ("Aztec Gems Deluxe", "96.50%", "🏺"),
        ("Aztec Gems Megaways", "96.50%", "🏺"),
        ("Aztec Powernudge", "96.50%", "🏺"),
        ("Aztec Smash", "96.50%", "🏺"),
        ("Aztec Treasure Hunt", "96.50%", "🏺"),
        # B
        ("Badge Blitz", "96.50%", "🤠"),
        ("Bandit Megaways", "96.50%", "🤠"),
        ("Barn Festival", "96.50%", "🌾"),
        ("Barnyard Megahays Megaways", "96.50%", "🐄"),
        ("Bee Keeper", "96.50%", "🐝"),
        ("Beware the Deep Megaways", "96.50%", "🦈"),
        ("Big Bass Amazon Xtreme", "96.50%", "🎣"),
        ("Big Bass Bonanza", "96.71%", "🎣"),
        ("Big Bass Bonanza 1000", "96.50%", "🎣"),
        ("Big Bass Bonanza 3 Reeler", "96.50%", "🎣"),
        ("Big Bass Bonanza Megaways", "96.70%", "🎣"),
        ("Big Bass Bonanza Reel Action", "96.50%", "🎣"),
        ("Big Bass Christmas Bash", "96.50%", "🎄"),
        ("Big Bass Christmas Frozen Lake", "96.50%", "❄️"),
        ("Big Bass Crash", "96.50%", "💥"),
        ("Big Bass Day at the Races", "96.50%", "🏇"),
        ("Big Bass Dice", "96.50%", "🎲"),
        ("Big Bass Floats My Boat", "96.50%", "🎣"),
        ("Big Bass Halloween", "96.50%", "🎃"),
        ("Big Bass Halloween 2", "96.50%", "🎃"),
        ("Big Bass Halloween 3", "96.50%", "🎃"),
        ("Big Bass Hold & Spinner Megaways", "96.50%", "🎣"),
        ("Big Bass Keeping It Reel", "96.50%", "🎣"),
        ("Big Bass Mission Fishin", "96.50%", "🎣"),
        ("Big Bass Raceday Repeat", "96.50%", "🏇"),
        ("Big Bass Reel Repeat", "96.50%", "🎣"),
        ("Big Bass Splash", "96.71%", "🎣"),
        ("Bigger Bass Splash", "96.50%", "🎣"),
        ("Bingo Mania", "96.50%", "🎱"),
        ("Black Bull", "96.50%", "🐂"),
        ("Blade & Fangs", "96.50%", "🧛"),
        ("Blazing Wilds Megaways", "96.50%", "🔥"),
        ("Blitz Super Wheel", "96.50%", "🎡"),
        ("Bloody Dawn", "96.50%", "🌅"),
        ("Bomb Bonanza", "96.50%", "💣"),
        ("Book of Golden Sands", "96.50%", "📖"),
        ("Book of Kingdoms", "96.50%", "📖"),
        ("Book of Monsters", "96.50%", "📖"),
        ("Book of the Fallen", "96.50%", "📖"),
        ("Book of Tut Megaways", "96.50%", "📖"),
        ("Book of Vikings", "96.50%", "📖"),
        ("Bounty Gold", "96.50%", "🏴‍☠️"),
        ("Bounty Hunter", "96.50%", "🤠"),
        ("Bow of Artemis", "96.50%", "🏹"),
        ("Brick House Bonanza", "96.50%", "🐷"),
        ("Buffalo King", "96.06%", "🦬"),
        ("Buffalo King Megaways", "96.78%", "🦬"),
        ("Buffalo King Untamed Megaways", "96.50%", "🦬"),
        # C
        ("Caishen's Cash", "96.50%", "💰"),
        ("Caishen's Gold", "96.50%", "💰"),
        ("Candy Blitz", "96.50%", "🍬"),
        ("Candy Blitz Bombs", "96.50%", "🍬"),
        ("Candy Corner", "96.50%", "🍬"),
        ("Candy Jar Clusters", "96.50%", "🍬"),
        ("Candy Stars", "96.50%", "🍬"),
        ("Captain Kraken Megaways", "96.50%", "🐙"),
        ("Cash Bonanza", "96.50%", "💵"),
        ("Cash Box", "96.50%", "💵"),
        ("Cash Chips", "96.50%", "💵"),
        ("Cash Elevator", "96.50%", "🛗"),
        ("Cash Patrol", "96.50%", "💵"),
        ("Cash Surge", "96.50%", "💵"),
        ("Castle of Fire", "96.50%", "🔥"),
        ("Chase for Glory", "96.50%", "🏆"),
        ("Chests of Cai Shen", "96.50%", "💰"),
        ("Chests of Cai Shen 2", "96.50%", "💰"),
        ("Chicken Chase", "96.50%", "🐔"),
        ("Chicken Drop", "96.50%", "🐔"),
        ("Chicken+", "96.50%", "🐔"),
        ("Chilli Heat", "96.50%", "🌶️"),
        ("Chilli Heat Megaways", "96.50%", "🌶️"),
        ("Chilli Heat Spicy Spins", "96.50%", "🌶️"),
        ("Christmas Big Bass Bonanza", "96.50%", "🎄"),
        ("Christmas Carol Megaways", "96.50%", "🎄"),
        ("Cleocatra", "96.50%", "🐱"),
        ("Clover Gold", "96.50%", "🍀"),
        ("Club Tropicana", "96.50%", "🌴"),
        ("Colossal Cash Zone", "96.50%", "💰"),
        ("Congo Cash", "96.50%", "🦍"),
        ("Congo Cash XL", "96.50%", "🦍"),
        ("Country Framing", "96.50%", "🚜"),
        ("Cowboys Gold", "96.50%", "🤠"),
        ("Cowboy Coins", "96.50%", "🤠"),
        ("Crank It Up", "96.50%", "🎸"),
        ("Crown of Fire", "96.50%", "👑"),
        ("Crystal Caverns Megaways", "96.50%", "💎"),
        ("Cult.", "96.50%", "🔮"),
        ("Curse of the Werewolf Megaways", "96.50%", "🐺"),
        ("Cyberheist City", "96.50%", "🤖"),
        ("Cyclops Smash", "96.50%", "👁️"),
        # D
        ("Da Vinci's Treasure", "96.50%", "🎨"),
        ("Dance Party", "96.50%", "🕺"),
        ("Darts", "96.50%", "🎯"),
        ("Day of Dead", "96.50%", "💀"),
        ("Demon Pots", "96.50%", "😈"),
        ("Devilicious", "96.50%", "😈"),
        ("Diamond Cascade", "96.50%", "💎"),
        ("Diamond Strike", "96.50%", "💎"),
        ("Diamonds Are Forever 3 Lines", "96.50%", "💎"),
        ("Diamonds of Egypt", "96.50%", "💎"),
        ("Ding Dong Christmas Bells", "96.50%", "🔔"),
        ("Dino Drop", "96.50%", "🦖"),
        ("Down the Rails", "96.50%", "🚂"),
        ("Drago – Jewels of Fortune", "96.50%", "🐉"),
        ("Dragon Gold 88", "96.50%", "🐉"),
        ("Dragon Hero", "96.50%", "🐉"),
        ("Dragon Hot Hold & Spin", "96.50%", "🐉"),
        ("Dragon King Hot Pots", "96.50%", "🐉"),
        ("Dragon Kingdom", "96.50%", "🐉"),
        ("Dragon Tiger Fortunes", "96.50%", "🐉"),
        ("Drill That Gold", "96.50%", "⛏️"),
        ("Duel of Night & Day", "96.50%", "⚔️"),
        ("Dwarf & Dragon", "96.50%", "🐉"),
        ("Dwarven Gold Deluxe", "96.50%", "⛏️"),
        ("Dynamite Diggin Doug", "96.50%", "💥"),
        # E
        ("Egyptian Fortunes", "96.50%", "🏺"),
        ("Elemental Gems Megaways", "96.50%", "💎"),
        ("Emerald King", "96.50%", "💎"),
        ("Emerald King Rainbow Road", "96.50%", "💎"),
        ("Emerald King Wheel of Wealth", "96.50%", "💎"),
        ("Empty the Bank", "96.50%", "🏦"),
        ("Escape the Pyramid Fire & Ice", "96.50%", "🏺"),
        ("Eternal Empress Freeze Time", "96.50%", "👸"),
        ("Excalibur Unleashed", "96.50%", "⚔️"),
        ("Extra Juicy", "96.50%", "🍉"),
        ("Extra Juicy Megaways", "96.52%", "🍉"),
        ("Eye of Cleopatra", "96.50%", "👁️"),
        ("Eye of Spartacus", "96.50%", "🛡️"),
        ("Eye of the Storm", "96.50%", "🌪️"),
        # F
        ("Fairytale Fortune", "96.50%", "🧚"),
        ("Fangtastic Freespins", "96.50%", "🧛"),
        ("Fantastic League", "96.50%", "⚽"),
        ("Fat Panda", "96.50%", "🐼"),
        ("Fire 88", "96.50%", "🔥"),
        ("Fire Archer", "96.50%", "🏹"),
        ("Fire Hot 100", "96.50%", "🔥"),
        ("Fire Hot 20", "96.50%", "🔥"),
        ("Fire Hot 40", "96.50%", "🔥"),
        ("Fire Hot 5", "96.50%", "🔥"),
        ("Fire Portals", "96.50%", "🔥"),
        ("Fire Stampede", "96.50%", "🦬"),
        ("Fire Stampede 2", "96.50%", "🦬"),
        ("Fire Stampede Ultimate", "96.50%", "🦬"),
        ("Fire Strike", "96.50%", "🔥"),
        ("Fire Strike 2", "96.50%", "🔥"),
        ("Firebird Spirit", "96.50%", "🐦"),
        ("Fish Eye", "96.50%", "🐟"),
        ("Fishin' Reels", "96.50%", "🎣"),
        ("Floating Dragon Dragon Boat Festival", "96.50%", "🐉"),
        ("Floating Dragon Hold & Spin", "96.50%", "🐉"),
        ("Floating Dragon Wild Horses", "96.50%", "🐉"),
        ("Floating Dragon Year of the Snake", "96.50%", "🐍"),
        ("Fonzo's FelineFortunes", "96.50%", "🐱"),
        ("Force 1", "96.50%", "🏎️"),
        ("Forge of Olympus", "96.50%", "⚡"),
        ("Forging Wilds", "96.50%", "🔨"),
        ("Fortune Hit'n Roll", "96.50%", "💰"),
        ("Fortune of Giza", "96.50%", "🏺"),
        ("Fortune of Olympus", "96.50%", "⚡"),
        ("Fortunes of Aztec", "96.50%", "🏺"),
        ("Frightening Frankie", "96.50%", "🧟"),
        ("Front Runner Odds On", "96.50%", "🏇"),
        ("Frozen Tropics", "96.50%", "❄️"),
        ("Fruit Party", "96.50%", "🍓"),
        ("Fruit Party 2", "96.50%", "🍓"),
        ("Fruity Treats", "96.50%", "🍬"),
        ("Fury of Odin Megaways", "96.50%", "⚡"),
        # G
        ("Gates of Hades", "96.50%", "💀"),
        ("Gates of Olympus", "96.50%", "⚡"),
        ("Gates of Olympus 1000", "96.50%", "⚡"),
        ("Gates of Olympus Dice", "96.50%", "⚡"),
        ("Gates of Olympus Super Scatter", "96.50%", "⚡"),
        ("Gates of Olympus Xmas 1000", "96.50%", "⚡"),
        ("Gates of Valhalla", "96.50%", "⚔️"),
        ("Gears of Horus", "96.50%", "⚙️"),
        ("Gem Elevator", "96.50%", "💎"),
        ("Gems Bonanza", "96.50%", "💎"),
        ("Gems of Serengeti", "96.50%", "💎"),
        ("Genie's Gem Bonanza", "96.50%", "💎"),
        ("Goblin Heist Powernudge", "96.50%", "👺"),
        ("Gods of Giza", "96.50%", "🏺"),
        ("Gold Oasis", "96.50%", "💰"),
        ("Gold Party", "96.50%", "🥇"),
        ("Gold Rush", "96.50%", "⭐"),
        ("Gold Train", "96.50%", "🚂"),
        ("Good Luck & Good Fortune", "96.50%", "🍀"),
        ("Gorilla Mayhem", "96.50%", "🦍"),
        ("Gosmic Cash", "96.50%", "🚀"),
        ("Gravity Bonanza", "96.50%", "🌌"),
        ("Great Reef", "96.50%", "🐠"),
        ("Great Rhino", "95.97%", "🦏"),
        ("Great Rhino Deluxe", "96.50%", "🦏"),
        ("Great Rhino Megaways", "96.58%", "🦏"),
        ("Greedy Fortune Pig", "96.50%", "🐷"),
        ("Greedy Wolf", "96.50%", "🐺"),
        ("Greek Gods", "96.50%", "⚡"),
        ("Greyhound Racing", "96.50%", "🐕"),
        # H
        ("Hammer Storm", "96.50%", "🔨"),
        ("Hand of Midas 2", "96.50%", "✋"),
        ("Happy Dragon", "96.50%", "🐉"),
        ("Happy Hooves", "96.50%", "🐴"),
        ("Haunted Crypt", "96.50%", "💀"),
        ("Heart of Cleopatra", "96.50%", "💗"),
        ("Heart of Rio", "96.50%", "❤️"),
        ("Heist for the Golden Nuggets", "96.50%", "💰"),
        ("Hellvis Wild", "96.50%", "🎸"),
        ("Hercules and Pegasus", "96.50%", "🦅"),
        ("Hercules Son of Zeus", "96.50%", "💪"),
        ("Heroic Spins", "96.50%", "🛡️"),
        ("High Flyer", "96.50%", "✈️"),
        ("Himalayan Wild", "96.50%", "🐆"),
        ("Honey Honey Honey", "96.50%", "🍯"),
        ("Horse Racing", "96.50%", "🏇"),
        ("Hot Chilli", "96.50%", "🌶️"),
        ("Hot Fiesta", "96.08%", "🌶️"),
        ("Hot Pepper", "96.50%", "🌶️"),
        ("Hot Safari", "96.50%", "🦁"),
        ("Hot Tuna", "96.50%", "🐟"),
        ("Hot to Burn", "96.50%", "🔥"),
        ("Hot to Burn Extreme", "96.50%", "🔥"),
        ("Hot to Burn Hold and Spin", "96.50%", "🔥"),
        ("Hot to Burn Multiplier", "96.50%", "🔥"),
        ("Hot to Burn 7 Deadly", "96.50%", "🔥"),
        ("Hundreds and Thousands", "96.50%", "🍰"),
        # I
        ("Ice Lobster", "96.50%", "🦞"),
        ("Ice Mints", "96.50%", "❄️"),
        ("Infective Wild", "96.50%", "🧟"),
        ("Irish Charms", "96.50%", "🍀"),
        ("Irish Crown", "96.50%", "🍀"),
        # J
        ("Jackpot Blaze", "96.50%", "7️⃣"),
        ("Jackpot Hunter", "96.50%", "🏆"),
        ("Jade Butterfly", "96.50%", "🦋"),
        ("Jane Hunter and the Mask of Montezuma", "96.50%", "🏺"),
        ("Jasmine Dreams", "96.50%", "🌸"),
        ("Jeitinho Brasileiro", "96.50%", "🇧🇷"),
        ("Jelly Express", "96.50%", "🍬"),
        ("Jewel Rush", "96.50%", "💎"),
        ("John Hunter and the Aztec Treasure", "96.50%", "🏺"),
        ("John Hunter and the Book of Tut", "96.50%", "📖"),
        ("John Hunter and the Book of Tut Respin", "96.50%", "📖"),
        ("John Hunter and the Mayan Gods", "96.50%", "🏺"),
        ("John Hunter & the Quest for Bermuda Riches", "96.50%", "🏝️"),
        ("John Hunter & the Tomb of the Scarab Queen", "96.50%", "🐞"),
        ("Joker King", "96.50%", "🃏"),
        ("Joker's Jewels", "96.50%", "🃏"),
        ("Joker's Jewels Cash", "96.50%", "🃏"),
        ("Joker's Jewels Dice", "96.50%", "🃏"),
        ("Joker's Jewels Hold & Spin", "96.50%", "🃏"),
        ("Joker's Jewels Hot", "96.50%", "🃏"),
        ("Joker's Jewels Wild", "96.50%", "🃏"),
        ("Journey to the West", "96.50%", "🐒"),
        ("Juicy Fruits", "96.50%", "🍓"),
        ("Juicy Fruits Multihold", "96.50%", "🍓"),
        ("Jungle Gorilla", "96.50%", "🦍"),
        # K
        ("Kingdom of the Dead", "96.50%", "💀"),
        ("Knight Hot Spotz", "96.50%", "⚔️"),
        ("Knights vs Barbarians", "96.50%", "⚔️"),
        # L
        ("Lady Godiva", "96.50%", "🐴"),
        ("Lamp of Infinity", "96.50%", "🪔"),
        ("Lava Balls", "96.50%", "🌋"),
        ("Leprechaun Carol", "96.50%", "🍀"),
        ("Leprechaun Song", "96.50%", "🍀"),
        ("Little Gem", "96.50%", "💎"),
        ("Lobster Bob's Crazy Crab Shack", "96.50%", "🦞"),
        ("Lobster Bob's Sea Food and Win It", "96.50%", "🦞"),
        ("Lobster House", "96.50%", "🦞"),
        ("Loki's Riches", "96.50%", "⚡"),
        ("Lucky Dragons", "96.50%", "🐉"),
        ("Lucky Grace and Charm", "96.50%", "🍀"),
        ("Lucky Lightning", "96.50%", "⚡"),
        ("Lucky New Year", "96.50%", "🎆"),
        ("Lucky's Wild Pub", "96.50%", "🍺"),
        ("Lucky's Wild Pub 2", "96.50%", "🍺"),
        # M
        ("Madame Destiny", "96.50%", "🔮"),
        ("Madame Destiny Megaways", "96.50%", "🔮"),
        ("Magic Journey", "96.50%", "🌟"),
        ("Magic Money Maze", "96.50%", "💰"),
        ("Magician's Secrets", "96.50%", "🎩"),
        ("Mahjong Wins Super Scatter", "96.50%", "🀄"),
        ("Mammoth Gold Megaways", "96.50%", "🦣"),
        ("Master Chen's Fortune", "96.50%", "💰"),
        ("Master Joker", "96.50%", "🃏"),
        ("Medusa's Stone", "96.50%", "🐍"),
        ("Mermaid's Treasure Trove", "96.50%", "🧜"),
        ("Might of Freya Megaways", "96.50%", "⚡"),
        ("Might of Ra", "96.50%", "☀️"),
        ("Mighty Kong", "96.50%", "🦍"),
        ("Mighty Munching Melons", "96.50%", "🍈"),
        ("Mining Rush", "96.50%", "⛏️"),
        ("Mochimon", "96.50%", "🎭"),
        ("Moleiona Ire", "96.50%", "🐀"),
        ("Money Mouse", "96.50%", "🐭"),
        ("Money Stacks", "96.50%", "💵"),
        ("Money Stacks Dice", "96.50%", "🎲"),
        ("Money Stacks Megaways", "96.50%", "💵"),
        ("Monkey Madness", "96.50%", "🐒"),
        ("Monkey Warrior", "96.50%", "🐒"),
        ("Monster Superlanche", "96.50%", "👹"),
        ("Muertos Multiplier Megaways", "96.50%", "💀"),
        ("Mummy's Jewels 100", "96.50%", "🏺"),
        ("Mustang Gold", "96.50%", "🐎"),
        ("Mustang Gold Megaways", "96.50%", "🐎"),
        ("Mustang Trail", "96.50%", "🐎"),
        ("Mysterious", "96.50%", "🔮"),
        ("Mysterious Egypt", "96.50%", "🏺"),
        ("Mystery Mice", "96.50%", "🐭"),
        ("Mystery of the Orient", "96.50%", "🏮"),
        ("Mystic Chief", "96.50%", "🪶"),
        # N
        ("New Year Festival Floating Dragon", "96.50%", "🐉"),
        ("Nile Fortune", "96.50%", "🏺"),
        ("North Guardians", "96.50%", "🛡️"),
        # O
        ("O Vira-Lata Caramelo", "96.50%", "🐕"),
        ("Octobeer Fortunes", "96.50%", "🍺"),
        ("Oodles of Noodles", "96.50%", "🍜"),
        ("Oracle of Gold", "96.50%", "🔮"),
        # P
        ("Pandemic Rising", "96.50%", "🦠"),
        ("Panda's Fortune", "96.50%", "🐼"),
        ("Panda's Fortune 2", "96.50%", "🐼"),
        ("Peak Power", "96.50%", "⚡"),
        ("Peking Luck", "96.50%", "🏮"),
        ("Penalty Shootout", "96.50%", "⚽"),
        ("Piggy Bank Bills", "96.50%", "🐷"),
        ("Piggy Bankers", "96.50%", "🐷"),
        ("Pinup Girls", "96.50%", "💄"),
        ("Pirate Gold", "96.50%", "🏴‍☠️"),
        ("Pirate Gold Deluxe", "96.50%", "🏴‍☠️"),
        ("Pirate Golden Age", "96.50%", "🏴‍☠️"),
        ("Pirates Pub", "96.50%", "🏴‍☠️"),
        ("Pixie Wings", "96.50%", "🧚"),
        ("Pizza! Pizza? Pizza!", "96.50%", "🍕"),
        ("Plinko+", "96.50%", "🔴"),
        ("Pompeii Megareels Megaways", "96.50%", "🌋"),
        ("Pot of Fortune", "96.50%", "🍀"),
        ("Power of Merlin Megaways", "96.50%", "⚡"),
        ("Power of Thor Megaways", "96.55%", "⚡"),
        # Q-R
        ("Release the Kraken", "96.50%", "🐙"),
        # S
        ("Starlighta Princess", "96.50%", "⭐"),
        ("Sugar Rush", "96.50%", "🍬"),
        ("Sugar Rush 1000", "96.50%", "🍬"),
        ("Sweet Bonanza", "96.51%", "🍭"),
        ("Sweet Bonanza 1000", "96.50%", "🍭"),
        ("Sweet Bonanza Xmas", "96.48%", "🎄"),
        # T
        ("The Dog House", "96.51%", "🐶"),
        ("The Dog House Megaways", "96.55%", "🐶"),
        ("Touro Sortudo", "96.50%", "🐂"),
        # W
        ("Wild West Gold", "96.51%", "🤠"),
        ("Wild West Gold Megaways", "96.54%", "🤠"),
        ("Wolf Gold", "96.01%", "🐺"),
    ],
    "Hacksaw": [
        ("2 Wild 2 Die", "96.30%", "💥"),
        ("Aztec Twist", "96.36%", "🏺"),
        ("Balloons", "96.30%", "🎈"),
        ("Beam Boys", "96.30%", "⚡"),
        ("Beast Below", "96.30%", "🐙"),
        ("Benny the Beer", "96.30%", "🍺"),
        ("Blocks", "96.30%", "🟨"),
        ("Bloodthirst", "96.30%", "🧛"),
        ("Born Wild", "96.30%", "🐺"),
        ("Bouncy Bombs", "96.30%", "💣"),
        ("Boxes", "96.30%", "🎁"),
        ("Break Bones", "96.30%", "💀"),
        ("Break the Ice", "96.30%", "❄️"),
        ("Buffalo Stack'N'Sync", "96.30%", "🦬"),
        ("Cash Compass", "96.42%", "🧭"),
        ("Cash Crew", "96.30%", "💰"),
        ("Cash Pool", "96.30%", "💵"),
        ("Cash Quest", "96.30%", "🏆"),
        ("Cash Scratch", "96.30%", "🎟️"),
        ("Cash Vault I", "96.30%", "🏦"),
        ("Cash Vault II", "96.30%", "🏦"),
        ("Chaos Crew", "96.30%", "💥"),
        ("Chaos Crew 2", "96.30%", "💥"),
        ("Chaos Crew Scratch", "96.30%", "🎟️"),
        ("Cloud Princess", "96.30%", "👸"),
        ("Coins", "96.30%", "🪙"),
        ("Colors", "96.30%", "🎨"),
        ("Crazy Donuts", "96.30%", "🍩"),
        ("Cubes", "96.30%", "🧊"),
        ("Cubes 2", "96.38%", "🧊"),
        ("Cursed Crypt", "96.30%", "💀"),
        ("Cursed Seas", "96.30%", "🏴‍☠️"),
        ("Cut the Grass", "96.30%", "🌿"),
        ("Dark Summoning", "96.30%", "🌑"),
        ("Dawn of Kings", "96.30%", "👑"),
        ("Densho", "96.40%", "⛩️"),
        ("Diamond Rush", "96.30%", "💎"),
        ("Dice", "96.30%", "🎲"),
        ("Divine Drop", "96.30%", "⚡"),
        ("Donny Dough", "96.30%", "🍩"),
        ("Dork Unit", "96.30%", "🤡"),
        ("Double Rainbow", "96.30%", "🌈"),
        ("Double Salary - 1 Year", "96.30%", "💵"),
        ("Dragon's Domain", "96.30%", "🐉"),
        ("Dream Car Speed", "96.30%", "🏎️"),
        ("Dream Car SUV", "96.30%", "🚗"),
        ("Dream Car Urban", "96.30%", "🚙"),
        ("Drop'Em", "96.30%", "🎯"),
        ("Eggstra Cash", "96.30%", "🥚"),
        ("Evil Eyes", "96.30%", "👁️"),
        ("Express 200 Scratch", "96.30%", "🎟️"),
        ("Eye of the Panda", "96.30%", "🐼"),
        ("Fear the Dark", "96.30%", "🌑"),
        ("Feel the Beat", "96.30%", "🎵"),
        ("Fist of Destruction", "96.30%", "👊"),
        ("Football Scratch", "96.30%", "⚽"),
        ("Forest Fortune", "96.30%", "🌲"),
        ("Frank's Farm", "96.30%", "🚜"),
        ("Frogs Scratch", "96.30%", "🐸"),
        ("Fruit Duel", "96.30%", "🍊"),
        ("Frutz", "96.40%", "🍓"),
        ("Get the Cheese", "96.30%", "🐭"),
        ("Gladiator Legends", "96.30%", "🛡️"),
        ("Go Panda", "96.30%", "🐼"),
        ("Gold Coins", "96.30%", "🪙"),
        ("Gold Rush", "96.30%", "⭐"),
        ("Gronk's Gems", "96.30%", "💎"),
        ("Hand of Anubis", "96.24%", "🐺"),
        ("Happy Scratch", "96.30%", "🎟️"),
        ("Harvest Wilds", "96.30%", "🌾"),
        ("Hi-Lo", "96.30%", "🃏"),
        ("Hop'N Pop", "96.30%", "🐸"),
        ("It's Bananas!", "96.30%", "🍌"),
        ("Itero", "96.30%", "🏛️"),
        ("Jelly Slice", "96.30%", "🍬"),
        ("Joker Bombs", "96.48%", "🃏"),
        ("Keep 'Em Cool", "96.30%", "❄️"),
        ("Keep'Em", "96.27%", "❌"),
        ("King Carrot", "96.30%", "🥕"),
        ("King Treasure", "96.30%", "👑"),
        ("Koi Cash", "96.30%", "🐟"),
        ("Le Bandit", "96.30%", "🎭"),
        ("Le Cowboy", "96.28%", "🤠"),
        ("Le Viking", "96.30%", "🛡️"),
        ("Le Zeus", "96.30%", "⚡"),
        ("Let it Snow", "96.30%", "❄️"),
        ("Limbo", "96.30%", "🎯"),
        ("Lines", "96.30%", "🎯"),
        ("Love is All You Need", "96.30%", "❤️"),
        ("Lucky Number X8", "96.30%", "🎟️"),
        ("Lucky Number X12", "96.30%", "🎟️"),
        ("Lucky Number X16", "96.30%", "🎟️"),
        ("Lucky Number X20", "96.30%", "🎟️"),
        ("Lucky Scratch", "96.30%", "🎟️"),
        ("Lucky Shot", "96.30%", "🎯"),
        ("Magic Piggy", "96.30%", "🐷"),
        ("Mayan Stackways", "96.30%", "🏺"),
        ("Miami Multiplier", "96.30%", "🌴"),
        ("Mighty Masks", "96.30%", "🎭"),
        ("Mystery Motel", "96.30%", "🏨"),
        ("Octo Attack", "96.30%", "🐙"),
        ("Omnom", "96.30%", "🎮"),
        ("Outlaws Inc.", "96.30%", "🤠"),
        ("Plinko", "96.30%", "🔴"),
        ("Prince Treasure", "96.30%", "👑"),
        ("Pug Life", "96.30%", "🐶"),
        ("Queen Treasure", "96.30%", "👑"),
        ("Rat Riches", "96.30%", "🐭"),
        ("Rip City", "96.22%", "💀"),
        ("Rise of Ymir", "96.30%", "🧊"),
        ("Rocket Reels", "96.30%", "🚀"),
        ("Ronin Stackways", "96.30%", "⚔️"),
        ("Rotten", "96.30%", "🧟"),
        ("Ruby Rush", "96.30%", "💎"),
        ("Rusty & Curly", "96.30%", "🐷"),
        ("Scratch! Bronze", "96.30%", "🎟️"),
        ("Scratch! Gold", "96.30%", "🎟️"),
        ("Scratch! Platinum", "96.30%", "🎟️"),
        ("Scratch! Silver", "96.30%", "🎟️"),
        ("Scratch! Treasure", "96.30%", "🎟️"),
        ("Scratch 'Em", "96.30%", "🎟️"),
        ("Scratchy", "96.30%", "🎟️"),
        ("Scratchy Big", "96.30%", "🎟️"),
        ("Scratchy Mini", "96.30%", "🎟️"),
        ("Shave the Beard", "96.30%", "🪒"),
        ("Shave the Sheep", "96.30%", "🐑"),
        ("SixSixSix", "96.30%", "😈"),
        ("Slayers Inc", "96.30%", "⚔️"),
        ("Snow Scratcher", "96.30%", "❄️"),
        ("Speed Crash", "96.30%", "💥"),
        ("Spooky Scary Scratchy", "96.30%", "🎃"),
        ("Stack 'Em", "96.30%", "🟨"),
        ("Stack 'Em Scratch", "96.30%", "🎟️"),
        ("Stick'Em", "96.30%", "🟡"),
        ("Stormforged", "96.30%", "⚡"),
        ("Summer Scratch", "96.30%", "☀️"),
        ("Tai the Toad", "96.30%", "🐸"),
        ("Tasty Treats", "96.30%", "🍭"),
        ("Temple of Torment", "96.30%", "🏛️"),
        ("The Bowery Boys", "96.41%", "🦹"),
        ("The Perfect Scratch", "96.30%", "🎟️"),
        ("The Respinners", "96.30%", "🎰"),
        ("Tiger Scratch", "96.30%", "🐯"),
        ("Time Spinners", "96.30%", "⏰"),
        ("Toshi Video Club", "96.30%", "🎮"),
        ("Twenty-One", "96.30%", "🃏"),
        ("Twisted Lab", "96.30%", "🧪"),
        ("Undead Fortune", "96.30%", "💀"),
        ("Vending Machine", "96.30%", "🎰"),
        ("Wanted Dead or a Wild", "96.38%", "🤠"),
        ("Warrior Ways", "96.30%", "⚔️"),
        ("Wheel", "96.30%", "🎡"),
        ("Xmas Drop", "96.30%", "🎄"),
        ("Xpander", "96.30%", "💥"),
        ("Ze Zeus", "96.30%", "⚡"),
    ],
    "Spribe": [
        ("Aviator", "", "✈️"),
        ("Dice", "", "🎲"),
        ("Goal", "", "⚽"),
        ("Hi Lo", "", "🃏"),
        ("Hotline", "", "📞"),
        ("Keno", "", "🔢"),
        ("Keno 80", "", "🔢"),
        ("Mines", "", "💣"),
        ("Mini Roulette", "", "🎡"),
        ("Plinko", "", "🔴"),
    ],
    "Spirit": [
        ("Ace Wild", "", "🃏"),
        ("Carnival", "", "🎭"),
        ("Coming Money", "", "💰"),
        ("Gems Fortune", "", "💎"),
        ("Gems Fortune 2", "", "💎"),
        ("God of Wealth", "", "🐉"),
        ("Ice Princess", "", "❄️"),
        ("Joker Spin", "", "🤡"),
        ("Merry Christmas", "", "🎄"),
        ("Mouse Fortune", "", "🐭"),
        ("Ox Fortune", "", "🐂"),
        ("Rabbit Fortune", "", "🐰"),
        ("Tiger Fortune", "", "🐯"),
        ("Wild Buffalo", "", "🦬"),
        ("Wild Lion", "", "🦁"),
        ("Wrath of Olympus", "", "⚡"),
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
    "Revenge Games": [
        ("Fortune Mouse 2", "", "🐭"),
        ("Treasures of Aztec Rewind", "", "🏺"),
        ("Fortune Tiger 2", "", "🐯"),
        ("Super Dragon Hatch", "", "🐉"),
        ("Fortune Dragon 2", "", "🐉"),
        ("Dragon Hatch Reborn", "", "🐉"),
        ("Fortune Ox 2", "", "🐂"),
        ("Fortune Chicken", "", "🐔"),
        ("Fortune Monkey", "", "🐒"),
        ("Fortune Horse", "", "🐎"),
        ("Fortune Dog", "", "🐕"),
        ("Fortune Goat", "", "🐐"),
    ],
    "Rectangle Games": [
        ("Afun Firecrackers Fortune", "", "🐉"),
        ("Aquarius Fortune Wheel", "", "🎡"),
        ("Aztec's Mystery", "", "🏺"),
        ("Battle Ship", "", "⚓"),
        ("Black Assassin", "", "🗡️"),
        ("Capricorn's Orb of Fortune", "", "🔮"),
        ("Chicken Uncrossable", "", "🐔"),
        ("Disco Fever", "", "🪩"),
        ("Dragon Crash", "", "🐉"),
        ("Eggy Pop", "", "🥚"),
        ("Farmageddon", "", "🐄"),
        ("Fiesta Blue", "", "🎭"),
        ("Fiesta Green", "", "🎭"),
        ("Fiesta Magenta", "", "🎭"),
        ("Fiesta Red", "", "🎭"),
        ("Firecrackers Fortune", "", "🧨"),
        ("Firecrackers Fortune 100", "", "🧨"),
        ("Fortune Pig", "", "🐷"),
        ("Gold Diggers", "", "⛏️"),
        ("Golden Koi Trail", "", "🐟"),
        ("The Inmate Outcuss", "", "🔫"),
        ("Iron Valor", "", "⚔️"),
        ("Lucky Caramelo", "", "🍬"),
        ("Lucky Caramelo 1000", "", "🍬"),
        ("Lucky Duck", "", "🦆"),
        ("Lucky Fox", "", "🦊"),
        ("Lucky Panda", "", "🐼"),
        ("Lucky Snake", "", "🐍"),
        ("Lucky Turtle", "", "🐢"),
        ("Magic Circus", "", "🎪"),
        ("Money Mania", "", "💵"),
        ("Piggy Mines", "", "🐷"),
        ("Pirate's Treasure Reel", "", "🏴‍☠️"),
        ("Pisces Realm of Fortune", "", "🐟"),
        ("Prosperity Clash", "", "💰"),
        ("Prosperity Dragon", "", "🐉"),
        ("Prosperity Dragon Golden Reel", "", "🐉"),
        ("Prosperity Horse", "", "🐎"),
        ("Prosperity Mouse", "", "🐭"),
        ("Prosperity Ox", "", "🐂"),
        ("Prosperity Rabbit", "", "🐰"),
        ("Prosperity Tiger", "", "🐯"),
        ("Realm of Thunder", "", "⚡"),
        ("Rudolf's Gifts", "", "🦌"),
        ("Semana Santa Treasures", "", "✝️"),
        ("Shapes of Fortune", "", "🔷"),
        ("Shapes of Fortune Xmas", "", "🎄"),
        ("Smash Fury", "", "💥"),
        ("Solar Pong", "", "🌞"),
        ("Swaggy Caramelo", "", "🍬"),
        ("Swaggy Prize", "", "🏆"),
        ("The Lone Fireball", "", "🔥"),
        ("The Lucky Year", "", "🎆"),
        ("Tinkering Box", "", "🔧"),
        ("Topfly Pirate's Treasure Reel", "", "🏴‍☠️"),
        ("Treasures of Hades", "", "💀"),
        ("Wheel of Wealth", "", "🎡"),
        ("Year of the Golden Horse", "", "🐎"),
    ],
    "Funky Games": [
        ("5 Dragons Legend", "", "🐉"),
        ("7 Up 7 Down", "", "🎲"),
        ("7 Up Down", "", "🎲"),
        ("777 Blazing", "", "7️⃣"),
        ("777 Blazing 2", "", "7️⃣"),
        ("777 Blazing Classic", "", "7️⃣"),
        ("777 Blazing Hold and Win", "", "7️⃣"),
        ("Alice", "", "🐇"),
        ("Aloha Fruit Punch", "", "🍹"),
        ("Aloha! Fruityways", "", "🌺"),
        ("Atom", "", "⚛️"),
        ("Atomwar", "", "⚛️"),
        ("Aztec Fortune Megaways", "", "🏺"),
        ("Aztec Plinko", "", "🔴"),
        ("Baccarat Babes", "", "🃏"),
        ("Baccarat VVIP", "", "🃏"),
        ("Basketball Strike", "", "🏀"),
        ("Bau Cua", "", "🎲"),
        ("Belangkai", "", "🦀"),
        ("Big Bang Boxing", "", "🥊"),
        ("Bonus Bear", "", "🐻"),
        ("Buffalo Rage", "", "🦬"),
        ("Buffalo Splash", "", "🦬"),
        ("Cai Shen 88", "", "💰"),
        ("Caishen Baoxi", "", "💰"),
        ("Caishen's Fortune", "", "💰"),
        ("Calabash Brothers", "", "🎭"),
        ("Capsa Susun", "", "🃏"),
        ("Captain Money", "", "🏴‍☠️"),
        ("Captain's Treasure", "", "🏴‍☠️"),
        ("Caribbean Saga", "", "🎡"),
        ("Cash Booster", "", "💵"),
        ("Cash or Crash", "", "💥"),
        ("Cash or Crash 2", "", "💥"),
        ("Chicken Love", "", "🐔"),
        ("Clover Brew", "", "🍀"),
        ("Clover Coin Combo", "", "🍀"),
        ("Colorful Mermaid", "", "🧜"),
        ("Domino Gaplebet", "", "🀱"),
        ("Easter Run", "", "🐣"),
        ("Eros", "", "💘"),
        ("Euro Cup", "", "⚽"),
        ("Fafafa", "", "🎰"),
        ("Fafafa2", "", "🎰"),
        ("Fan Tan", "", "🎲"),
        ("Fish Prawn Crab", "", "🦀"),
        ("Football Champion", "", "⚽"),
        ("Football Fever", "", "⚽"),
        ("Football Mines", "", "💣"),
        ("Football Star", "", "⚽"),
        ("Football Strike", "", "⚽"),
        ("Fortune Dragon", "", "🐉"),
        ("Fortune Goddess", "", "👸"),
        ("Fortune Tree Wild", "", "🌳"),
        ("Gems of Zeus", "", "💎"),
        ("Ghost Pirate", "", "🏴‍☠️"),
        ("Golden Crab", "", "🦀"),
        ("Golden Dynasty", "", "👑"),
        ("Golden Koi Rise", "", "🐟"),
        ("Golden Mahjong Deluxe", "", "🀄"),
        ("Happy Hour Fruit Slot", "", "🍓"),
        ("Happy10", "", "🔢"),
        ("Haunted Spirit", "", "👻"),
        ("Hawaii", "", "🌺"),
        ("Heart of Ocean", "", "🌊"),
        ("Highway King", "", "🚛"),
        ("Huga", "", "🦁"),
        ("Ice Land", "", "❄️"),
        ("Inferno Sea", "", "🔥"),
        ("Ji Ji Ji", "", "🎰"),
        ("Jogo do Bicho", "", "🐾"),
        ("Kenosoccer", "", "🔢"),
        ("Kenowar", "", "🔢"),
        ("Landing Chicken", "", "🐔"),
        ("Legend of Egypt", "", "🏺"),
        ("Limbo Football", "", "🎯"),
        ("Lubu", "", "⚔️"),
        ("Lucky Lanterns", "", "🏮"),
        ("Lucky Wheel", "", "🎡"),
        ("Meow HiLo", "", "🃏"),
        ("Midnight Robbery", "", "💰"),
        ("Mines", "", "💣"),
        ("Mines or Crash", "", "💣"),
        ("Mines or Gift", "", "💣"),
        ("Mines or Treat", "", "💣"),
        ("Narcos", "", "🔫"),
        ("Nezha", "", "🔥"),
        ("Nuggets", "", "⛏️"),
        ("Number Game", "", "🔢"),
        ("Odds Hi Lo", "", "🃏"),
        ("Outlaw Trails", "", "🤠"),
        ("Panther Moon", "", "🐆"),
        ("Peony Beauty", "", "🌸"),
        ("Pinata", "", "🎉"),
        ("Plinko Mega Win", "", "🔴"),
        ("Plinko UFO", "", "🔴"),
        ("Plinkos", "", "🔴"),
        ("Pok Deng", "", "🃏"),
        ("Poker Slam", "", "♠️"),
        ("Poseidon 777", "", "🔱"),
        ("Racing King", "", "🏎️"),
        ("Rage of Olympus", "", "⚡"),
        ("RNGWar", "", "🎲"),
        ("Roma", "", "🛡️"),
        ("Roma Reborn", "", "🛡️"),
        ("Roulette VVIP", "", "🎡"),
        ("Royal Ace", "", "🂡"),
        ("Royal Tiger Baccarat", "", "🐯"),
        ("Safari Heat", "", "🦁"),
        ("Sexy Blink", "", "💃"),
        ("Shuihuheroes", "", "⚔️"),
        ("Skullbingo", "", "💀"),
        ("Southern Queen", "", "👑"),
        ("Sparta", "", "🛡️"),
        ("Sparta2", "", "🛡️"),
        ("Speed Blackjack", "", "🃏"),
        ("Sugar High", "", "🍬"),
        ("Sweet Bombs", "", "💣"),
        ("Tai Xiu", "", "🎲"),
        ("Taj Mahal", "", "🕌"),
        ("Thai HiLo", "", "🃏"),
        ("Thai Lotto", "", "🎟️"),
        ("Thai Paradise", "", "🌴"),
        ("The Phoenix from the Flames", "", "🔥"),
        ("Three Brave Piggies", "", "🐷"),
        ("Thunder Blackjack", "", "🃏"),
        ("Thunder Dice", "", "🎲"),
        ("Thunder Feng Shen", "", "⚡"),
        ("Treasure Dragon", "", "🐉"),
        ("Virtual Baccarat", "", "🃏"),
        ("Virtual Dragon Bonus Baccarat", "", "🃏"),
        ("Virtual Sicbo", "", "🎲"),
        ("Virtual Tiger Baccarat", "", "🐯"),
        ("White Lion", "", "🦁"),
        ("White Tiger", "", "🐯"),
        ("Zombie Killer", "", "🧟"),
    ],
    "Microgaming": [
        ("10000 Wishes", "", "🌟"),
        ("108 Heroes", "", "⚔️"),
        ("15 Tridents", "", "🔱"),
        ("25000 Talons", "", "🦅"),
        ("4 Diamond Blues Megaways", "", "💎"),
        ("5 Reel Drive", "", "🏎️"),
        ("5 Star Knockout", "", "⭐"),
        ("777 Mega Deluxe", "", "7️⃣"),
        ("777 Royal Wheel", "", "🎡"),
        ("777 Super Big Buildup Deluxe", "", "7️⃣"),
        ("777 Surge", "", "7️⃣"),
        ("9 Enchanted Beans", "", "🌱"),
        ("9 Masks of Fire", "", "🔥"),
        ("9 Pots of Gold", "", "🍀"),
        ("9 Pots of Gold Megaways", "", "🍀"),
        ("A Tale of Elves", "", "🧝"),
        ("Adventure Palace", "", "🏰"),
        ("Adventures of Doubloon Island", "", "🏝️"),
        ("Africa X Up", "", "🦁"),
        ("Age of Discovery", "", "⛵"),
        ("Agent Jane Blonde", "", "🕵️"),
        ("Agent Jane Blonde Max Volume", "", "🕵️"),
        ("Alaskan Fishing", "", "🎣"),
        ("Alchemy Fortunes", "", "⚗️"),
        ("Almighty Zeus Empire", "", "⚡"),
        ("Amazing Pharaoh", "", "🏺"),
        ("Amazon Lost Gold", "", "🌿"),
        ("Ancient Fortunes Poseidon Megaways", "", "🔱"),
        ("Ancient Fortunes Zeus", "", "⚡"),
        ("Andvari The Magic Ring", "", "💍"),
        ("Anvil & Ore", "", "⚒️"),
        ("Aquanauts", "", "🤿"),
        ("Ariana", "", "🧜"),
        ("Ark of Ra", "", "☀️"),
        ("Asgardian Fire", "", "🔥"),
        ("Asian Beauty", "", "🌸"),
        ("Assassin Moon", "", "🌙"),
        ("Astro Legends Lyra and Erion", "", "🌌"),
        ("Aurora Wilds", "", "🎡"),
        ("Avalon", "", "⚔️"),
        ("Aztec Falls", "", "🏺"),
        ("Badminton Hero", "", "🏸"),
        ("Bar Bar Black Sheep 5 Reel", "", "🐑"),
        ("Basketball Star", "", "🏀"),
        ("Basketball Star Deluxe", "", "🏀"),
        ("Basketball Star on Fire", "", "🏀"),
        ("Basketball Star Wilds", "", "🏀"),
        ("Beautiful Bones", "", "💀"),
        ("Big Boom Riches", "", "💥"),
        ("Big Kahuna", "", "🌺"),
        ("Big Top", "", "🎪"),
        ("Bikini Party", "", "👙"),
        ("Bison Moon", "", "🐂"),
        ("Blazing Mammoth", "", "🦣"),
        ("Boat of Fortune", "", "🐉"),
        ("Bolt X Up", "", "⚡"),
        ("Book of Mrs Claus", "", "🎄"),
        ("Book of Oz", "", "📖"),
        ("Book of Oz Lock & Spin", "", "📖"),
        ("Break Away", "", "🏒"),
        ("Break Away Deluxe", "", "🏒"),
        ("Break Away Lucky Wilds", "", "🏒"),
        ("Break Away Max", "", "🏒"),
        ("Break Away Ultra", "", "🏒"),
        ("Break Da Bank", "", "🏦"),
        ("Break Da Bank Again", "", "🏦"),
        ("Break Da Bank Again Megaways", "", "🏦"),
        ("Bubble Beez", "", "🐝"),
        ("Burning Desire", "", "🔥"),
        ("Bust the Bank", "", "🏦"),
        ("Candy Rush Wilds", "", "🍬"),
        ("Carnaval", "", "🎭"),
        ("Carnaval Jackpot", "", "🎭"),
        ("Cashapillar", "", "🐛"),
        ("Cat Clans", "", "🐱"),
        ("Centre Court", "", "🎾"),
        ("Champions of Olympus", "", "⚡"),
        ("Chests of Gold Power Combo", "", "💰"),
        ("Chilli Pepe Hot Stacks", "", "🌶️"),
        ("Chronicles of Olympus II Zeus", "", "⚡"),
        ("Chronicles of Olympus X Up", "", "⚡"),
        ("Circus Jugglers Jackpots", "", "🎪"),
        ("Crazy Rich Tigers", "", "🐯"),
        ("Cricket Star", "", "🏏"),
        ("Cricket Star Scratch", "", "🏏"),
        ("Deck the Halls", "", "🎄"),
        ("Diamond Empire", "", "💎"),
        ("Divine Riches Helios", "", "☀️"),
        ("Dog Days", "", "🐕"),
        ("Doki Doki Fireworks", "", "🎆"),
        ("Doki Doki Parfait", "", "🍮"),
        ("Dragon Shard", "", "🐉"),
        ("Dragon's Loot Link Win 4tune", "", "🐉"),
        ("Dream Date", "", "💘"),
        ("Dungeons and Diamonds", "", "💎"),
        ("Eagle's Wings", "", "🦅"),
        ("Egyptian Tombs", "", "🏺"),
        ("Emperor of the Sea", "", "🌊"),
        ("Emperor of the Sea Deluxe", "", "🌊"),
        ("Exotic Cats", "", "🐆"),
        ("Fiona's Christmas Fortune", "", "🎄"),
        ("Fire Forge", "", "🔥"),
        ("Fire and Roses Joker", "", "🌹"),
        ("Fire and Roses Jolly Joker", "", "🌹"),
        ("Fish 'Em Up", "", "🐟"),
        ("Fishin' Bigger Pots of Gold", "", "🎣"),
        ("Fishin' Christmas Pots of Gold", "", "🎣"),
        ("Fishin' Pots of Gold", "", "🎣"),
        ("Fishin' Pots of Gold Gold Blitz", "", "🎣"),
        ("Football Star", "", "⚽"),
        ("Football Star Deluxe", "", "⚽"),
        ("Forgotten Island Megaways", "", "🏝️"),
        ("Fortune Pike Gold", "", "🐟"),
        ("Fortunium", "", "💰"),
        ("Fruit Blast", "", "🍓"),
        ("Fruit vs Candy", "", "🍬"),
        ("Gallo Megaways Gold Bruno's", "", "🐓"),
        ("Gem Fire Frenzy", "", "💎"),
        ("Gems & Dragons", "", "🐉"),
        ("Gods & Pyramids Power Combo", "", "🏺"),
        ("Gold Blitz", "", "⚡"),
        ("Gold Blitz Extreme", "", "⚡"),
        ("Gold Collector", "", "💰"),
        ("Golden Princess", "", "👸"),
        ("Gopher Gold", "", "🐾"),
        ("Granny vs Zombies", "", "🧟"),
        ("Happy Lucky Cats", "", "🐱"),
        ("Happy Monster Claw", "", "👾"),
        ("Holly Jolly Penguins", "", "🐧"),
        ("Huangdi The Yellow Emperor", "", "👑"),
        ("Hyper Gold", "", "💛"),
        ("Immortal Romance", "", "🧛"),
        ("Ingots of Cai Shen", "", "💰"),
        ("Jungle Jim El Dorado", "", "🌿"),
        ("Jungle Jim and the Lost Sphinx", "", "🏺"),
        ("Kings of Crystals", "", "💎"),
        ("Ladies Nite", "", "🌙"),
        ("Lara Croft Temples and Tombs", "", "🏺"),
        ("Legacy of Oz", "", "📖"),
        ("Legend of the Moon Lovers", "", "🌙"),
        ("Legendary Treasures", "", "💰"),
        ("Leprechaun Strike", "", "🍀"),
        ("Loaded", "", "💵"),
        ("Lost Vegas", "", "🎰"),
        ("Lucha Legends", "", "🤼"),
        ("Lucky Bachelors", "", "🎰"),
        ("Lucky Clucks", "", "🐔"),
        ("Lucky Firecracker", "", "🧨"),
        ("Lucky Koi", "", "🐟"),
        ("Lucky Leprechaun Clusters", "", "🍀"),
        ("Lucky Twins", "", "🐉"),
        ("Lucky Twins Jackpot", "", "🐉"),
        ("Lucky Twins Link & Win", "", "🐉"),
        ("Lucky Twins Wilds", "", "🐉"),
        ("Magic Jokers", "", "🃏"),
        ("Mask of Amun", "", "🏺"),
        ("Masters of Olympus", "", "⚡"),
        ("Masters of Valhalla", "", "⚔️"),
        ("Maui Mischief", "", "🌺"),
        ("Max Damage and the Alien Attack", "", "👾"),
        ("Mermaids Millions", "", "🧜"),
        ("Mining Pots of Gold", "", "⛏️"),
        ("Monkey Bonanza", "", "🐒"),
        ("Oni Hunter Night Sakura", "", "🌸"),
        ("Ping Pong Star", "", "🏓"),
        ("Playboy", "", "🐰"),
        ("Playboy Fortunes", "", "🐰"),
        ("Playboy Gold Jackpots", "", "🐰"),
        ("Playboy Wilds", "", "🐰"),
        ("Pong Pong Mahjong", "", "🀄"),
        ("Pure Platinum", "", "💎"),
        ("Queen of Alexandria", "", "👑"),
        ("Queen of Crystal Rays", "", "💎"),
        ("Queens of Ra", "", "☀️"),
        ("Reel Gems", "", "💎"),
        ("Reel Gems Deluxe", "", "💎"),
        ("Reel Thunder", "", "⚡"),
        ("Relic Seekers", "", "🏺"),
        ("Retro Reels", "", "🎰"),
        ("Retro Reels Diamond Glitz", "", "💎"),
        ("Rhyming Reels Hearts & Tarts", "", "❤️"),
        ("Robin Hood's Heroes", "", "🏹"),
        ("Rome Fight for Gold", "", "🛡️"),
        ("Rugby Star", "", "🏉"),
        ("Rugby Star Deluxe", "", "🏉"),
        ("Santa's Wild Ride", "", "🎅"),
        ("Scrooge", "", "💰"),
        ("Serengeti Gold", "", "🦁"),
        ("Shamrock Holmes", "", "🍀"),
        ("Shogun of Time", "", "⚔️"),
        ("Showdown Saloon", "", "🤠"),
        ("Silver Seas", "", "⚓"),
        ("Silverback Multiplier Mountain", "", "🦍"),
        ("Soccer Striker", "", "⚽"),
        ("Solar Wilds", "", "☀️"),
        ("Spin Spin Sugar", "", "🍬"),
        ("Spring Break", "", "🌊"),
        ("Squealin' Riches", "", "🐷"),
        ("Starlite Fruits", "", "🍓"),
        ("Storm to Riches", "", "⛈️"),
        ("Sugar Craze Bonanza", "", "🍬"),
        ("Tally Ho", "", "🦊"),
        ("The Eternal Widow", "", "🕷️"),
        ("The Incredible Balloon Machine", "", "🎈"),
        ("The Twisted Circus", "", "🎪"),
        ("Thunderstruck", "", "⚡"),
        ("Thunderstruck II", "", "⚡"),
        ("Thunderstruck Stormchaser", "", "⚡"),
        ("Thunderstruck Wild Lightning", "", "⚡"),
        ("Tiger's Ice", "", "🐯"),
        ("Tiki Reward", "", "🗿"),
        ("Tiki Tiki Boom", "", "🗿"),
        ("Tippy Tavern", "", "🍺"),
        ("Titans of the Sun Theia", "", "☀️"),
        ("Treasure Palace", "", "💎"),
        ("Treasures of Lion City", "", "🦁"),
        ("Trojan Kingdom", "", "🛡️"),
        ("Unusual Suspects", "", "🕵️"),
        ("WWE Legends", "", "🤼"),
        ("Wacky Panda", "", "🐼"),
        ("Wanted Outlaws", "", "🤠"),
        ("Western Gold", "", "🤠"),
        ("What a Hoot", "", "🦉"),
        ("Wild Catch New", "", "🎣"),
        ("Wild Orient", "", "🐼"),
        ("Wild Scarabs", "", "🪲"),
        ("Wild Wild Romance", "", "❤️"),
        ("Wildfire Wins", "", "🎡"),
        ("Wildfire Wins Extreme", "", "🎡"),
        ("Wolf Blaze Megaways", "", "🐺"),
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
    "Playtech": [
        ("Adventure Trail Fireblaze Jackpots", "", "🏆"),
        ("Alohawaii Cash Collect", "", "🌺"),
        ("Amazing Factory Fire Blaze Golden", "", "🏭"),
        ("Azteca Bonus Lines", "", "🏺"),
        ("Azteca Cash Collect", "", "🏺"),
        ("Blue Wizard Fireblaze", "", "🧙"),
        ("Blue Wizard Megaways Fire Blaze Classics", "", "🧙"),
        ("Buffalo Blitz", "", "🦬"),
        ("Buffalo Blitz 2", "", "🦬"),
        ("Cash Collect Silver Bullet Bandit", "", "🤠"),
        ("Classic Roulette", "", "🎡"),
        ("Diamond Bet Roulette", "", "🎡"),
        ("Diamond Rise", "", "💎"),
        ("Double Digger", "", "⛏️"),
        ("Dragon Bonanza Gold Hit", "", "🐉"),
        ("Eternal Lady Fireblaze", "", "👸"),
        ("God of Storms 2 Age of the Gods", "", "⚡"),
        ("Gold Hit Lil Demon", "", "😈"),
        ("Gold Trio", "", "💰"),
        ("Halloween Fortune", "", "🎃"),
        ("Hit Bar", "", "🍺"),
        ("Hit Bar Gold", "", "🍺"),
        ("Jackpots Legacy of the Tiger Mega Fire Blaze", "", "🐯"),
        ("Jinns Moon Fire Blaze", "", "🧞"),
        ("Joker Rush Cash Collect", "", "🃏"),
        ("JP Bacon & Co. Gold Hit & Link", "", "🐷"),
        ("Khonsu God of Moon Mega Fire Blaze", "", "🌙"),
        ("King Blitz", "", "🦁"),
        ("Leprechaun's Luck Cash Collect Megaways", "", "🍀"),
        ("Leprechauns Luck Cash Collect", "", "🍀"),
        ("Macaque Fireblaze Golden", "", "🐒"),
        ("Mega Cash Collect Queen of the Pyramids", "", "🏺"),
        ("Mega Fire Blaze Big Circus", "", "🎪"),
        ("Penny Roulette", "", "🎡"),
        ("Pharaoh's Daughter Fireblaze", "", "🏺"),
        ("Premium Blackjack", "", "🃏"),
        ("Pyramid Linx", "", "👁️"),
        ("Quantum BJ Plus Instant Play", "", "🃏"),
        ("Red Wizard Fire Blaze Jackpot", "", "🧙"),
        ("Sahara Riches Cash Collect", "", "🏜️"),
        ("Sahara Riches Megaways Cash Collect", "", "🏜️"),
        ("Silent Samurai Mega Cash Collect", "", "⚔️"),
        ("Sky Queen Fireblaze", "", "👸"),
        ("Spin 'Em Round!", "", "🎡"),
        ("Tsai Shen's Gift Fireblaze", "", "💰"),
        ("Tundra Wolf Fire Blaze Golden", "", "🐺"),
        ("Wheels of Olympus Age of the Gods", "", "⚡"),
        ("Wild Pistolero Mega Fireblaze", "", "🤠"),
        ("Witches Cash Collect", "", "🧙"),
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
    "Fat Panda": [
        ("Panda Panda", "", "🐼"),
        ("Lucky Panda", "", "🐼"),
        ("Panda Gold", "", "🐼"),
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
        "💎 Estilo Premium Scratch:\n• Jogue em bet baixa e fixa\n• Máximo 5 raspadinhas por sessão\n• Não aumente a bet após perda\n• Se ganhar, pare — não reinvista tudo",
        "💎 Estilo Premium Scratch:\n• Sessão curta e controlada\n• Bet mínima para mais volume de jogadas\n• Stop win: dobrou a banca = encerra\n• Stop loss: 5 tentativas sem retorno",
    ],
    "coin_flip": [
        "💎 Estilo Premium Heads Tails:\n• Escolha sempre o mesmo lado por sessão\n• Bet fixa sem dobrar após perda\n• Máximo 8 rodadas por sessão\n• Stop loss: 5 derrotas seguidas = encerra",
        "💎 Estilo Premium Heads Tails:\n• Não troque de lado no meio da sessão\n• Gestão fixa sem martingale\n• Sessão disciplinada e curta\n• Lucro pequeno e consistente",
    ],
    "wheel": [
        "💎 Estilo Premium Wheel:\n• Aposte nos campos de menor multiplicador\n• Bet fixa e pequena\n• Máximo 10 giros por sessão\n• Não persiga o multiplicador máximo",
        "💎 Estilo Premium Wheel:\n• Foque nos campos com maior frequência\n• Bet constante sem variação\n• Sessão curta com meta definida\n• Stop loss: 30% da banca",
    ],
    "penalty": [
        "💎 Estilo Premium Penalty Shootout:\n• Escolha sempre o mesmo canto por sessão\n• Bet fixa sem progressão\n• Máximo 8 cobranças por sessão\n• Stop loss: 4 erros seguidos = pausa",
        "💎 Estilo Premium Penalty Shootout:\n• Não mude o canto no meio da sessão\n• Gestão disciplinada da banca\n• Sessão curta e objetiva\n• Encerre ao atingir a meta",
    ],
    "tower": [
        "💎 Estilo Premium Tower:\n• Suba no máximo 4 andares por rodada\n• Retire antes do 5º andar\n• Bet fixa e pequena\n• Pare ao perder 3 rodadas seguidas",
        "💎 Estilo Premium Tower:\n• Não force andares altos\n• Saída disciplinada no 3º ou 4º andar\n• Sessão curta com stop definido\n• Stop loss: 20% da banca",
    ],
    "grid_slot": [
        "💎 Estilo Premium Grid Slot:\n• Jogue em bet baixa — a volatilidade é alta\n• Aguarde as cascatas acontecerem naturalmente\n• Não aumente a bet em sequência negativa\n• Stop loss: 20% da banca por sessão\n• Quando encaixar uma sequência, retire o lucro",
        "💎 Estilo Premium Grid Slot:\n• Alta volatilidade — prepare a banca para sequências secas\n• Bet fixa e disciplinada durante toda a sessão\n• O potencial de multiplicador é alto — não force\n• Sessão curta com meta definida\n• Stop win: dobrou = encerra",
    ],
    "keno": [
        "💎 Estilo Premium Keno:\n• Escolha entre 4 e 6 números por rodada\n• Mantenha os mesmos números por toda a sessão\n• Bet fixa sem progressão após perda\n• Máximo 10 rodadas por sessão\n• Stop loss: 20% da banca",
        "💎 Estilo Premium Keno:\n• Não troque os números no meio da sessão\n• Gestão disciplinada e bet constante\n• Sessão curta com meta definida\n• Stop win: triplicou = encerra",
    ],
    "roulette": [
        "💎 Estilo Premium Roleta:\n• Aposte nas cores (vermelho ou preto) com bet fixa\n• Não use progressão após perda\n• Máximo 10 rodadas por sessão\n• Stop loss: 25% da banca\n• Escolha um lado e mantenha por toda a sessão",
        "💎 Estilo Premium Roleta:\n• Foque nas apostas de maior frequência\n• Bet pequena e constante\n• Sessão curta e disciplinada\n• Stop win: dobrou = encerra\n• Evite apostar em números únicos",
    ],
    "runner": [
        "💎 Estilo Premium Runner:\n• Comece com bet baixa até pegar o ritmo\n• Foque em desviar dos obstáculos sem pressa\n• Não aumente a bet em sequência negativa\n• Máximo 10 partidas por sessão\n• Stop loss: 20% da banca",
        "💎 Estilo Premium Runner:\n• Bet fixa e pequena por partida\n• Concentração total — não jogue apressado\n• Sessão curta com meta definida\n• Stop win: dobrou = encerra\n• Pare ao perder 4 seguidas",
    ],
    "baccarat": [
        "💎 Estilo Premium Baccarat:\n• Aposte sempre no Banker (menor vantagem da casa)\n• Bet fixa sem progressão\n• Máximo 10 mãos por sessão\n• Stop loss: 20% da banca\n• Não aposte no Tie",
        "💎 Estilo Premium Baccarat:\n• Mantenha a aposta no Banker por toda a sessão\n• Gestão disciplinada sem martingale\n• Sessão curta e objetiva\n• Stop win: 30% de lucro = encerra",
    ],
    "blackjack": [
        "💎 Estilo Premium Blackjack:\n• Siga sempre a estratégia básica\n• Bet fixa sem dobrar no tilt\n• Máximo 10 mãos por sessão\n• Stop loss: 20% da banca\n• Dobrar só no 10 ou 11 contra carta fraca do dealer",
        "💎 Estilo Premium Blackjack:\n• Disciplina total na estratégia básica\n• Gestão fixa sem progressão agressiva\n• Sessão curta com meta definida\n• Stop win: dobrou = encerra",
    ],
    "racing": [
        "💎 Estilo Premium Racing:\n• Escolha sempre o mesmo competidor por sessão\n• Bet fixa sem progressão\n• Máximo 8 apostas por sessão\n• Stop loss: 4 derrotas seguidas = pausa\n• Não mude de favorito no meio da sessão",
        "💎 Estilo Premium Racing:\n• Analise o histórico antes de apostar\n• Bet pequena e constante\n• Sessão curta e disciplinada\n• Stop win: dobrou = encerra",
    ],
    "bingo": [
        "💎 Estilo Premium Bingo:\n• Jogue com bet fixa e pequena\n• Máximo 10 cartelas por sessão\n• Não aumente a bet após sequência negativa\n• Stop loss: 20% da banca\n• Aproveite os bônus de múltiplas cartelas",
        "💎 Estilo Premium Bingo:\n• Controle o número de cartelas por rodada\n• Gestão disciplinada sem impulsividade\n• Sessão curta com meta definida\n• Stop win: dobrou = encerra",
    ],
    "darts": [
        "💎 Estilo Premium Darts:\n• Escolha sempre a mesma região alvo por sessão\n• Bet fixa sem progressão\n• Máximo 10 arremessos por sessão\n• Stop loss: 5 erros seguidos = pausa\n• Foco total na pontaria — não jogue apressado",
        "💎 Estilo Premium Darts:\n• Bet pequena e constante\n• Disciplina na escolha do alvo\n• Sessão curta com meta definida\n• Stop win: dobrou = encerra",
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
        ("Free", "R$ 0,00", "Acesso a alguns sinais do dia|Estratégias padrão (simplificadas)|Acesso ao grupo|Sem prioridade nas entradas|Suporte exclusivo para VIP e Premium"),
        ("VIP", "R$ 97,00", "Acesso completo aos sinais|Estratégias completas estilo premium|Prioridade nas entradas|Acesso ao grupo VIP|Método validado na prática"),
        ("Premium", "R$ 297,00", "Tudo do VIP|Acesso antecipado aos sinais|Estratégias agressivas exclusivas|Suporte prioritário|White label e personalização total"),
    ]
    for name, price, features in plans:
        cur.execute("SELECT id FROM plans WHERE name = %s", (name,))
        if not cur.fetchone():
            cur.execute("INSERT INTO plans (name, price, features, active) VALUES (%s, %s, %s, 1)", (name, price, features))

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
    if "hi-lo" in n or "hilo" in n or "hi lo" in n:
        return "hilo"
    if "limbo" in n:
        return "limbo"
    if "plinko" in n:
        return "plinko"
    if "scratch" in n or "scratchy" in n:
        return "scratch"
    if "heads tails" in n or "heads & tails" in n:
        return "coin_flip"
    if "lucky wheel" in n or n == "wheel":
        return "wheel"
    if "penalty" in n:
        return "penalty"
    if "tower" in n:
        return "tower"
    if n in {"blocks", "colors", "cubes", "cubes 2", "lines"}:
        return "grid_slot"
    if "roulette" in n or "mini roulette" in n:
        return "roulette"
    if "bingo" in n:
        return "bingo"
    if "blackjack" in n:
        return "blackjack"
    if "baccarat" in n:
        return "baccarat"
    if "darts" in n:
        return "darts"
    if "racing" in n or "horse racing" in n or "greyhound" in n or "front runner" in n or "day at the races" in n or "force 1" in n or "raceday" in n:
        return "racing"
    if "keno" in n:
        return "keno"
    if "chicken uncrossable" in n:
        return "runner"
    if "piggy mines" in n or "football mines" in n or "mines or" in n:
        return "mines"
    if "aquarius fortune wheel" in n or "wheel of wealth" in n or "blitz super wheel" in n or "caribbean saga" in n or "roulette vvip" in n or "777 royal wheel" in n or "aurora wilds" in n or "wildfire wins" in n or "spin 'em round" in n:
        return "wheel"
    if "cash or crash" in n or "big bass crash" in n:
        return "crash"
    if "meow hilo" in n or "odds hi lo" in n or "thai hilo" in n or "7 up" in n:
        return "hilo"
    if "aztec plinko" in n or "plinko mega win" in n or "plinko ufo" in n or "plinkos" in n:
        return "plinko"
    if "bau cua" in n or "fan tan" in n or "tai xiu" in n or "thunder dice" in n or "virtual sicbo" in n or "rngwar" in n or "money stacks dice" in n or "big bass dice" in n or "gates of olympus dice" in n or "joker's jewels dice" in n:
        return "dice"
    if "kenosoccer" in n or "kenowar" in n or "happy10" in n or "number game" in n or "thai lotto" in n or "keno 80" in n:
        return "keno"
    if "limbo football" in n:
        return "limbo"
    if "rocket reels" in n or "speed crash" in n or "hotline" in n or "doctor rocket" in n:
        return "crash"
    if "dice" in n or "crash" in n or "rocket" in n:
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
    """, (name.strip(), provider.strip(), (rtp or "").strip(), (emoji or "🎰").strip(), infer_game_type(provider, name), now_br_str()))
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
        "grid_slot": "grid_slot",
        "keno":      "keno",
        "roulette":  "roulette",
        "runner":    "runner",
        "baccarat":  "baccarat",
        "blackjack": "blackjack",
        "racing":    "racing",
        "bingo":     "bingo",
        "darts":     "darts",
    }
    if game_type in mapping:
        return mapping[game_type]
    modes = ["slots_leve", "slots_media", "slots_agressiva"]
    return modes[position % len(modes)]


def build_message_for_game(plan_date: str, position: int, game_row):
    intro = choose_variant(INTRO_VARIANTS, plan_date, game_row["id"], "intro")
    closing = choose_variant(CLOSING_VARIANTS, plan_date, game_row["id"], "closing")
    strategy_key = choose_strategy_key(game_row["game_type"], position)
    strategy_text = choose_variant(STRATEGY_VARIANTS[strategy_key], plan_date, game_row["id"], "strategy")

    provider_line = f"🏢 Provedora: {game_row['provider']}\n" if game_row["provider"] else ""
    rtp_line = f"📊 RTP: {game_row['rtp']}\n" if game_row["rtp"] else "📊 RTP: Verificado ✅\n"

    # Sinalização especial Megaways
    is_megaways = "megaways" in game_row["name"].lower()
    megaways_line = "⚡ Mecânica: MEGAWAYS — rolos expansíveis, alta volatilidade!\n" if is_megaways else ""

    return (
        f"{intro}\n\n"
        f"🎮 Jogo: {game_row['name']} {game_row['emoji']}\n"
        f"{provider_line}"
        f"{rtp_line}"
        f"{megaways_line}\n"
        f"{strategy_text}\n\n"
        f"{closing}"
    )


def acquire_scheduler_leadership() -> bool:
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
        can_take = (not current_owner or not current_lease or current_lease <= now_str or current_owner == SCHEDULER_INSTANCE_ID)
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
        return max(1, int(raw))
    except Exception:
        return SEND_INTERVAL_MINUTES


def get_max_late_minutes():
    raw = get_setting("max_late_minutes", str(MAX_LATE_MINUTES)).strip()
    try:
        return max(1, int(raw))
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
    max_interval = get_interval_minutes()
    min_interval = 1
    rng_slots = random.Random(stable_seed_for_day(day_str + "_slots"))
    slots = []
    current = start_dt
    while current <= end_dt:
        slots.append(current)
        minutes = rng_slots.randint(min_interval, max_interval)
        seconds = rng_slots.randint(0, 59)
        current += timedelta(minutes=minutes, seconds=seconds)
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
            INSERT INTO daily_plan (plan_date, position, game_id, send_at, sent, sent_at, telegram_status, telegram_response, locked_at)
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
    """, (day_str, now_dt.strftime("%Y-%m-%d %H:%M:%S"), cutoff_dt.strftime("%Y-%m-%d %H:%M:%S"), lock_cutoff, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def try_lock_item(item_id: int) -> bool:
    now_dt = now_br()
    lock_cutoff = (now_dt - timedelta(seconds=LOCK_TIMEOUT_SECONDS)).strftime("%Y-%m-%d %H:%M:%S")
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    conn = db()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE daily_plan SET locked_at = %s
            WHERE id = %s AND sent = 0 AND (locked_at = '' OR locked_at <= %s)
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
        UPDATE daily_plan SET sent = %s, sent_at = %s, telegram_status = %s, telegram_response = %s, locked_at = ''
        WHERE id = %s
    """, (1 if ok else 0, sent_now if ok else '', "ok" if ok else "erro", (response or "")[:1000], plan_row["id"]))
    cur.execute("""
        INSERT INTO sent_log (send_date, send_time, game_id, game_name, provider, sent_at, telegram_status, telegram_response)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (today_str(), datetime.strptime(plan_row["send_at"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M"), plan_row["game_id"], plan_row["game_name"], plan_row["provider"], sent_now, "ok" if ok else "erro", (response or "")[:1000]))
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
    keyboard = {"inline_keyboard": [[{"text": footer_text, "url": footer_link}]]}
    try:
        if image_url.strip():
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            data = {"chat_id": CHAT_ID, "photo": image_url.strip(), "caption": text[:1024], "reply_markup": json.dumps(keyboard)}
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {"chat_id": CHAT_ID, "text": text, "reply_markup": json.dumps(keyboard)}
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
                    game_row={"id": item["game_id"], "name": item["game_name"], "provider": item["provider"], "rtp": item["rtp"], "emoji": item["emoji"], "game_type": item["game_type"]}
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
.brand{font-size:22px;font-weight:700;color:var(--secondary);}
.top-actions a{color:#fff;text-decoration:none;margin-left:12px;padding:10px 14px;border-radius:12px;background:rgba(255,255,255,.06);display:inline-block;}
.container{max-width:1400px;margin:0 auto;padding:24px;}
.grid{display:grid;gap:18px;}
.grid-2{grid-template-columns:1.1fr .9fr;}
.grid-3{grid-template-columns:repeat(3, 1fr);}
.card{background:var(--dark2);border:1px solid rgba(212,175,55,.18);border-radius:24px;padding:20px;box-shadow:0 10px 30px rgba(0,0,0,.25);}
.card h2, .card h3{margin:0 0 14px 0;color:var(--secondary);}
.kpi{font-size:30px;font-weight:700;margin-top:10px;}
.sub{color:#d7d7d7;font-size:14px;}
form input, form select, form textarea{width:100%;background:#0e0e14;color:#fff;border:1px solid rgba(212,175,55,.18);border-radius:14px;padding:12px 14px;margin:8px 0 14px 0;outline:none;}
form textarea{min-height:140px;resize:vertical;}
button, .btn{background:linear-gradient(180deg, var(--secondary) 0%, #b58d10 100%);color:#111;border:none;border-radius:14px;padding:12px 16px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-block;}
.table-wrap{overflow:auto;}
table{width:100%;border-collapse:collapse;}
th, td{padding:12px;border-bottom:1px solid rgba(255,255,255,.08);text-align:left;vertical-align:top;}
th{color:var(--secondary);font-size:14px;}
.badge{display:inline-block;padding:6px 10px;border-radius:999px;font-size:12px;font-weight:700;}
.badge-success{background:rgba(57,217,138,.12);color:var(--success);}
.badge-gold{background:rgba(212,175,55,.12);color:var(--secondary);}
.flash{margin-bottom:16px;padding:14px 16px;border-radius:14px;background:rgba(255,255,255,.07);}
.preview{white-space:pre-wrap;background:#0e0e14;padding:16px;border-radius:18px;border:1px solid rgba(212,175,55,.14);}
.muted{color:#bdbdbd;font-size:13px;}
.small{font-size:12px;color:#cfcfcf;}
@media (max-width: 980px){.grid-2, .grid-3{grid-template-columns:1fr;}}
</style>
<script>
(function(){
    function isDashboard(){return window.location.pathname === '/' || window.location.pathname === '';}
    if(!isDashboard()) return;
    function updateDashboard(){
        fetch('/api/dashboard-stats')
            .then(function(r){return r.json();})
            .then(function(d){
                var els={'kpi-jogos':d.total_games,'kpi-providers':d.total_providers,'kpi-sent':d.sent_today,'kpi-pending':d.pending_today,'kpi-hora':d.hora_atual,'kpi-first':d.first_time,'kpi-last':d.last_time,'kpi-last-game':d.last_game,'kpi-last-time':d.last_send_time,'kpi-last-status':d.last_status};
                Object.keys(els).forEach(function(id){var el=document.getElementById(id);if(el&&els[id]!==undefined)el.textContent=els[id];});
                var prev=document.getElementById('preview-next');
                if(prev&&d.preview)prev.textContent=d.preview;
                var tbody=document.getElementById('tbody-logs');
                if(tbody&&d.logs){tbody.innerHTML=d.logs.map(function(row){var badge=row.status==='ok'?'<span class="badge badge-success">ok</span>':'<span class="badge badge-gold">'+(row.status||'-')+'</span>';return '<tr><td>'+row.date+'</td><td>'+row.time+'</td><td>'+row.game+'</td><td>'+row.provider+'</td><td>'+badge+'</td></tr>';}).join('');}
                var ind=document.getElementById('refresh-indicator');
                if(ind){ind.style.opacity='1';setTimeout(function(){ind.style.opacity='0';},800);}
            }).catch(function(){});
    }
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
        {% if messages %}{% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}{% endif %}
    {% endwith %}
    {{ content|safe }}
</div>
</body>
</html>
"""


def render_page(title, content):
    return render_template_string(
        BASE_HTML, title=title, content=content,
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
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s AND is_active = 1 LIMIT 1", (username, password))
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
        FROM daily_plan dp JOIN games g ON g.id = dp.game_id
        WHERE dp.plan_date = %s AND dp.sent = 0
        ORDER BY dp.position ASC LIMIT 1
    """, (today_str(),))
    next_item = cur.fetchone()
    cur.execute("SELECT * FROM sent_log ORDER BY id DESC LIMIT 12")
    recent_logs = cur.fetchall()
    cur.close()
    conn.close()

    preview = "Nenhuma prévia disponível."
    if next_item:
        preview = build_message_for_game(plan_date=next_item["plan_date"], position=next_item["position"], game_row={"id": next_item["game_id"], "name": next_item["game_name"], "provider": next_item["provider"], "rtp": next_item["rtp"], "emoji": next_item["emoji"], "game_type": next_item["game_type"]})

    rows_html = ""
    for row in recent_logs:
        status_badge = "badge-success" if row["telegram_status"] == "ok" else "badge-gold"
        rows_html += f'<tr><td>{row["send_date"]}</td><td>{row["send_time"]}</td><td>{row["game_name"] or "-"}</td><td>{row["provider"] or "-"}</td><td><span class="badge {status_badge}">{row["telegram_status"] or "-"}</span></td></tr>'

    first_time_text = datetime.strptime(first_time["send_at"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M") if first_time else "-"
    last_time_text = datetime.strptime(last_time["send_at"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M") if last_time else "-"

    html = f"""
    <div style="display:flex;justify-content:flex-end;align-items:center;margin-bottom:10px;gap:10px;">
        <span id="refresh-indicator" style="font-size:12px;color:#39d98a;opacity:0;transition:opacity .4s;">● atualizado</span>
        <span class="muted" style="font-size:12px;">⟳ Painel atualiza automaticamente a cada 20s</span>
    </div>
    <div class="grid grid-3">
        <div class="card"><div class="sub">Jogos no catálogo</div><div class="kpi" id="kpi-jogos">{total_games}</div></div>
        <div class="card"><div class="sub">Provedoras</div><div class="kpi" id="kpi-providers">{total_providers}</div></div>
        <div class="card"><div class="sub">Envios feitos hoje</div><div class="kpi" id="kpi-sent">{sent_today}</div></div>
    </div>
    <div class="grid grid-2" style="margin-top:18px;">
        <div class="card">
            <h2>Próxima mensagem automática</h2>
            <div class="preview" id="preview-next">{preview}</div>
            <div class="muted" style="margin-top:12px;">O botão "{get_setting("footer_text", DEFAULT_FOOTER_TEXT)}" é enviado automaticamente em todas as mensagens.</div>
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
                <thead><tr><th>Data</th><th>Hora</th><th>Jogo</th><th>Provedora</th><th>Status</th></tr></thead>
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
        cards += f'<div class="card"><h3>{row["name"]}</h3><div class="kpi" style="font-size:26px;">{row["price"]}</div><div class="preview" style="margin-top:12px;">{features}</div></div>'
    html = f'<div class="card"><h2>Plano de vendas</h2></div><div class="grid grid-3" style="margin-top:18px;">{cards}</div>'
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
                cur.execute("INSERT INTO users (username, password, role, plan, brand_name, created_at) VALUES (%s, %s, %s, %s, %s, %s)", (username, password, role, plan, brand_name, now_br_str()))
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
    rows = "".join(f'<tr><td>{u["id"]}</td><td>{u["username"]}</td><td>{u["role"]}</td><td>{u["plan"]}</td><td>{"Ativo" if u["is_active"] else "Inativo"}</td></tr>' for u in users)
    html = f"""
    <div class="grid grid-2">
        <div class="card">
            <h2>Criar usuário</h2>
            <form method="post">
                <label>Usuário</label><input name="username" required>
                <label>Senha</label><input name="password" required>
                <label>Tipo</label>
                <select name="role"><option value="client">Cliente</option><option value="admin">Admin</option></select>
                <label>Plano</label>
                <select name="plan"><option value="Free">Free</option><option value="VIP">VIP</option><option value="Premium">Premium</option></select>
                <label>Marca</label><input name="brand_name" value="Rainha Games">
                <button type="submit">Criar usuário</button>
            </form>
        </div>
        <div class="card">
            <h2>Usuários cadastrados</h2>
            <div class="table-wrap">
                <table><thead><tr><th>ID</th><th>Usuário</th><th>Tipo</th><th>Plano</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>
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
    cur.execute("SELECT provider, COUNT(*) AS total FROM games GROUP BY provider ORDER BY total DESC, provider ASC")
    provider_rows = cur.fetchall()
    cur.execute("SELECT * FROM games ORDER BY id DESC LIMIT 40")
    recent_games = cur.fetchall()
    cur.close()
    conn.close()
    provider_table = "".join(f'<tr><td>{row["provider"]}</td><td>{row["total"]}</td></tr>' for row in provider_rows)
    recent_table = "".join(f'<tr><td>{row["name"]}</td><td>{row["provider"]}</td><td>{row["rtp"] or "Verificado ✅"}</td><td>{row["emoji"]}</td><td>{row["game_type"]}</td></tr>' for row in recent_games)
    html = f"""
    <div class="grid grid-2">
        <div class="card">
            <h2>Adicionar jogo manual</h2>
            <form method="post">
                <input type="hidden" name="mode" value="single">
                <label>Provedora</label><input name="provider" placeholder="Ex.: PG Soft">
                <label>Nome do jogo</label><input name="name" placeholder="Ex.: Fortune Tiger">
                <label>RTP (opcional)</label><input name="rtp" placeholder="Ex.: 96.81%">
                <label>Emoji (opcional)</label><input name="emoji" value="🎰">
                <button type="submit">Adicionar jogo</button>
            </form>
        </div>
        <div class="card">
            <h2>Importação em massa</h2>
            <div class="small" style="margin-bottom:10px;">Formato: <b>Provedora | Nome | RTP | Emoji</b></div>
            <form method="post">
                <input type="hidden" name="mode" value="bulk">
                <textarea name="bulk_text" placeholder="PG Soft | Fortune Tiger | 96.81% | 🐯"></textarea>
                <button type="submit">Importar em massa</button>
            </form>
        </div>
    </div>
    <div class="grid grid-2" style="margin-top:18px;">
        <div class="card">
            <h2>Provedoras no catálogo</h2>
            <div class="table-wrap">
                <table><thead><tr><th>Provedora</th><th>Total</th></tr></thead><tbody>{provider_table}</tbody></table>
            </div>
        </div>
        <div class="card">
            <h2>Últimos jogos cadastrados</h2>
            <div class="table-wrap">
                <table><thead><tr><th>Jogo</th><th>Provedora</th><th>RTP</th><th>Emoji</th><th>Tipo</th></tr></thead><tbody>{recent_table}</tbody></table>
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
        if interval: set_setting("send_interval_minutes", interval)
        if late: set_setting("max_late_minutes", late)
        if start_time: set_setting("auto_start_time", start_time)
        if end_time: set_setting("auto_end_time", end_time)
        flash("Configurações salvas.")
        return redirect(url_for("admin_settings"))
    html = f"""
    <div class="card">
        <h2>Configurações</h2>
        <form method="post">
            <label>Nome da marca</label><input name="brand_name" value="{get_setting('brand_name', 'Rainha Games')}">
            <label>Texto do botão</label><input name="footer_text" value="{get_setting('footer_text', DEFAULT_FOOTER_TEXT)}">
            <label>Link do botão</label><input name="footer_link" value="{get_setting('footer_link', DEFAULT_FOOTER_LINK)}">
            <label>URL da imagem opcional</label><input name="hero_image_url" value="{get_setting('hero_image_url', '')}" placeholder="https://...">
            <label>Horário inicial automático</label><input name="auto_start_time" value="{get_setting('auto_start_time', AUTO_START_TIME)}">
            <label>Horário final automático</label><input name="auto_end_time" value="{get_setting('auto_end_time', AUTO_END_TIME)}">
            <label>Intervalo entre envios (minutos)</label><input name="send_interval_minutes" value="{get_setting('send_interval_minutes', str(SEND_INTERVAL_MINUTES))}">
            <label>Tolerância máxima de atraso (minutos)</label><input name="max_late_minutes" value="{get_setting('max_late_minutes', str(MAX_LATE_MINUTES))}">
            <label>Cor principal</label><input name="theme_primary" value="{get_setting('theme_primary', '#B3001B')}">
            <label>Cor secundária</label><input name="theme_secondary" value="{get_setting('theme_secondary', '#D4AF37')}">
            <label>Cor escura</label><input name="theme_dark" value="{get_setting('theme_dark', '#0B0B0F')}">
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
        FROM daily_plan dp JOIN games g ON g.id = dp.game_id
        WHERE dp.plan_date = %s AND dp.sent = 0
        ORDER BY dp.position ASC LIMIT 1
    """, (today_str(),))
    next_item = cur.fetchone()
    cur.close()
    conn.close()
    if not next_item:
        flash("Não há item pendente para teste hoje.")
        return redirect(url_for("dashboard"))
    msg = build_message_for_game(plan_date=next_item["plan_date"], position=next_item["position"], game_row={"id": next_item["game_id"], "name": next_item["game_name"], "provider": next_item["provider"], "rtp": next_item["rtp"], "emoji": next_item["emoji"], "game_type": next_item["game_type"]})
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
        FROM daily_plan dp JOIN games g ON g.id = dp.game_id
        WHERE dp.plan_date = %s AND dp.sent = 0
        ORDER BY dp.position ASC LIMIT 1
    """, (today_str(),))
    next_item = cur.fetchone()
    cur.execute("SELECT * FROM sent_log ORDER BY id DESC LIMIT 12")
    recent_logs = cur.fetchall()
    cur.close()
    conn.close()
    preview = "Nenhuma prévia disponível."
    if next_item:
        preview = build_message_for_game(plan_date=next_item["plan_date"], position=next_item["position"], game_row={"id": next_item["game_id"], "name": next_item["game_name"], "provider": next_item["provider"], "rtp": next_item["rtp"], "emoji": next_item["emoji"], "game_type": next_item["game_type"]})
    first_time_text = datetime.strptime(first_time["send_at"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M") if first_time else "-"
    last_time_text = datetime.strptime(last_time["send_at"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M") if last_time else "-"
    logs_data = [{"date": row["send_date"], "time": row["send_time"], "game": row["game_name"] or "-", "provider": row["provider"] or "-", "status": row["telegram_status"] or "-"} for row in recent_logs]
    return jsonify({"total_games": total_games, "total_providers": total_providers, "sent_today": sent_today, "pending_today": pending_today, "hora_atual": now_br().strftime("%H:%M:%S"), "first_time": first_time_text, "last_time": last_time_text, "last_game": last_log["game_name"] if last_log else "Ainda não houve envio", "last_send_time": last_log["send_time"] if last_log else "-", "last_status": last_log["telegram_status"] if last_log else "-", "preview": preview, "logs": logs_data})


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
