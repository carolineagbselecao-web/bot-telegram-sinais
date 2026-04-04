<h2>🎮 Cadastrar Jogo</h2>
            <form method="post" action="/">
                <label>Escolha o jogo:</label>
                <select name="nome_jogo">
                    {% for j in jogos_lista %}
                    <option value="{{ j }}">{{ j }}</option>
                    {% endfor %}
                </select>
                <label>Link da imagem (opcional):</label>
                <input name="imagem_url" placeholder="https://i.imgur.com/...">
                <button class="btn">💾 Salvar Jogo</button>
            </form>
            <div class="dica">💡 Estratégia gerada automaticamente e varia a cada envio!</div>
        </div>
        <div class="card">
            <h2>⏰ Cadastrar Horário</h2>
            <form method="post" action="/horario/novo">
                <label>Horário (HH:MM):</label>
                <input name="hora" placeholder="Ex: 20:00" maxlength="5">
                <button class="btn">➕ Adicionar</button>
            </form>
            <div class="tags">
                <p style="color:#f5c542;font-weight:bold;margin-bottom:8px;">🔄 Rotação de hoje:</p>
                {% for h in horarios_hoje %}<span>{{ h }}</span>
                {% else %}<p style="color:#aaa;font-size:13px;">Nenhum horário ainda</p>{% endfor %}
            </div>
            <table style="margin-top:15px;">
                <tr><th>Horário</th><th>Excluir</th></tr>
                {% for h in todos_horarios %}
                <tr><td>{{ h[1] }}</td><td><a class="del" href="/horario/excluir/{{ h[0] }}">🗑️</a></td></tr>
                {% endfor %}
            </table>
        </div>
    </div>
    <div class="card secao">
        <h2>📋 Jogos cadastrados ({{ mensagens|length }})</h2>
        <table>
            <tr><th>#</th><th>Jogo</th><th>Img</th><th>Último envio</th><th>Ação</th></tr>
            {% for m in mensagens %}
            <tr>
                <td>{{ m[0] }}</td>
                <td>{{ m[1] }}</td>
                <td>{{ '✅' if m[2] else '❌' }}</td>
                <td>{{ m[3] or 'Nunca' }}</td>
                <td><a class="del" href="/excluir/{{ m[0] }}">🗑️</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def painel():
    if request.method == "POST":
        nome_jogo = request.form["nome_jogo"]
        imagem_url = request.form.get("imagem_url", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO mensagens (nome_jogo, imagem_url) VALUES (?, ?)", (nome_jogo, imagem_url))
        conn.commit()
        conn.close()
        return redirect(url_for("painel"))
    agora = datetime.now(FUSO).strftime("%H:%M")
    return render_template_string(HTML,
        agora=agora,
        mensagens=buscar_mensagens(),
        todos_horarios=buscar_horarios(),
        horarios_hoje=horarios_hoje(),
        jogos_lista=sorted(JOGOS.keys())
    )


@app.route("/excluir/<int:msg_id>")
def excluir(msg_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM mensagens WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("painel"))


@app.route("/horario/novo", methods=["POST"])
def novo_horario():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO horarios (hora) VALUES (?)", (request.form["hora"],))
    conn.commit()
    conn.close()
    return redirect(url_for("painel"))


@app.route("/horario/excluir/<int:h_id>")
def excluir_horario(h_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM horarios WHERE id=?", (h_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("painel"))


def verificar_mensagens():
    while True:
    agora = datetime.now(FUSO)
        hora_atual = agora.strftime("%H:%M")
        data_hoje = agora.strftime("%Y-%m-%d")
        horarios = horarios_hoje()
        print(f"Verificando... {hora_atual} | Horários: {horarios}")
        if horarios:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, nome_jogo, imagem_url, ultimo_envio FROM mensagens")
            for i, m in enumerate(c.fetchall()):
                msg_id, nome_jogo, imagem_url, ultimo_envio = m
                if i < len(horarios) and horarios[i] == hora_atual and ultimo_envio != data_hoje:
                    texto = gerar_mensagem(nome_jogo)
                    enviar_telegram(texto, imagem_url)
                    c.execute("UPDATE mensagens SET ultimo_envio=? WHERE id=?", (data_hoje, msg_id))
                    print(f"Enviado: {nome_jogo}")
            conn.commit()
            conn.close()
        time.sleep(20)


threading.Thread(target=verificar_mensagens, daemon=True).start()

if name == "main":
    app.run(host="0.0.0.0", port=10000)
