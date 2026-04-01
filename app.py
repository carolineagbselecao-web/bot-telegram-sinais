from flask import Flask, request, render_template_string
import sqlite3
import threading
import time
from datetime import datetime
import pytz
import os
import requests

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)
FUSO = pytz.timezone("America/Sao_Paulo")
DB_PATH = "/tmp/database.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            horario TEXT,
            enviado INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def enviar_telegram(texto):
    if not TOKEN or not CHAT_ID:
        print("TOKEN ou CHAT_ID não configurados.")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        resultado = requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": texto},
            timeout=15
        )
        print(f"Telegram respondeu: {resultado.status_code} - {resultado.text}")
    except Exception as e:
        print(f"Erro ao enviar para o Telegram: {e}")


@app.route("/", methods=["GET", "POST"])
def painel():
    if request.method == "POST":
        titulo = request.form["titulo"].strip()
        horario = request.form["horario"].strip()

        if titulo and horario:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO mensagens (titulo, horario) VALUES (?, ?)",
                (titulo, horario)
            )
            conn.commit()
            conn.close()
            print(f"Mensagem salva: {titulo} às {horario}")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM mensagens WHERE enviado=0 ORDER BY horario")
    mensagens = c.fetchall()
    conn.close()

    agora = datetime.now(FUSO).strftime("%H:%M")

    html = """
    <h2>Painel de Mensagens Agendadas</h2>
    <p>Horário atual do Brasil: <b>{{ agora }}</b></p>

    <form method="post">
        Mensagem/Título:<br>
        <input name="titulo" style="width:300px"><br><br>

        Horário (HH:MM):<br>
        <input name="horario" placeholder="13:45" style="width:120px"><br><br>

        <button type="submit">Salvar</button>
    </form>

    <h3>Mensagens pendentes:</h3>
    {% for m in mensagens %}
        <p>{{ m[1] }} - {{ m[2] }}</p>
    {% else %}
        <p>Nenhuma mensagem pendente.</p>
    {% endfor %}
    """
    return render_template_string(html, mensagens=mensagens, agora=agora)


def enviar_mensagens():
    while True:
        agora = datetime.now(FUSO).strftime("%H:%M")
        print(f"Verificando mensagens... horário Brasil: {agora}")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM mensagens WHERE horario=? AND enviado=0",
            (agora,)
        )
        mensagens = c.fetchall()

        for m in mensagens:
            texto = f"""📢 MENSAGEM PROGRAMADA

📝 Conteúdo: {m[1]}
⏰ Horário: {m[2]}
"""
            enviar_telegram(texto)
            c.execute("UPDATE mensagens SET enviado=1 WHERE id=?", (m[0],))
            print(f"Mensagem enviada: {m[1]} às {m[2]}")

        conn.commit()
        conn.close()
        time.sleep(20)


init_db()
threading.Thread(target=enviar_mensagens, daemon=True).start()

if __name__ == "__main__":
    enviar_telegram("✅ Bot online e funcionando.")
    app.run(host="0.0.0.0", port=10000)
