import os
import re
import secrets
import configuracao  # carrega .env ANTES de importar assistente e ler DB_CONFIG
from datetime import date, datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, session, redirect
from werkzeug.utils import secure_filename
from assistente import responder_com_plano, risco_de_desistir
import catalogo
import biblioteca_exercicios
import plano_kiara
from auth_utils import validar_cadastro, gerar_hash_senha, verificar_senha
import mysql.connector
from mysql.connector import Error

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
UPLOAD_FOLDER = os.path.join(PUBLIC_DIR, "uploads", "avatars")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'avif'}

app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path="")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def login_obrigatorio(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if "usuario" not in session:
            return jsonify({"erro": "Não autenticado."}), 401
        return f(*args, **kwargs)
    return decorada


DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "database": os.environ.get("DB_NAME", "fitfatec"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
}


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def garantir_tabela_chat():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_mensagens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_aluno INT NOT NULL,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                eh_treino TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_chat_aluno (id_aluno)
            )
            """
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


try:
    garantir_tabela_chat()
except Exception:
    pass


def salvar_aluno_no_banco(nome, email, senha_hash):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_aluno FROM aluno WHERE email = %s", (email,))
        if cursor.fetchone():
            raise ValueError("E-mail já cadastrado.")

        cursor.execute(
            """
            INSERT INTO aluno (nome, email, senha_hash, papel, created_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (nome, email, senha_hash, "aluno"),
        )
        id_aluno = cursor.lastrowid
        matricula = f"{date.today().year}{id_aluno:04d}"
        cursor.execute("UPDATE aluno SET matricula = %s WHERE id_aluno = %s", (matricula, id_aluno))
        conn.commit()
        return id_aluno
    finally:
        cursor.close()
        conn.close()


def limpar_aluno(dados):
    try:
        return {
            "idade": int(dados["idade"]),
            "objetivo": str(dados["objetivo"]),
            "nivel": str(dados["nivel"]),
            "frequencia_semanal": int(dados["frequencia_semanal"]),
            "meses_matricula": int(dados["meses_matricula"]),
            "faltas_ultimo_mes": int(dados["faltas_ultimo_mes"]),
        }
    except (KeyError, ValueError, TypeError):
        return None


def _serializar_agendamento(ag):
    if not ag:
        return None
    copia = dict(ag)
    if isinstance(copia.get("data_aula"), (date, datetime)):
        copia["data_aula"] = copia["data_aula"].strftime("%Y-%m-%d")
    if isinstance(copia.get("horario"), timedelta):
        total_seg = int(copia["horario"].total_seconds())
        horas, resto = divmod(total_seg, 3600)
        minutos = resto // 60
        copia["horario"] = f"{horas:02d}:{minutos:02d}"
    return copia


@app.get("/health")
def health():
    return jsonify({"status": "ok", "mensagem": "Servidor Flask está funcionando"})


@app.get("/")
def pagina_inicial():
    if "usuario" not in session:
        return redirect("/pages/conta.html")
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.get("/conta")
@app.get("/teste-auth")
def pagina_conta():
    return send_from_directory(os.path.join(PUBLIC_DIR, "pages"), "conta.html")


@app.post("/cadastro")
@app.post("/api/cadastro")
def cadastro():
    corpo = request.get_json(silent=True) or {}
    nome = corpo.get("nome", "")
    email = corpo.get("email", "")
    senha = corpo.get("senha", "")

    valido, mensagem = validar_cadastro(nome, email, senha)
    if not valido:
        return jsonify({"erro": mensagem}), 400

    senha_hash = gerar_hash_senha(senha)

    try:
        salvar_aluno_no_banco(nome, email, senha_hash)
    except ValueError as e:
        return jsonify({"erro": str(e)}), 409
    except Error:
        return jsonify({"erro": "Erro ao salvar aluno no banco."}), 500

    return jsonify({"mensagem": "Cadastro realizado com sucesso."}), 201


def formatar_aluno_publico(aluno):
    if not aluno:
        return None
    copia = dict(aluno)
    copia.pop("senha_hash", None)
    copia.pop("token_recuperacao", None)
    copia.pop("token_expiracao", None)
    copia["id"] = copia.get("id_aluno")
    copia["ativo"] = not copia.get("desistiu", False)
    copia["telefone"] = copia.get("telefone") or ""
    copia["avatar_url"] = copia.get("avatar_url") or ""
    copia["treinos_semana"] = copia.get("treinos_semana") or 3
    copia["modalidade_principal"] = copia.get("modalidade_principal") or "Musculação"
    copia["notificacoes"] = bool(copia.get("notificacoes", 1))
    copia["acessibilidade"] = copia.get("acessibilidade") or "padrao"
    copia["tema"] = copia.get("tema") or "escuro"
    return copia


def buscar_aluno_por_email(email):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM aluno WHERE email = %s", (email,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def buscar_aluno_por_identificador(identificador):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM aluno WHERE email = %s OR matricula = %s",
            (identificador, identificador)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def buscar_aluno_por_id(id_aluno):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM aluno WHERE id_aluno = %s", (id_aluno,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


@app.post("/login")
@app.post("/api/login")
def login():
    corpo = request.get_json(silent=True) or {}
    identificador = (corpo.get("identificador") or corpo.get("email") or corpo.get("matricula") or "").strip()
    senha = corpo.get("senha", "")

    if not identificador or not senha:
        return jsonify({"erro": "Matrícula/e-mail e senha são obrigatórios."}), 400

    aluno = buscar_aluno_por_identificador(identificador)

    if aluno is None or not aluno.get("senha_hash"):
        return jsonify({"erro": "Credenciais inválidas."}), 401

    if not verificar_senha(senha, aluno["senha_hash"]):
        return jsonify({"erro": "Credenciais inválidas."}), 401

    session["usuario"] = formatar_aluno_publico(aluno)

    return jsonify(
        {
            "mensagem": "Login realizado com sucesso.",
            "usuario": session["usuario"],
        }
    ), 200


@app.post("/logout")
def logout():
    session.clear()
    return jsonify({"mensagem": "Logout realizado com sucesso."}), 200


@app.get("/api/me")
@login_obrigatorio
def api_me():
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"erro": "Não autenticado."}), 401
    return jsonify({"usuario": usuario}), 200


@app.post("/api/risco")
def api_risco():
    corpo = request.get_json(silent=True) or {}
    aluno = limpar_aluno(corpo.get("aluno", {}))
    if aluno is None:
        return jsonify({"erro": "Dados do aluno inválidos"}), 400
    return jsonify({"risco": float(risco_de_desistir(aluno))})


@app.get("/api/chat/historico")
@login_obrigatorio
def api_chat_historico():
    id_aluno = session["usuario"]["id_aluno"]
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, role, content, eh_treino FROM chat_mensagens WHERE id_aluno = %s ORDER BY id ASC LIMIT 50",
            (id_aluno,),
        )
        mensagens = cursor.fetchall()
        return jsonify({"ok": True, "mensagens": mensagens})
    finally:
        cursor.close()
        conn.close()


@app.post("/api/chat")
@login_obrigatorio
def api_chat():
    corpo = request.get_json(silent=True) or {}
    aluno = limpar_aluno(corpo.get("aluno", {}))
    historico = corpo.get("historico", [])
    if (aluno is None or not isinstance(historico, list) or not historico
            or any(not isinstance(m, dict)
                   or m.get("role") not in ("user", "assistant")
                   or not isinstance(m.get("content"), str)
                   or not 1 <= len(m["content"]) <= 12000 for m in historico)
            or historico[-1]["role"] != "user"):
        return jsonify({"erro": "Dados inválidos"}), 400

    # Mantém apenas as últimas 30 mensagens para enviar à IA sem estourar o limite
    historico = historico[-30:]

    usuario = session["usuario"]
    id_aluno = usuario["id_aluno"]
    aluno["nome"] = usuario.get("nome", "Aluno")
    ultima_msg_user = historico[-1]["content"]

    try:
        msg_lower = ultima_msg_user.lower()
        
        # Verifica se o usuário está pedindo um novo treino ou grupo específico
        pediu_novo_treino = any(
            p in msg_lower
            for p in (
                "outro treino",
                "novo treino",
                "monte um treino",
                "criar treino",
                "gerar treino",
                "treino de",
                "treino para",
                "ficha de",
                "ficha para",
                "exercícios para",
                "exercicios para",
                "focado em",
            )
        )
        
        # SE pediu um novo treino, isolamos a mensagem atual para a IA não misturar com o assunto antigo
        if pediu_novo_treino:
            historico_para_ia = [{"role": "user", "content": ultima_msg_user}]
            plano_anterior = None
            session.pop("plano_kiara", None)  # Limpa o plano anterior da sessão
        else:
            historico_para_ia = historico[-30:]
            plano_anterior = session.get("plano_kiara")

        resposta, modo, plano = responder_com_plano(aluno, historico_para_ia, plano_anterior)
        session["plano_kiara"] = plano
        
        eh_treino = 1 if (plano and plano.get("exercicios")) or (
            "séries" in resposta.lower()
            or "x 1" in resposta.lower()
            or "aquecimento" in resposta.lower()
        ) else 0

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_mensagens (id_aluno, role, content, eh_treino) VALUES (%s, 'user', %s, 0)",
                (id_aluno, ultima_msg_user),
            )
            cursor.execute(
                "INSERT INTO chat_mensagens (id_aluno, role, content, eh_treino) VALUES (%s, 'assistant', %s, %s)",
                (id_aluno, resposta, eh_treino),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        return jsonify({
            "resposta": resposta,
            "modo": modo,
            "eh_treino": bool(eh_treino),
            "risco": float(risco_de_desistir(aluno))
        })
    except Exception as e:
        print("Erro no chat:", e)
        return jsonify({"erro": "A Kiara não conseguiu responder agora. Tente novamente."}), 500

@app.post("/api/chat/limpar")
@login_obrigatorio
def api_limpar_chat():
    session.pop("plano_kiara", None)
    return jsonify({"mensagem": "Conversa reiniciada."}), 200


# ---------------------------------------------------------------- Treinos
@app.get("/api/serie")
def api_serie():
    nivel = request.args.get("nivel", "iniciante")
    objetivo = request.args.get("objetivo", "saúde geral")
    return jsonify(catalogo.montar_serie(nivel, objetivo))


# ---------------------------------------------------------------- Agendamento
HORARIOS = [f"{h:02d}:00" for h in range(6, 22)]
CAPACIDADE_POR_HORARIO = 10
MODALIDADES = ["musculação", "funcional", "aeróbico"]
DIAS_MAX_ANTECEDENCIA = 30


def buscar_aluno_por_matricula(matricula):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_aluno, nome FROM aluno WHERE matricula = %s", (matricula,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def contar_ocupacao(data_aula):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT TIME_FORMAT(horario, '%H:%i'), COUNT(*) FROM agendamento
               WHERE data_aula = %s AND status = 'agendada' GROUP BY horario""",
            (data_aula,),
        )
        return {h: int(q) for h, q in cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


def inserir_agendamento(id_aluno, data_aula, horario, modalidade):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO agendamento (id_aluno, data_aula, horario, modalidade) VALUES (%s, %s, %s, %s)",
            (id_aluno, data_aula, horario, modalidade),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def _parse_data(texto):
    try:
        return datetime.strptime(str(texto), "%Y-%m-%d").date()
    except ValueError:
        return None


@app.get("/api/horarios")
def api_horarios():
    data_aula = _parse_data(request.args.get("data", ""))
    if data_aula is None:
        return jsonify({"erro": "Data inválida. Use o formato AAAA-MM-DD."}), 400
    try:
        ocupacao = contar_ocupacao(data_aula)
    except Error:
        return jsonify({"erro": "Erro ao consultar horários."}), 500
    return jsonify({"data": str(data_aula), "horarios": [
        {"horario": h, "vagas": max(0, CAPACIDADE_POR_HORARIO - ocupacao.get(h, 0))}
        for h in HORARIOS]})


@app.post("/api/agendar")
@app.post("/api/agendamentos")
@login_obrigatorio
def api_agendar():
    corpo = request.get_json(silent=True) or {}
    id_aluno = session["usuario"].get("id_aluno")
    horario_bruto = str(corpo.get("horario", "")).strip()
    horario = horario_bruto.split("–")[0].strip().replace("h", ":")
    modalidade = str(corpo.get("modalidade", "musculação")).strip().lower()
    data_aula = _parse_data(corpo.get("data") or corpo.get("data_aula") or "")

    if not isinstance(id_aluno, int) or id_aluno <= 0:
        return jsonify({"erro": "Sessão inválida. Entre novamente."}), 401
    if data_aula is None:
        return jsonify({"erro": "Data inválida. Use o formato AAAA-MM-DD."}), 400
    hoje = date.today()
    if data_aula < hoje or data_aula > hoje + timedelta(days=DIAS_MAX_ANTECEDENCIA):
        return jsonify({"erro": f"Escolha uma data entre hoje e {DIAS_MAX_ANTECEDENCIA} dias à frente."}), 400
    if horario not in HORARIOS:
        return jsonify({"erro": "Horário indisponível. Atendemos das 06:00 às 21:00."}), 400
    if modalidade not in MODALIDADES:
        return jsonify({"erro": "Modalidade inválida."}), 400

    try:
        if contar_ocupacao(data_aula).get(horario, 0) >= CAPACIDADE_POR_HORARIO:
            return jsonify({"erro": "Horário lotado. Escolha outro horário."}), 409
        id_ag = inserir_agendamento(id_aluno, data_aula, horario, modalidade)
    except Error as e:
        if getattr(e, "errno", None) == 1062:
            return jsonify({"erro": "Você já tem aula agendada nesse horário."}), 409
        return jsonify({"erro": "Erro ao salvar agendamento."}), 500

    return jsonify({"mensagem": f"Aula de {modalidade} agendada para {data_aula.strftime('%d/%m/%Y')} às {horario}.",
                    "id_agendamento": id_ag}), 201


# ---------------------------------------------------------------- Auth (Novos)
@app.post("/api/auth/esqueci-senha")
def esqueci_senha():
    corpo = request.get_json(silent=True) or {}
    identificador = corpo.get("identificador")
    if not identificador:
        return jsonify({"ok": False, "erro": "Identificador é obrigatório."}), 400

    aluno = buscar_aluno_por_identificador(identificador)
    if not aluno:
        return jsonify({"ok": False, "erro": "Aluno não encontrado."}), 404

    token = secrets.token_urlsafe(32)
    expiracao = datetime.now() + timedelta(hours=1)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE aluno SET token_recuperacao = %s, token_expiracao = %s WHERE id_aluno = %s",
                       (token, expiracao, aluno["id_aluno"]))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return jsonify({"ok": True, "token_demonstracao": token})


@app.post("/api/auth/redefinir-senha")
def redefinir_senha():
    corpo = request.get_json(silent=True) or {}
    token = corpo.get("token")
    nova_senha = corpo.get("nova_senha")

    if not token or not nova_senha or len(nova_senha) < 8:
        return jsonify({"ok": False, "erro": "Dados inválidos."}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_aluno, token_expiracao FROM aluno WHERE token_recuperacao = %s", (token,))
        aluno = cursor.fetchone()

        if not aluno or aluno["token_expiracao"] < datetime.now():
            return jsonify({"ok": False, "erro": "Token inválido ou expirado."}), 400

        cursor.execute("UPDATE aluno SET senha_hash = %s, token_recuperacao = NULL, token_expiracao = NULL WHERE id_aluno = %s",
                       (gerar_hash_senha(nova_senha), aluno["id_aluno"]))
        conn.commit()
        return jsonify({"ok": True, "mensagem": "Senha redefinida com sucesso."})
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------- Dashboard
@app.get("/api/dashboard")
@login_obrigatorio
def api_dashboard():
    usuario = session["usuario"]
    aluno = buscar_aluno_por_id(usuario["id_aluno"])

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        dia_semana_hoje = datetime.now().strftime("%A")
        cursor.execute("SELECT * FROM treinos WHERE aluno_id = %s AND dia_semana = %s AND ativo = 1",
                       (aluno["id_aluno"], dia_semana_hoje))
        treino_hoje = cursor.fetchone()
        if treino_hoje:
            cursor.execute("SELECT * FROM treino_exercicios WHERE treino_id = %s ORDER BY ordem", (treino_hoje["id"],))
            treino_hoje["exercicios"] = cursor.fetchall()

        cursor.execute("SELECT * FROM agendamento WHERE id_aluno = %s AND data_aula >= CURDATE() AND status IN ('agendada', 'agendado') ORDER BY data_aula, horario LIMIT 1",
                       (aluno["id_aluno"],))
        proxima_aula = cursor.fetchone()

        cursor.execute("SELECT * FROM agendamento WHERE id_aluno = %s AND data_aula >= CURDATE() ORDER BY data_aula, horario LIMIT 3",
                       (aluno["id_aluno"],))
        proximos_agendamentos = cursor.fetchall()

        return jsonify({
            "ok": True,
            "aluno": formatar_aluno_publico(aluno),
            "treino_hoje": treino_hoje,
            "proxima_aula": _serializar_agendamento(proxima_aula),
            "proximos_agendamentos": [_serializar_agendamento(a) for a in proximos_agendamentos]
        })
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------- Perfil
@app.get("/api/perfil")
@login_obrigatorio
def api_perfil():
    aluno = buscar_aluno_por_id(session["usuario"]["id_aluno"])

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM agendamento WHERE id_aluno = %s AND status IN ('concluida', 'concluido')", (aluno["id_aluno"],))
        aulas_concluidas = cursor.fetchone()[0]
        cursor.close()
    finally:
        conn.close()

    return jsonify({
        "ok": True,
        "aluno": formatar_aluno_publico(aluno),
        "progresso": {
            "aulas_realizadas": aulas_concluidas,
            "frequencia": f"{aluno.get('treinos_semana', 3)}/sem",
            "evolucao_estimada": f"{min(aulas_concluidas * 2, 100)}%"
        }
    })


@app.post("/api/perfil")
@app.put("/api/perfil")
@login_obrigatorio
def api_perfil_update():
    corpo = request.get_json(silent=True) or {}
    usuario = session["usuario"]

    if "frequencia" in corpo and "treinos_semana" not in corpo:
        try:
            corpo["treinos_semana"] = int(str(corpo["frequencia"]).split()[0])
        except ValueError:
            pass
    if "modalidade" in corpo and "modalidade_principal" not in corpo:
        corpo["modalidade_principal"] = corpo["modalidade"]

    campos_permitidos = ['nome', 'email', 'telefone', 'objetivo', 'nivel', 'treinos_semana', 'modalidade_principal', 'notificacoes', 'acessibilidade', 'tema']
    dados_para_update = {k: v for k, v in corpo.items() if k in campos_permitidos}

    if not dados_para_update:
        return jsonify({"ok": False, "erro": "Dados inválidos."}), 400

    set_clause = ", ".join([f"{k} = %s" for k in dados_para_update.keys()])
    values = list(dados_para_update.values())
    values.append(usuario["id_aluno"])

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE aluno SET {set_clause} WHERE id_aluno = %s", tuple(values))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    aluno_atualizado = buscar_aluno_por_id(usuario["id_aluno"])
    session["usuario"] = formatar_aluno_publico(aluno_atualizado)
    return jsonify({"ok": True, "mensagem": "Perfil atualizado.", "aluno": session["usuario"]})


@app.post("/api/perfil/avatar")
@login_obrigatorio
def api_avatar_upload():
    if 'avatar' not in request.files:
        return jsonify({"ok": False, "erro": "Arquivo não enviado."}), 400
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({"ok": False, "erro": "Nome de arquivo inválido."}), 400

    if file:
        filename = secure_filename(f"avatar_{session['usuario']['id_aluno']}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        avatar_url = f"/uploads/avatars/{filename}"

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE aluno SET avatar_url = %s WHERE id_aluno = %s", (avatar_url, session["usuario"]["id_aluno"]))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        session["usuario"]["avatar_url"] = avatar_url
        session.modified = True

        return jsonify({"ok": True, "avatar_url": avatar_url})


# ---------------------------------------------------------------- Treinos
@app.get("/api/treinos")
@login_obrigatorio
def api_treinos():
    id_aluno = session["usuario"]["id_aluno"]
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM treinos WHERE aluno_id = %s AND ativo = 1", (id_aluno,))
        treinos = cursor.fetchall()
        for t in treinos:
            cursor.execute("SELECT * FROM treino_exercicios WHERE treino_id = %s ORDER BY ordem", (t["id"],))
            t["exercicios"] = cursor.fetchall()
        return jsonify({"ok": True, "treinos": treinos})
    finally:
        cursor.close()
        conn.close()


@app.post("/api/treinos/gerar-kiara")
@login_obrigatorio
def api_gerar_treino_kiara():
    usuario = session["usuario"]
    aluno = buscar_aluno_por_id(usuario["id_aluno"])

    resposta, modo, plano = responder_com_plano(aluno, [{"role": "user", "content": "Monte um treino"}], None)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO treinos (aluno_id, titulo, dia_semana, origem) VALUES (%s, %s, %s, %s)",
                       (aluno["id_aluno"], "Treino Kiara", "Segunda-feira", "kiara"))
        treino_id = cursor.lastrowid

        for i, ex in enumerate(plano.get("exercicios", [])):
            cursor.execute("INSERT INTO treino_exercicios (treino_id, nome_exercicio, series, repeticoes, ordem) VALUES (%s, %s, %s, %s, %s)",
                           (treino_id, ex.get("nome_pt"), ex.get("series"), ex.get("repeticoes"), i+1))
        conn.commit()
        return jsonify({"ok": True, "treino_id": treino_id, "mensagem": "Treino gerado pela Kiara e salvo!"})
    finally:
        cursor.close()
        conn.close()

@app.post("/api/treinos/salvar-do-chat")
@login_obrigatorio
def api_salvar_treino_do_chat():
    corpo = request.get_json(silent=True) or {}
    texto_treino = (corpo.get("texto") or "").strip()
    dia_semana = (corpo.get("dia_semana") or "Segunda-feira").strip()

    exercicios_para_salvar = []
    titulo_detectado = None

    ignorar_prefixos = (
        "aquecimento",
        "treino principal",
        "treino secundário",
        "treino secundario",
        "observações",
        "observacoes",
        "dica",
        "importante",
        "atenção",
    )

    if texto_treino:
        for linha in texto_treino.splitlines():
            limpa = re.sub(r"^[\-\•\*\#\d\.\)\s]+", "", linha.strip()).strip()
            if not limpa:
                continue

            # Detecta título se a Kiara escreveu "Treino A...", "Treino de Peito...", etc.
            if not titulo_detectado and (
                limpa.lower().startswith(("treino ", "ficha ", "plano ", "rotina "))
            ) and not re.search(r"\d+\s*[xX]\s*\d+", limpa) and len(limpa) <= 65:
                titulo_detectado = limpa.rstrip(":")
                continue

            # Verifica se a linha parece um exercício (tem ":", "—", " - " ou padrão "3x10" / "min")
            tem_padrao_sr = bool(re.search(r"\d+\s*[xX]\s*\d+", limpa))
            tem_min = bool(re.search(r"\b\d+\s*min\b", limpa, re.IGNORECASE))
            tem_separador = any(sep in limpa for sep in (":", " — ", " – ", " - "))

            if not (tem_padrao_sr or tem_min or tem_separador):
                continue

            # Separa nome do exercício e detalhes
            if ":" in limpa:
                nome_ex, detalhes = limpa.split(":", 1)
            elif " — " in limpa:
                nome_ex, detalhes = limpa.split(" — ", 1)
            elif " – " in limpa:
                nome_ex, detalhes = limpa.split(" – ", 1)
            elif " - " in limpa:
                nome_ex, detalhes = limpa.split(" - ", 1)
            else:
                m_split = re.search(r"(\(?\d+\s*[xX]\s*[\d\s\-–]+.*|\(?\d+\s*min.*)", limpa, re.IGNORECASE)
                if m_split:
                    nome_ex = limpa[:m_split.start()].strip(" -–—:(")
                    detalhes = m_split.group(1).strip("()")
                else:
                    continue

            nome_ex = nome_ex.strip(" *#:")
            detalhes = detalhes.strip()

            if not nome_ex or not detalhes or nome_ex.lower() in ignorar_prefixos:
                continue

            series = 3
            repeticoes = "10 - 12"
            descanso = 60

            m_sr = re.search(r"(\d+)\s*[xX]\s*([\d\s\-–]+)", detalhes)
            if m_sr:
                series = int(m_sr.group(1))
                repeticoes = m_sr.group(2).strip() or "10"
            elif "min" in detalhes.lower():
                series = 1
                m_min = re.search(r"(\d+\s*min)", detalhes, re.IGNORECASE)
                repeticoes = m_min.group(1) if m_min else "8 min"

            m_desc = re.search(r"descanso\s*(\d+)", detalhes, re.IGNORECASE)
            if m_desc:
                descanso = int(m_desc.group(1))

            exercicios_para_salvar.append({
                "nome_exercicio": nome_ex[:80],
                "series": series,
                "repeticoes": repeticoes[:25],
                "descanso_segundos": descanso,
            })

    # Fallback para plano_kiara da sessão apenas se nenhum exercício foi extraído do texto
    if not exercicios_para_salvar:
        plano = session.get("plano_kiara") or {}
        for ex in (plano.get("exercicios") or []):
            exercicios_para_salvar.append({
                "nome_exercicio": ex.get("nome_pt") or ex.get("nome") or "Exercício",
                "series": int(ex.get("series") or 3),
                "repeticoes": str(ex.get("repeticoes") or "8 - 12"),
                "descanso_segundos": int(ex.get("descanso_segundos") or 60),
            })

    if not exercicios_para_salvar:
        exercicios_para_salvar.append({
            "nome_exercicio": "Treino personalizado (ver observações)",
            "series": 3,
            "repeticoes": "10 - 12",
            "descanso_segundos": 60,
        })

    id_aluno = session["usuario"]["id_aluno"]
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Conta quantos treinos o aluno já tem para numerar caso não tenha título específico
        cursor.execute("SELECT COUNT(*) FROM treinos WHERE aluno_id = %s AND ativo = 1", (id_aluno,))
        qtd_existente = cursor.fetchone()[0]
        titulo_final = titulo_detectado or f"Treino Kiara #{qtd_existente + 1}"

        cursor.execute(
            "INSERT INTO treinos (aluno_id, titulo, subtitulo, dia_semana, origem, observacoes) VALUES (%s, %s, %s, %s, 'kiara', %s)",
            (id_aluno, titulo_final, f"{len(exercicios_para_salvar)} exercícios", dia_semana, texto_treino[:1000]),
        )
        treino_id = cursor.lastrowid
        for i, ex in enumerate(exercicios_para_salvar):
            cursor.execute(
                "INSERT INTO treino_exercicios (treino_id, nome_exercicio, series, repeticoes, descanso_segundos, ordem) VALUES (%s, %s, %s, %s, %s, %s)",
                (treino_id, ex["nome_exercicio"], ex["series"], ex["repeticoes"], ex["descanso_segundos"], i + 1),
            )
        conn.commit()
        return jsonify({"ok": True, "treino_id": treino_id, "mensagem": f"{titulo_final} salvo em Meus treinos!"})
    finally:
        cursor.close()
        conn.close()


@app.post("/api/treinos")
@login_obrigatorio
def api_criar_treino():
    corpo = request.get_json(silent=True) or {}
    id_aluno = session["usuario"]["id_aluno"]

    titulo = corpo.get("titulo")
    dia_semana = corpo.get("dia_semana")
    exercicios = corpo.get("exercicios", [])

    if not titulo or not dia_semana:
        return jsonify({"ok": False, "erro": "Título e dia da semana são obrigatórios."}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO treinos (aluno_id, titulo, subtitulo, dia_semana, origem, observacoes) VALUES (%s, %s, %s, %s, %s, %s)",
                       (id_aluno, titulo, corpo.get("subtitulo"), dia_semana, corpo.get("origem", "manual"), corpo.get("observacoes")))
        treino_id = cursor.lastrowid

        for i, ex in enumerate(exercicios):
            cursor.execute("INSERT INTO treino_exercicios (treino_id, nome_exercicio, grupo_muscular, series, repeticoes, descanso_segundos, ordem) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (treino_id, ex.get("nome_exercicio"), ex.get("grupo_muscular"), ex.get("series", 3), ex.get("repeticoes", "8 - 12"), ex.get("descanso_segundos", 60), i+1))
        conn.commit()
        return jsonify({"ok": True, "treino_id": treino_id}), 201
    finally:
        cursor.close()
        conn.close()


@app.delete("/api/treinos/<int:treino_id>")
@login_obrigatorio
def api_deletar_treino(treino_id):
    id_aluno = session["usuario"]["id_aluno"]
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM treinos WHERE id = %s AND aluno_id = %s", (treino_id, id_aluno))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"ok": False, "erro": "Treino não encontrado."}), 404
        return jsonify({"ok": True, "mensagem": "Treino removido."})
    finally:
        cursor.close()
        conn.close()


@app.get("/api/exercicios")
def api_exercicios():
    busca = request.args.get("busca", "").lower()
    grupo = request.args.get("grupo_muscular", "").lower()

    todos = biblioteca_exercicios.carregar()
    resultado = []

    for item in todos:
        nome_pt = biblioteca_exercicios.nome_pt(item.get("name", ""), item.get("id"))
        if not nome_pt:
            continue
        if busca and busca not in nome_pt.lower():
            continue
        resultado.append({
            "id": item.get("id"),
            "nome": nome_pt,
            "equipamento": item.get("equipment"),
            "alvo": item.get("target")
        })

    return jsonify({"ok": True, "exercicios": resultado[:50]})


# ---------------------------------------------------------------- Agendamentos (Novos)
@app.get("/api/agendamentos")
@login_obrigatorio
def api_listar_agendamentos():
    id_aluno = session["usuario"]["id_aluno"]
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM agendamento WHERE id_aluno = %s ORDER BY data_aula DESC, horario DESC", (id_aluno,))
        agendamentos = cursor.fetchall()

        hoje = date.today()
        proximos = [a for a in agendamentos if a["data_aula"] >= hoje and a["status"] in ('agendada', 'agendado')]

        return jsonify({
            "ok": True,
            "agendamentos": [_serializar_agendamento(a) for a in agendamentos],
            "proximos_agendamentos": [_serializar_agendamento(a) for a in proximos]
        })
    finally:
        cursor.close()
        conn.close()


@app.get("/api/agendamentos/vagas")
def api_agendamentos_vagas():
    data_str = request.args.get("data")
    modalidade = request.args.get("modalidade", "Musculação")

    if not data_str:
        return jsonify({"ok": False, "erro": "Data é obrigatória."}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT horario, vagas_totais FROM grade_horarios WHERE modalidade = %s AND ativo = 1", (modalidade,))
        grades = cursor.fetchall()

        cursor.execute("SELECT horario, COUNT(*) as ocupados FROM agendamento WHERE data_aula = %s AND modalidade = %s AND status IN ('agendada', 'agendado') GROUP BY horario",
                       (data_str, modalidade))
        ocupacao = {row["horario"]: row["ocupados"] for row in cursor.fetchall()}

        resultado = []
        for g in grades:
            vagas = max(0, g["vagas_totais"] - ocupacao.get(g["horario"], 0))
            resultado.append({
                "horario": g["horario"],
                "vagas_restantes": vagas
            })

        return jsonify({"ok": True, "vagas": resultado})
    finally:
        cursor.close()
        conn.close()


@app.post("/api/agendamentos/inteligente")
@login_obrigatorio
def api_agendamento_inteligente():
    usuario = session["usuario"]
    aluno = buscar_aluno_por_id(usuario["id_aluno"])
    modalidade = aluno.get("modalidade_principal", "Musculação")

    amanha = date.today() + timedelta(days=1)

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT horario FROM grade_horarios WHERE modalidade = %s AND ativo = 1 LIMIT 1", (modalidade,))
        grade = cursor.fetchone()

        if not grade:
            return jsonify({"ok": False, "erro": "Não há horários disponíveis para sua modalidade."}), 404

        horario = grade["horario"]

        cursor.execute("INSERT INTO agendamento (id_aluno, data_aula, horario, modalidade, status) VALUES (%s, %s, %s, %s, 'agendado')",
                       (aluno["id_aluno"], amanha, horario, modalidade))
        conn.commit()

        return jsonify({
            "ok": True,
            "mensagem": "Agendamento inteligente realizado com sucesso!",
            "agendamento": {
                "data": str(amanha),
                "horario": horario,
                "modalidade": modalidade
            }
        })
    finally:
        cursor.close()
        conn.close()


@app.delete("/api/agendamentos/<int:agendamento_id>")
@login_obrigatorio
def api_cancelar_agendamento(agendamento_id):
    id_aluno = session["usuario"]["id_aluno"]
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE agendamento SET status = 'cancelado' WHERE id_agendamento = %s AND id_aluno = %s",
                       (agendamento_id, id_aluno))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"ok": False, "erro": "Agendamento não encontrado."}), 404
        return jsonify({"ok": True, "mensagem": "Agendamento cancelado com sucesso."})
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5000)