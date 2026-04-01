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
            texto TEXT NOT NULL,
            imagem_path TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hora TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS envios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_envio TEXT NOT NULL,
            mensagem_id INTEGER NOT NULL,
            horario TEXT NOT NULL,
            enviado INTEGER DEFAULT 0
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


def salvar_imagem(upload):
    if upload and upload.filename:
        extensao = os.path.splitext(upload.filename)[1].lower()
        nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
        imagem_path = os.path.join(UPLOAD_DIR, nome_arquivo)
        upload.save(imagem_path)
        return imagem_path
    return ""


def get_conexao():
    return sqlite3.connect(DB_PATH)


def listar_mensagens():
    conn = get_conexao()
    c = conn.cursor()
    c.execute("SELECT id, texto, imagem_path FROM mensagens ORDER BY id")
    dados = c.fetchall()
    conn.close()
    return dados


def listar_horarios():
    conn = get_conexao()
    c = conn.cursor()
    c.execute("SELECT id, hora FROM horarios ORDER BY hora")
    dados = c.fetchall()
    conn.close()
    return dados


def gerar_escala_do_dia():
    agora = datetime.now(FUSO)
    data_hoje = agora.strftime("%Y-%m-%d")
    dia_indice = agora.toordinal()

    conn = get_conexao()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM envios WHERE data_envio=?", (data_hoje,))
    ja_existe = c.fetchone()[0]

    if ja_existe > 0:
        conn.close()
        return

    c.execute("SELECT id, texto, imagem_path FROM mensagens ORDER BY id")
    mensagens = c.fetchall()

    c.execute("SELECT hora FROM horarios ORDER BY hora")
    horarios = [h[0] for h in c.fetchall()]

    if not mensagens or not horarios:
        conn.close()
        return

    deslocamento = dia_indice % len(horarios)

    for i, msg in enumerate(mensagens):
        mensagem_id = msg[0]
        horario_escolhido = horarios[(i + deslocamento) % len(horarios)]
        c.execute("""
            INSERT INTO envios (data_envio, mensagem_id, horario, enviado)
            VALUES (?, ?, ?, 0)
        """, (data_hoje, mensagem_id, horario_escolhido))

    conn.commit()
    conn.close()
    print(f"Escala do dia gerada para {data_hoje}")


def buscar_escala_do_dia():
    agora = datetime.now(FUSO)
    data_hoje = agora.strftime("%Y-%m-%d")

    conn = get_conexao()
    c = conn.cursor()
    c.execute("""
        SELECT e.id, e.horario, e.enviado, m.texto, m.imagem_path, m.id
        FROM envios e
        JOIN mensagens m ON m.id = e.mensagem_id
        WHERE e.data_envio=?
        ORDER BY e.horario
    """, (data_hoje,))
    dados = c.fetchall()
    conn.close()
    return dados


HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Painel Rotativo Diário</title>
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
            max-width: 1200px;
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
        textarea, input[type="time"], input[type="file"] {
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
        button {
            border: none;
            border-radius: 14px;
            padding: 12px 18px;
            font-weight: bold;
            cursor: pointer;
            color: white;
            background: linear-gradient(135deg, #22c55e, #16a34a);
        }
        .btn-red {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            text-decoration: none;
            padding: 10px 14px;
            border-radius: 12px;
            color: white;
            display: inline-block;
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
        .escala-ok {
            color: #86efac;
            font-weight: bold;
        }
        .escala-pendente {
            color: #fcd34d;
            font-weight: bold;
        }
        .acoes {
            margin-top: 10px;
        }
        .vazio {
            color: #94a3b8;
            text-align: center;
            padding: 20px 0;
        }
        @media (max-width: 900px) {
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="topo">
            <h1>🔄 Painel Rotativo Diário</h1>
            <div class="sub">As mensagens mudam de horário automaticamente a cada dia</div>
            <div class="badge">Horário atual do Brasil: {{ agora }}</div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>📝 Nova mensagem</h2>
                <form method="post" action="/nova_mensagem" enctype="multipart/form-data">
                    <label>Texto</label>
                    <textarea name="texto" placeholder="Digite sua mensagem com emojis" required></textarea>

                    <label>Imagem / banner</label>
                    <input type="file" name="imagem" accept="image/*">

                    <button type="submit">Salvar mensagem</button>
                </form>
            </div>

            <div class="card">
                <h2>⏰ Novo horário</h2>
                <form method="post" action="/novo_horario">
                    <label>Horário</label>
                    <input type="time" name="hora" required>
                    <button type="submit">Salvar horário</button>
                </form>
            </div>
        </div>

        <div class="grid" style="margin-top:22px;">
            <div class="card">
                <h2>📚 Lista de mensagens</h2>
                {% for m in mensagens %}
                    <div class="item">
                        <div class="tag">ID {{ m[0] }}</div>
                        <div class="tag">{{ "🖼️ Com imagem" if m[2] else "💬 Só texto" }}</div>
                        <div class="msg">{{ m[1] }}</div>
                        <div class="acoes">
                            <a class="btn-red" href="/excluir_mensagem/{{ m[0] }}">Excluir</a>
                        </div>
                    </div>
                {% else %}
                    <div class="vazio">Nenhuma mensagem cadastrada.</div>
                {% endfor %}
            </div>

            <div class="card">
                <h2>🕒 Lista de horários</h2>
                {% for h in horarios %}
                    <div class="item">
                        <div class="tag">Horário</div>
                        <div style="font-size:22px; font-weight:bold;">{{ h[1] }}</div>
                        <div class="acoes">
                            <a class="btn-red" href="/excluir_horario/{{ h[0] }}">Excluir</a>
                        </div>
                    </div>
                {% else %}
                    <div class="vazio">Nenhum horário cadastrado.</div>
                {% endfor %}
            </div>
        </div>

        <div class="card" style="margin-top:22px;">
            <h2>📅 Escala de hoje</h2>
            {% for e in escala %}
                <div class="item">
                    <div class="tag">Mensagem ID {{ e[5] }}</div>
                    <div class="tag">⏰ {{ e[1] }}</div>
                    <div class="tag">{{ "✅ Enviado" if e[2] == 1 else "⌛ Pendente" }}</div>
                    <div class="{{ 'escala-ok' if e[2] == 1 else 'escala-pendente' }}">
                        {{ "Enviado" if e[2] == 1 else "Aguardando horário" }}
                    </div>
                    <div class="msg">{{ e[3] }}</div>
                </div>
            {% else %}
                <div class="vazio">Cadastre mensagens e horários para gerar a escala do dia.</div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def painel():
    gerar_escala_do_dia()
    agora = datetime.now(FUSO).strftime("%H:%M")
    mensagens = listar_mensagens()
    horarios = listar_horarios()
    escala = buscar_escala_do_dia()

    return render_template_string(
        HTML,
        agora=agora,
        mensagens=mensagens,
        horarios=horarios,
        escala=escala
    )


@app.route("/nova_mensagem", methods=["POST"])
def nova_mensagem():
    texto = request.form["texto"].strip()
    imagem = request.files.get("imagem")
    imagem_path = salvar_imagem(imagem)

    if texto:
        conn = get_conexao()
        c = conn.cursor()
        c.execute(
            "INSERT INTO mensagens (texto, imagem_path) VALUES (?, ?)",
            (texto, imagem_path)
        )
        conn.commit()
        conn.close()

    return redirect(url_for("painel"))


@app.route("/novo_horario", methods=["POST"])
def novo_horario():
    hora = request.form["hora"].strip()

    if hora:
        conn = get_conexao()
        c = conn.cursor()
        c.execute("INSERT INTO horarios (hora) VALUES (?)", (hora,))
        conn.commit()
        conn.close()

    return redirect(url_for("painel"))


@app.route("/excluir_mensagem/<int:item_id>")
def excluir_mensagem(item_id):
    conn = get_conexao()
    c = conn.cursor()

    c.execute("SELECT imagem_path FROM mensagens WHERE id=?", (item_id,))
    item = c.fetchone()
    if item and item[0] and os.path.exists(item[0]):
        try:
            os.remove(item[0])
        except:
            pass

    c.execute("DELETE FROM mensagens WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("painel"))


@app.route("/excluir_horario/<int:item_id>")
def excluir_horario(item_id):
    conn = get_conexao()
    c = conn.cursor()
    c.execute("DELETE FROM horarios WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("painel"))


def verificar_envios():
    while True:
        gerar_escala_do_dia()

        agora = datetime.now(FUSO)
        data_hoje = agora.strftime("%Y-%m-%d")
        hora_atual = agora.strftime("%H:%M")
        print(f"Verificando envios... {data_hoje} {hora_atual}")

        conn = get_conexao()
        c = conn.cursor()
        c.execute("""
            SELECT e.id, e.mensagem_id, e.horario, e.enviado, m.texto, m.imagem_path
            FROM envios e
            JOIN mensagens m ON m.id = e.mensagem_id
            WHERE e.data_envio=? AND e.horario=? AND e.enviado=0
        """, (data_hoje, hora_atual))

        pendentes = c.fetchall()

        for p in pendentes:
            envio_id, mensagem_id, horario, enviado, texto, imagem_path = p
            enviar_telegram(texto, imagem_path)
            c.execute("UPDATE envios SET enviado=1 WHERE id=?", (envio_id,))
            print(f"Mensagem {mensagem_id} enviada às {horario}")

        conn.commit()
        conn.close()
        time.sleep(20)


threading.Thread(target=verificar_envios, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
