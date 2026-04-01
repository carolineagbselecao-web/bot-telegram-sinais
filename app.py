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
            imagem_url TEXT DEFAULT '',
            ativo INTEGER DEFAULT 1,
            ultimo_envio TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hora TEXT NOT NULL
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


def listar_mensagens():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, texto, imagem_url, ativo, ultimo_envio
        FROM mensagens
        ORDER BY id
    """)
    dados = c.fetchall()
    conn.close()
    return dados


def listar_horarios():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, hora
        FROM horarios
        ORDER BY hora
    """)
    dados = c.fetchall()
    conn.close()
    return dados


def buscar_mensagem(msg_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, texto, imagem_url, ativo, ultimo_envio
        FROM mensagens
        WHERE id=?
    """, (msg_id,))
    dado = c.fetchone()
    conn.close()
    return dado


def buscar_horario(horario_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, hora
        FROM horarios
        WHERE id=?
    """, (horario_id,))
    dado = c.fetchone()
    conn.close()
    return dado


def gerar_escala_do_dia():
    mensagens = [m for m in listar_mensagens() if m[3] == 1]
    horarios = listar_horarios()

    if not mensagens or not horarios:
        return []

    hoje = datetime.now(FUSO)
    indice_dia = hoje.toordinal()

    rotacao = indice_dia % len(horarios)
    horarios_rotacionados = horarios[rotacao:] + horarios[:rotacao]

    escala = []
    for i, mensagem in enumerate(mensagens):
        horario = horarios_rotacionados[i % len(horarios_rotacionados)]
        escala.append({
            "mensagem_id": mensagem[0],
            "texto": mensagem[1],
            "imagem_url": mensagem[2],
            "ultimo_envio": mensagem[4],
            "hora": horario[1]
        })

    return escala


def verificar_mensagens():
    while True:
        agora = datetime.now(FUSO)
        hora_atual = agora.strftime("%H:%M")
        data_hoje = agora.strftime("%Y-%m-%d")

        escala = gerar_escala_do_dia()
        print(f"Verificando mensagens... horário Brasil: {hora_atual}")
        print(f"Escala de hoje: {[f'{e['mensagem_id']}->{e['hora']}' for e in escala]}")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        for item in escala:
            msg_id = item["mensagem_id"]
            texto = item["texto"]
            imagem_url = item["imagem_url"]
            ultimo_envio = item["ultimo_envio"]
            hora_programada = item["hora"]

            if hora_programada == hora_atual and ultimo_envio != data_hoje:
                enviar_telegram(texto, imagem_url)
                c.execute("""
                    UPDATE mensagens
                    SET ultimo_envio=?
                    WHERE id=?
                """, (data_hoje, msg_id))
                print(f"Mensagem enviada: ID {msg_id} às {hora_programada}")

        conn.commit()
        conn.close()

        time.sleep(20)


HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Painel Rotativo</title>
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
            margin: 0 0 8px 0;
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
            margin-top: 22px;
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
            min-height: 130px;
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

        .btn-green { background: linear-gradient(135deg, #22c55e, #16a34a); }
        .btn-blue { background: linear-gradient(135deg, #3b82f6, #2563eb); }
        .btn-red { background: linear-gradient(135deg, #ef4444, #dc2626); }
        .btn-gray { background: linear-gradient(135deg, #64748b, #475569); }

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

        .mini {
            color: #94a3b8;
            font-size: 13px;
            margin-top: 8px;
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
                <h2>{{ titulo_form }}</h2>
                <form method="post" action="{{ action_form }}">
                    <label>Texto da mensagem</label>
                    <textarea name="texto" required>{{ mensagem[1] if mensagem else '' }}</textarea>

                    <label>Link da imagem (opcional)</label>
                    <input type="text" name="imagem_url" placeholder="https://..." value="{{ mensagem[2] if mensagem else '' }}">

                    <div class="acoes">
                        <button class="btn btn-green" type="submit">{{ botao_form }}</button>
                        {% if editando %}
                            <a class="btn btn-gray" href="{{ url_for('painel') }}">Cancelar</a>
                        {% endif %}
                    </div>
                </form>
            </div>

            <div class="card">
                <h2>⏰ Novo horário</h2>
                <form method="post" action="{{ url_for('novo_horario') }}">
                    <label>Horário</label>
                    <input type="time" name="hora" required>
                    <button class="btn btn-green" type="submit">Salvar horário</button>
                </form>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>🗂️ Mensagens cadastradas</h2>
                {% for m in mensagens %}
                    <div class="item">
                        <div class="tag">ID {{ m[0] }}</div>
                        <div class="tag">{{ "🖼️ Com imagem" if m[2] else "💬 Só texto" }}</div>
                        <div class="tag">{{ "✅ Ativa" if m[3] == 1 else "⛔ Inativa" }}</div>
                        <div class="mini">Último envio: {{ m[4] if m[4] else "-" }}</div>
                        <div class="msg">{{ m[1] }}</div>
                        {% if m[2] %}
                            <div class="mini">Imagem: {{ m[2] }}</div>
                        {% endif %}
                        <div class="acoes">
                            <a class="btn btn-blue" href="{{ url_for('editar_mensagem', msg_id=m[0]) }}">Editar</a>
                            <a class="btn btn-red" href="{{ url_for('excluir_mensagem', msg_id=m[0]) }}">Excluir</a>
                        </div>
                    </div>
                {% else %}
                    <div class="vazio">Nenhuma mensagem cadastrada.</div>
                {% endfor %}
            </div>

            <div class="card">
                <h2>🕒 Horários cadastrados</h2>
                {% for h in horarios %}
                    <div class="item">
                        <div class="tag">ID {{ h[0] }}</div>
                        <div class="msg">{{ h[1] }}</div>
                        <div class="acoes">
                            <a class="btn btn-blue" href="{{ url_for('editar_horario', horario_id=h[0]) }}">Editar</a>
                            <a class="btn btn-red" href="{{ url_for('excluir_horario', horario_id=h[0]) }}">Excluir</a>
                        </div>
                    </div>
                {% else %}
                    <div class="vazio">Nenhum horário cadastrado.</div>
                {% endfor %}
            </div>
        </div>

        <div class="card">
            <h2>📅 Escala de hoje</h2>
            {% for e in escala %}
                <div class="item">
                    <div class="tag">Mensagem ID {{ e.mensagem_id }}</div>
                    <div class="tag">⏰ {{ e.hora }}</div>
                    <div class="msg">{{ e.texto }}</div>
                </div>
            {% else %}
                <div class="vazio">Cadastre mensagens e horários para gerar a escala.</div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def painel():
    if request.method == "POST":
        texto = request.form["texto"].strip()
        imagem_url = request.form.get("imagem_url", "").strip()

        if texto:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO mensagens (texto, imagem_url, ativo)
                VALUES (?, ?, 1)
            """, (texto, imagem_url))
            conn.commit()
            conn.close()

        return redirect(url_for("painel"))

    agora = datetime.now(FUSO).strftime("%H:%M")
    mensagens = listar_mensagens()
    horarios = listar_horarios()
    escala = gerar_escala_do_dia()

    return render_template_string(
        HTML,
        agora=agora,
        mensagens=mensagens,
        horarios=horarios,
        escala=escala,
        titulo_form="✨ Nova mensagem",
        botao_form="Salvar mensagem",
        editando=False,
        mensagem=None,
        action_form=url_for("painel")
    )


@app.route("/mensagem/editar/<int:msg_id>", methods=["GET", "POST"])
def editar_mensagem(msg_id):
    mensagem = buscar_mensagem(msg_id)
    if not mensagem:
        return redirect(url_for("painel"))

    if request.method == "POST":
        texto = request.form["texto"].strip()
        imagem_url = request.form.get("imagem_url", "").strip()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE mensagens
            SET texto=?, imagem_url=?
            WHERE id=?
        """, (texto, imagem_url, msg_id))
        conn.commit()
        conn.close()

        return redirect(url_for("painel"))

    agora = datetime.now(FUSO).strftime("%H:%M")
    mensagens = listar_mensagens()
    horarios = listar_horarios()
    escala = gerar_escala_do_dia()

    return render_template_string(
        HTML,
        agora=agora,
        mensagens=mensagens,
        horarios=horarios,
        escala=escala,
        titulo_form=f"✏️ Editando mensagem #{msg_id}",
        botao_form="Salvar alterações",
        editando=True,
        mensagem=mensagem,
        action_form=url_for("editar_mensagem", msg_id=msg_id)
    )


@app.route("/mensagem/excluir/<int:msg_id>")
def excluir_mensagem(msg_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM mensagens WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("painel"))


@app.route("/horario/novo", methods=["POST"])
def novo_horario():
    hora = request.form["hora"].strip()
    if hora:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO horarios (hora) VALUES (?)", (hora,))
        conn.commit()
        conn.close()

    return redirect(url_for("painel"))


@app.route("/horario/editar/<int:horario_id>", methods=["GET", "POST"])
def editar_horario(horario_id):
    horario = buscar_horario(horario_id)
    if not horario:
        return redirect(url_for("painel"))

    if request.method == "POST":
        hora = request.form["hora"].strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE horarios SET hora=? WHERE id=?", (hora, horario_id))
        conn.commit()
        conn.close()
        return redirect(url_for("painel"))

    html_editar_horario = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Editar horário</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #0f172a;
                color: white;
                padding: 30px;
            }
            .box {
                max-width: 500px;
                margin: 0 auto;
                background: #111827;
                padding: 24px;
                border-radius: 20px;
            }
            input, button, a {
                width: 100%;
                padding: 14px;
                border: none;
                border-radius: 12px;
                margin-top: 12px;
                font-size: 15px;
                box-sizing: border-box;
            }
            input {
                background: #1f2937;
                color: white;
            }
            button {
                background: #22c55e;
                color: white;
                font-weight: bold;
                cursor: pointer;
            }
            a {
                display: inline-block;
                background: #64748b;
                color: white;
                text-decoration: none;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>✏️ Editar horário</h2>
            <form method="post">
                <input type="time" name="hora" value="{{ horario[1] }}" required>
                <button type="submit">Salvar</button>
                <a href="{{ url_for('painel') }}">Cancelar</a>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_editar_horario, horario=horario)


@app.route("/horario/excluir/<int:horario_id>")
def excluir_horario(horario_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM horarios WHERE id=?", (horario_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("painel"))


threading.Thread(target=verificar_mensagens, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
