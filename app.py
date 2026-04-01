from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3
import threading
import time
from datetime import datetime
import pytz
import os
import requests
import uuid

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)
FUSO = pytz.timezone("America/Sao_Paulo")
DB_PATH = "/tmp/database.db"
UPLOAD_DIR = "/tmp/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            horario TEXT,
            repetir INTEGER DEFAULT 1,
            ultimo_envio TEXT DEFAULT '',
            imagem_path TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()


init_db()


def enviar_telegram(texto, imagem_path=""):
    if not TOKEN or not CHAT_ID:
        print("TOKEN ou CHAT_ID não configurados.")
        return

    try:
        if imagem_path and os.path.exists(imagem_path):
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            with open(imagem_path, "rb") as foto:
                files = {"photo": foto}
                data = {
                    "chat_id": CHAT_ID,
                    "caption": texto
                }
                resultado = requests.post(url, data=data, files=files, timeout=30)
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
        SELECT id, titulo, horario, repetir, ultimo_envio, imagem_path
        FROM mensagens
        ORDER BY horario
    """)
    mensagens = c.fetchall()
    conn.close()
    return mensagens


def buscar_mensagem_por_id(msg_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, titulo, horario, repetir, ultimo_envio, imagem_path
        FROM mensagens
        WHERE id=?
    """, (msg_id,))
    mensagem = c.fetchone()
    conn.close()
    return mensagem


def salvar_imagem(upload):
    if upload and upload.filename:
        extensao = os.path.splitext(upload.filename)[1].lower()
        nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
        imagem_path = os.path.join(UPLOAD_DIR, nome_arquivo)
        upload.save(imagem_path)
        return imagem_path
    return ""


HTML_BASE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Painel Profissional</title>
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
            margin-bottom: 28px;
        }

        .topo h1 {
            margin: 0 0 10px 0;
            font-size: 34px;
        }

        .sub {
            color: #cbd5e1;
            font-size: 15px;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 22px;
        }

        .card {
            background: rgba(17, 24, 39, 0.92);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 22px;
            padding: 24px;
            box-shadow: 0 18px 40px rgba(0,0,0,0.35);
        }

        .card h2 {
            margin-top: 0;
            font-size: 22px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #e5e7eb;
        }

        input[type="text"],
        input[type="time"],
        textarea,
        input[type="file"] {
            width: 100%;
            border: none;
            border-radius: 14px;
            padding: 14px;
            margin-bottom: 16px;
            background: #1f2937;
            color: white;
            font-size: 15px;
        }

        textarea {
            min-height: 150px;
            resize: vertical;
        }

        .linha-acoes {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 10px;
        }

        .btn {
            display: inline-block;
            border: none;
            border-radius: 14px;
            padding: 12px 18px;
            font-weight: bold;
            cursor: pointer;
            text-decoration: none;
            color: white;
        }

        .btn-salvar {
            background: linear-gradient(135deg, #22c55e, #16a34a);
        }

        .btn-editar {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
        }

        .btn-excluir {
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }

        .btn-cancelar {
            background: linear-gradient(135deg, #64748b, #475569);
        }

        .checkbox-wrap {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 18px;
            color: #e5e7eb;
        }

        .lista {
            margin-top: 10px;
        }

        .item {
            background: #0f172a;
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 16px;
        }

        .item-topo {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: start;
            margin-bottom: 10px;
        }

        .tag {
            display: inline-block;
            background: #1d4ed8;
            color: white;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 12px;
            margin-right: 6px;
            margin-bottom: 6px;
        }

        .texto-msg {
            white-space: pre-wrap;
            background: #111827;
            border-radius: 14px;
            padding: 14px;
            color: #f8fafc;
            margin-top: 12px;
        }

        .mini {
            color: #94a3b8;
            font-size: 13px;
        }

        .destaque {
            background: linear-gradient(135deg, #7c3aed, #2563eb);
            padding: 10px 14px;
            border-radius: 999px;
            display: inline-block;
            font-size: 13px;
            margin-top: 10px;
        }

        .preview {
            margin-top: 12px;
            font-size: 14px;
            color: #cbd5e1;
        }

        .vazio {
            color: #94a3b8;
            text-align: center;
            padding: 30px 10px;
        }

        @media (max-width: 900px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="topo">
            <h1>📣 Painel Profissional de Mensagens</h1>
            <div class="sub">Gerencie mensagens automáticas com texto, emojis, imagem e edição</div>
            <div class="destaque">Horário atual do Brasil: {{ agora }}</div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>{{ titulo_form }}</h2>
                <form method="post" enctype="multipart/form-data" action="{{ action_form }}">
                    <label>Texto da mensagem</label>
                    <textarea name="titulo" placeholder="Exemplo:
🔥 NOVIDADE LIBERADA
📢 Mensagem importante
💎 Continue acompanhando" required>{{ mensagem_form[1] if mensagem_form else '' }}</textarea>

                    <label>Horário</label>
                    <input name="horario" type="time" value="{{ mensagem_form[2] if mensagem_form else '' }}" required>

                    <label>Imagem / banner</label>
                    <input name="imagem" type="file" accept="image/*">

                    <div class="checkbox-wrap">
                        <input type="checkbox" name="repetir" id="repetir"
                        {% if not mensagem_form or mensagem_form[3] == 1 %}checked{% endif %}>
                        <label for="repetir" style="margin:0;">Repetir todos os dias</label>
                    </div>

                    {% if mensagem_form and mensagem_form[5] %}
                        <div class="preview">🖼️ Esta mensagem já possui uma imagem salva.</div>
                    {% endif %}

                    <div class="linha-acoes">
                        <button class="btn btn-salvar" type="submit">
                            {{ texto_botao }}
                        </button>

                        {% if editando %}
                            <a class="btn btn-cancelar" href="{{ url_for('painel') }}">Cancelar edição</a>
                        {% endif %}
                    </div>
                </form>
            </div>

            <div class="card">
                <h2>🗂️ Mensagens cadastradas</h2>

                <div class="lista">
                    {% for m in mensagens %}
                        <div class="item">
                            <div class="item-topo">
                                <div>
                                    <div class="tag">ID {{ m[0] }}</div>
                                    <div class="tag">⏰ {{ m[2] }}</div>
                                    <div class="tag">{{ "🔁 Repete" if m[3] == 1 else "1x Apenas" }}</div>
                                    <div class="tag">{{ "🖼️ Com imagem" if m[5] else "💬 Só texto" }}</div>
                                </div>
                                <div class="mini">
                                    Último envio: {{ m[4] if m[4] else "-" }}
                                </div>
                            </div>

                            <div class="texto-msg">{{ m[1] }}</div>

                            <div class="linha-acoes">
                                <a class="btn btn-editar" href="{{ url_for('editar', msg_id=m[0]) }}">Editar</a>
                                <a class="btn btn-excluir" href="{{ url_for('excluir', msg_id=m[0]) }}">Excluir</a>
                            </div>
                        </div>
                    {% else %}
                        <div class="vazio">Nenhuma mensagem cadastrada ainda.</div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def painel():
    if request.method == "POST":
        titulo = request.form["titulo"].strip()
        horario = request.form["horario"].strip()
        repetir = 1 if request.form.get("repetir") == "on" else 0
        imagem = request.files.get("imagem")
        imagem_path = salvar_imagem(imagem)

        if titulo and horario:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO mensagens (titulo, horario, repetir, imagem_path) VALUES (?, ?, ?, ?)",
                (titulo, horario, repetir, imagem_path)
            )
            conn.commit()
            conn.close()

        return redirect(url_for("painel"))

    mensagens = buscar_mensagens()
    agora = datetime.now(FUSO).strftime("%H:%M")

    return render_template_string(
        HTML_BASE,
        mensagens=mensagens,
        agora=agora,
        titulo_form="✨ Nova mensagem",
        texto_botao="Salvar mensagem",
        editando=False,
        mensagem_form=None,
        action_form=url_for("painel")
    )


@app.route("/editar/<int:msg_id>", methods=["GET", "POST"])
def editar(msg_id):
    mensagem = buscar_mensagem_por_id(msg_id)

    if not mensagem:
        return redirect(url_for("painel"))

    if request.method == "POST":
        titulo = request.form["titulo"].strip()
        horario = request.form["horario"].strip()
        repetir = 1 if request.form.get("repetir") == "on" else 0
        imagem = request.files.get("imagem")

        imagem_path = mensagem[5]
        nova_imagem = salvar_imagem(imagem)

        if nova_imagem:
            if imagem_path and os.path.exists(imagem_path):
                try:
                    os.remove(imagem_path)
                except:
                    pass
            imagem_path = nova_imagem

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE mensagens
            SET titulo=?, horario=?, repetir=?, imagem_path=?
            WHERE id=?
        """, (titulo, horario, repetir, imagem_path, msg_id))
        conn.commit()
        conn.close()

        return redirect(url_for("painel"))

    mensagens = buscar_mensagens()
    agora = datetime.now(FUSO).strftime("%H:%M")

    return render_template_string(
        HTML_BASE,
        mensagens=mensagens,
        agora=agora,
        titulo_form=f"✏️ Editando mensagem #{msg_id}",
        texto_botao="Salvar alterações",
        editando=True,
        mensagem_form=mensagem,
        action_form=url_for("editar", msg_id=msg_id)
    )


@app.route("/excluir/<int:msg_id>")
def excluir(msg_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT imagem_path FROM mensagens WHERE id=?", (msg_id,))
    item = c.fetchone()

    if item and item[0] and os.path.exists(item[0]):
        try:
            os.remove(item[0])
        except:
            pass

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
            SELECT id, titulo, horario, repetir, ultimo_envio, imagem_path
            FROM mensagens
        """)
        mensagens = c.fetchall()

        for m in mensagens:
            msg_id, titulo, horario, repetir, ultimo_envio, imagem_path = m

            if horario == hora_atual:
                if repetir == 1:
                    if ultimo_envio != data_hoje:
                        enviar_telegram(titulo, imagem_path)
                        c.execute(
                            "UPDATE mensagens SET ultimo_envio=? WHERE id=?",
                            (data_hoje, msg_id)
                        )
                        print(f"Mensagem repetida enviada: {titulo}")
                else:
                    if ultimo_envio == "":
                        enviar_telegram(titulo, imagem_path)
                        c.execute(
                            "UPDATE mensagens SET ultimo_envio=? WHERE id=?",
                            (data_hoje, msg_id)
                        )
                        print(f"Mensagem única enviada: {titulo}")

        conn.commit()
        conn.close()
        time.sleep(20)


threading.Thread(target=verificar_mensagens, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
