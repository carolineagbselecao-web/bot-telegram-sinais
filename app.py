from flask import Flask, request, render_template_string
import telegram
import sqlite3
import threading
import time
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sinais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        jogo TEXT,
        horario TEXT,
        enviado INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def painel():
    if request.method == "POST":
        jogo = request.form["jogo"]
        horario = request.form["horario"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO sinais (jogo, horario) VALUES (?, ?)", (jogo, horario))
        conn.commit()
        conn.close()

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM sinais")
    sinais = c.fetchall()
    conn.close()

    html = """
    <h2>Painel de Sinais 🎰</h2>
    <form method="post">
        Jogo: <input name="jogo"><br>
        Horário (HH:MM): <input name="horario"><br>
        <button>Salvar</button>
    </form>

    <h3>Sinais programados:</h3>
    {% for s in sinais %}
        <p>{{s[1]}} - {{s[2]}}</p>
    {% endfor %}
    """
    return render_template_string(html, sinais=sinais)

def enviar_sinais():
    while True:
        agora = datetime.now().strftime("%H:%M")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM sinais WHERE horario=? AND enviado=0", (agora,))
        sinais = c.fetchall()

        for s in sinais:
            mensagem = f"""
🎰 SINAL CONFIRMADO 🎰

🎮 Jogo: {s[1]}
⏰ Horário: {s[2]}

💰 Estratégia:
- 3 tentativas
- Dobrar na perda

🔥 ENTRE COM GERENCIAMENTO!
"""
            bot.send_message(chat_id=CHAT_ID, text=mensagem)
            c.execute("UPDATE sinais SET enviado=1 WHERE id=?", (s[0],))

        conn.commit()
        conn.close()
        time.sleep(30)

threading.Thread(target=enviar_sinais).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
