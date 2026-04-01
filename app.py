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


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            horario TEXT NOT NULL,
            repetir INTEGER DEFAULT 1,
            ultimo_envio TEXT DEFAULT '',
            imagem_url TEXT DEFAULT ''
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
        if imagem_url.strip():
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            data = {
                "chat_id": CHAT_ID,
                "photo": imagem_url.strip(),
                "caption": texto
            }
            resultado = requests.post(url, data=data, timeout=30)
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": texto
            }
            resultado = requests.post(url, data=data, timeout=30)

        print(f"Telegram respondeu: {resultado.status_code} - {resultado.text}")
    except Exception as e:
        print(f"Erro ao enviar para o Telegram: {e}")


def buscar_mensagens():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, texto, horario, repetir, ultimo_envio, imagem_url
        FROM mensagens
        ORDER BY horario, id
    """)
    mensagens = c.fetchall()
    conn.close()
    return mensagens


def buscar_mensagem(msg_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, texto, horario, repetir, ultimo_envio, imagem_url
        FROM mensagens
        WHERE id=?
    """, (msg_id,))
    mensagem = c.fetchone()
    conn.close()
    return mensagem


HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Painel de Mensagens</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #0f172a, #111827, #1e293b);
            color: white;
            padding: 24px;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
        }
        .topo {
            text-align: center;
            margin-bottom: 24px;
        }
        .topo h1 {
            margin: 0 0 10px;
            font-size: 34px;
        }
        .sub {
            color: #cbd5e1;
        }
        .badge {
            display: inline-block;
            margin-top: 12px;
            background: linear-gradient(135deg, #7c3aed, #2563eb);
            padding: 8px 14px;
            border-radius: 999px;
            font-size: 13px;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 22px;
        }
        .card {
            background: rgba(17, 24, 39, 0.94);
            border-radius: 22px;
            padding: 22px;
            box-shadow: 0 18px 40px rgba(0,0,0,0.35);
            border: 1px solid rgba(255,255,255,0.08);
        }
        h2 {
            margin-top: 0;
        }
        textarea, input[type="time"], input[type="text"] {
            width: 100%;
            border: none;
            border-radius: 14px;
            padding: 14px;
            margin-top: 8px;
            margin-bottom: 16px;
            background: #1f2937;
            color: white;
            font-size: 15px;
        }
        textarea {
            min-height: 140px;
            resize: vertical;
        }
        button, .btn {
            border: none;
            border-radius: 14px;
            padding: 12px 18px;
            font-weight: bold;
            cursor: pointer;
            color: white;
            text-decoration: none;
            display: inline-block;
        }
        .btn-green {
            background: linear-gradient(135deg, #22c55e, #16a34a);
        }
        .btn-blue {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
        }
        .btn-red {
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }
        .btn-gray {
            background: linear-gradient(135deg, #64748b, #475569);
        }
        .item {
            background: #0f172a;
            border-radius: 18px;
            padding: 16px;
            margin-bottom: 14px;
            border: 1px solid rgba(255,255,255,0.07);
        }
        .msg {
            white-space: pre-wrap;
            background: #111827;
            border-radius: 12px;
            padding: 12px;
            margin-top: 10px;
        }
        .tag {
            display: inline-block;
            font-size: 12px;
            padding: 5px 10px;
            border-radius: 999px;
            background: #1d4ed8;
            margin-right: 6px;
            margin-bottom: 6px;
        }
        .acoes {
            margin-top: 12px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .vazio {
            color: #94a3b8;
            text-align: center;
            padding: 20px 0;
        }
        .checkbox-wrap {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 18px;
            color: #e5e7eb;
        }
        .mini {
            color: #94a3b8;
            font-size: 13px;
        }
        @media (max-width: 900px) {
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="topo">
            <h1>📣 Painel de Mensagens</h1>
            <div class="sub">Texto, emojis, imagem por link e agendamento automático</div>
            <div class="badge">Horário atual do Brasil: {{ agora }}</div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>{{ titulo_form }}</h2>
                <form method="post" action="{{ action_form }}">
                    <label>Texto da mensagem</label>
                    <textarea name="texto" required>{{ mensagem[1] if mensagem else '' }}</textarea>

                    <label>Horário</label>
                    <input type="time" name="horario" value="{{ mensagem[2] if mensagem else '' }}" required>

                    <label>Link da imagem (opcional)</label>
                    <input type="text" name="imagem_url" placeholder="https://..." value="{{ mensagem[5] if mensagem else '' }}">

                    <div class="checkbox-wrap">
                        <input type="checkbox" name="repetir" id="repetir"
                        {% if not mensagem or mensagem[3] == 1 %}checked{% endif %}>
                        <label for="repetir" style="margin:0;">Repetir todos os dias</label>
                    </div>

                    <div class="acoes">
                        <button class="btn btn-green" type="submit">{{ botao_form }}</button>
                        {% if editando %}
                            <a class="btn btn-gray" href="{{ url_for('painel') }}">Cancelar</a>
                        {% endif %}
                    </div>
                </form>
            </div>

            <div class="card">
                <h2>🗂️ Mensagens cadastradas</h2>
                {% for m in mensagens %}
                    <div class="item">
                        <div class="tag">ID {{ m[0] }}</div>
                        <div class="tag">⏰ {{ m[2] }}</div>
                        <div class="tag">{{ "🔁 Repete" if m[3] == 1 else "1x Apenas" }}</div>
                        <div class="tag">{{ "🖼️ Com imagem" if m[5] else "💬 Só texto" }}</div>
                        <div class="mini">Último envio: {{ m[4] if m[4] else "-" }}</div>
                        <div class="msg">{{ m[1] }}</div>
                        {% if m[5] %}
                            <div class="mini" style="margin-top:10px;">Link da imagem: {{ m[5] }}</div>
                        {% endif %}
                        <div class="acoes">
                            <a class="btn btn-blue" href="{{ url_for('editar', msg_id=m[0]) }}">Editar</a>
                            <a class="btn btn-red" href="{{ url_for('excluir', msg_id=m[0]) }}">Excluir</a>
                        </div>
                    </div>
                {% else %}
                    <div class="vazio">Nenhuma mensagem cadastrada.</div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def painel():
    if request.method == "POST":
        texto = request.form["texto"].strip()
        horario = request.form["horario"].strip()
        imagem_url = request.form.get("imagem_url", "").strip()
        repetir = 1 if request.form.get("repetir") == "on" else 0

        if texto and horario:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO mensagens (texto, horario, repetir, imagem_url)
                VALUES (?, ?, ?, ?)
            """, (texto, horario, repetir, imagem_url))
            conn.commit()
            conn.close()

        return redirect(url_for("painel"))

    agora = datetime.now(FUSO).strftime("%H:%M")
    mensagens = buscar_mensagens()

    return render_template_string(
        HTML,
        agora=agora,
        mensagens=mensagens,
        titulo_form="✨ Nova mensagem",
        botao_form="Salvar mensagem",
        editando=False,
        mensagem=None,
        action_form=url_for("painel")
    )


@app.route("/editar/<int:msg_id>", methods=["GET", "POST"])
def editar(msg_id):
    mensagem = buscar_mensagem(msg_id)
    if not mensagem:
        return redirect(url_for("painel"))

    if request.method == "POST":
        texto = request.form["texto"].strip()
        horario = request.form["horario"].strip()
        imagem_url = request.form.get("imagem_url", "").strip()
        repetir = 1 if request.form.get("repetir") == "on" else 0

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE mensagens
            SET texto=?, horario=?, repetir=?, imagem_url=?
            WHERE id=?
        """, (texto, horario, repetir, imagem_url, msg_id))
        conn.commit()
        conn.close()

        return redirect(url_for("painel"))

    agora = datetime.now(FUSO).strftime("%H:%M")
    mensagens = buscar_mensagens()

    return render_template_string(
        HTML,
        agora=agora,
        mensagens=mensagens,
        titulo_form=f"✏️ Editando mensagem #{msg_id}",
        botao_form="Salvar alterações",
        editando=True,
        mensagem=mensagem,
        action_form=url_for("editar", msg_id=msg_id)
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

        print(f"Verificando mensagens... horário Brasil: {hora_atual}")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT id, texto, horario, repetir, ultimo_envio, imagem_url
            FROM mensagens
        """)
        mensagens = c.fetchall()

        for m in mensagens:
            msg_id, texto, horario, repetir, ultimo_envio, imagem_url = m

            if horario == hora_atual:
                if repetir == 1:
                    if ultimo_envio != data_hoje:
                        enviar_telegram(texto, imagem_url)
                        c.execute(
                            "UPDATE mensagens SET ultimo_envio=? WHERE id=?",
                            (data_hoje, msg_id)
                        )
                        print(f"Mensagem repetida enviada: {texto}")
                else:
                    if ultimo_envio == "":
                        enviar_telegram(texto, imagem_url)
                        c.execute(
                            "UPDATE mensagens SET ultimo_envio=? WHERE id=?",
                            (data_hoje, msg_id)
                        )
                        print(f"Mensagem única enviada: {texto}")

        conn.commit()
        conn.close()
        time.sleep(20)


threading.Thread(target=verificar_mensagens, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
