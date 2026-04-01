from flask import Flask, request, render_template_string, redirect, url_for
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

HORARIOS = ["09:00", "12:00", "18:00", "21:00"]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            imagem_url TEXT DEFAULT '',
            ativo INTEGER DEFAULT 1,
            ultimo_envio TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()

init_db()

def enviar_telegram(texto, imagem_url=""):
    if not TOKEN or not CHAT_ID:
        print("TOKEN ou CHAT_ID não configurados.")
        return
    try:
        if imagem_url and imagem_url.strip():
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            data = {"chat_id": CHAT_ID, "photo": imagem_url.strip(), "caption": texto}
            resultado = requests.post(url, data=data, timeout=30)
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {"chat_id": CHAT_ID, "text": texto}
            resultado = requests.post(url, data=data, timeout=30)
        print(f"Telegram respondeu: {resultado.status_code} - {resultado.text}")
    except Exception as e:
        print(f"Erro ao enviar: {e}")

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Painel Rainha Games</title>
    <style>
        body { font-family: Arial; background: #1a1a2e; color: #f5c542; padding: 20px; }
        h1 { color: #f5c542; }
        input, textarea { width: 100%; padding: 8px; margin: 5px 0 10px; background: #222; color: #fff; border: 1px solid #f5c542; border-radius: 5px; }
        button { background: #f5c542; color: #000; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #f5c542; text-align: left; }
        th { background: #f5c542; color: #000; }
        a { color: #e8384f; }
    </style>
</head>
<body>
    <h1>👑 Painel Rainha Games</h1>
    <p>Horário atual Brasil: <b>{{ agora }}</b></p>
    <h2>{{ titulo_form }}</h2>
    <form method="post" action="{{ action_form }}">
        <label>Texto da mensagem:</label>
        <textarea name="texto" rows="4">{{ mensagem.texto if editando else '' }}</textarea>
        <label>Link da imagem (opcional):</label>
        <input name="imagem_url" value="{{ mensagem.imagem_url if editando else '' }}">
        <button type="submit">{{ botao_form }}</button>
    </form>
    <h2>📋 Mensagens cadastradas</h2>
    <table>
        <tr><th>#</th><th>Texto</th><th>Imagem</th><th>Último envio</th><th>Ações</th></tr>
        {% for m in mensagens %}
        <tr>
            <td>{{ m[0] }}</td>
            <td>{{ m[1][:60] }}...</td>
            <td>{{ '✅' if m[2] else '❌' }}</td>
            <td>{{ m[4] or 'Nunca' }}</td>
            <td>
                <a href="/editar/{{ m[0] }}">✏️ Editar</a> |
                <a href="/excluir/{{ m[0] }}">🗑️ Excluir</a>
            </td>
        </tr>
        {% endfor %}
    </table>
    <br>
    <h3>🕐 Horários de envio (hoje):</h3>
    <p>{{ horarios_hoje }}</p>
</body>
</html>
"""

def buscar_mensagens():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, texto, imagem_url, ativo, ultimo_envio FROM mensagens")
    mensagens = c.fetchall()
    conn.close()
    return mensagens

def horarios_hoje():
    agora = datetime.now(FUSO)
    dia_numero = int(agora.strftime("%d"))
    rotacao = dia_numero % len(HORARIOS)
    return HORARIOS[rotacao:] + HORARIOS[:rotacao]

@app.route("/", methods=["GET", "POST"])
def painel():
    if request.method == "POST":
        texto = request.form["texto"]
        imagem_url = request.form.get("imagem_url", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO mensagens (texto, imagem_url) VALUES (?, ?)", (texto, imagem_url))
        conn.commit()
        conn.close()
        print(f"Mensagem salva: {texto[:30]}")
        return redirect(url_for("painel"))

    agora = datetime.now(FUSO).strftime("%H:%M")
    mensagens = buscar_mensagens()
    return render_template_string(HTML,
        agora=agora,
        mensagens=mensagens,
        titulo_form="➕ Nova mensagem",
        botao_form="Salvar mensagem",
        editando=False,
        mensagem={},
        action_form=url_for("painel"),
        horarios_hoje=", ".join(horarios_hoje())
    )

@app.route("/editar/<int:msg_id>", methods=["GET", "POST"])
def editar(msg_id):
    if request.method == "POST":
        texto = request.form["texto"]
        imagem_url = request.form.get("imagem_url", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE mensagens SET texto=?, imagem_url=? WHERE id=?", (texto, imagem_url, msg_id))
        conn.commit()
        conn.close()
        return redirect(url_for("painel"))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, texto, imagem_url, ativo, ultimo_envio FROM mensagens WHERE id=?", (msg_id,))
    mensagem = c.fetchone()
    conn.close()

    agora = datetime.now(FUSO).strftime("%H:%M")
    mensagens = buscar_mensagens()
    return render_template_string(HTML,
        agora=agora,
        mensagens=mensagens,
        titulo_form=f"✏️ Editando mensagem #{msg_id}",
        botao_form="Salvar alterações",
        editando=True,
        mensagem={"texto": mensagem[1], "imagem_url": mensagem[2]},
        action_form=url_for("editar", msg_id=msg_id),
        horarios_hoje=", ".join(horarios_hoje())
    )

@app.route("/excluir/<int:msg_id>")
def excluir(msg_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM mensagens WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("painel"))

def verificar_mensagens():
    while True:
        agora = datetime.now(FUSO)
        hora_atual = agora.strftime("%H:%M")
        data_hoje = agora.strftime("%Y-%m-%d")
        horarios = horarios_hoje()

        print(f"Verificando... horário Brasil: {hora_atual} | Horários hoje: {horarios}")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, texto, imagem_url, ativo, ultimo_envio FROM mensagens")
        mensagens = c.fetchall()

        for i, m in enumerate(mensagens):
            msg_id, texto, imagem_url, ativo, ultimo_envio = m
            if i < len(horarios):
                horario = horarios[i]
                if horario == hora_atual and ultimo_envio != data_hoje:
                    enviar_telegram(texto, imagem_url)
                    c.execute("UPDATE mensagens SET ultimo_envio=? WHERE id=?", (data_hoje, msg_id))
                    print(f"Enviado: {texto[:30]} às {hora_atual}")

        conn.commit()
        conn.close()
        time.sleep(20)

threading.Thread(target=verificar_mensagens, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
