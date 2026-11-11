import os
from datetime import date, datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, session
from assistente import responder, risco_de_desistir
import catalogo
from auth_utils import validar_cadastro, gerar_hash_senha, verificar_senha
import mysql.connector
from mysql.connector import Error

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")

# static_url_path="" serve CSS.css, visual.js e img/ direto da pasta public/
app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path="")

app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)


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


def salvar_aluno_no_banco(nome, email, senha_hash):
    """Insere um novo aluno na tabela aluno.

    Retorna o id_aluno gerado.
    Levanta ValueError se o e-mail já estiver cadastrado.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Verifica se o e-mail já existe antes de inserir
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
    """Converte os campos numéricos e garante que nada falte."""
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


@app.get("/health")
def health():
    return jsonify({"status": "ok", "mensagem": "Servidor Flask está funcionando"})


@app.get("/")
def pagina_inicial():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    public_dir = os.path.join(project_root, "public")
    return send_from_directory(public_dir, "index.html")


@app.get("/teste-auth")
def pagina_teste_auth():
    public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
    return send_from_directory(public_dir, "teste-auth.html")


@app.post("/cadastro")
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
    except Error as e:
        return jsonify({"erro": "Erro ao salvar aluno no banco."}), 500

    return jsonify({"mensagem": "Cadastro realizado com sucesso."}), 201


def buscar_aluno_por_email(email):
    """Busca um aluno pelo e-mail na tabela aluno.

    Retorna um dicionário com id_aluno, nome, email, senha_hash, papel
    ou None se não encontrar.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id_aluno, nome, email, senha_hash, papel, matricula
            FROM aluno
            WHERE email = %s
            """,
            (email,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


@app.post("/login")
def login():
    corpo = request.get_json(silent=True) or {}
    email = corpo.get("email", "")
    senha = corpo.get("senha", "")

    if not email or not senha:
        return jsonify({"erro": "E-mail e senha são obrigatórios."}), 400

    aluno = buscar_aluno_por_email(email)

    if aluno is None or not aluno.get("senha_hash"):
        return jsonify({"erro": "Credenciais inválidas."}), 401

    if not verificar_senha(senha, aluno["senha_hash"]):
        return jsonify({"erro": "Credenciais inválidas."}), 401

    session["usuario"] = {
        "id_aluno": aluno["id_aluno"],
        "nome": aluno["nome"],
        "email": aluno["email"],
        "papel": aluno["papel"],
        "matricula": aluno.get("matricula"),
    }

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


@app.post("/api/chat")
def api_chat():
    corpo = request.get_json(silent=True) or {}
    aluno = limpar_aluno(corpo.get("aluno", {}))
    historico = corpo.get("historico", [])
    if aluno is None or not historico:
        return jsonify({"erro": "Dados inválidos"}), 400
    try:
        resposta = responder(aluno, historico)
        return jsonify({"resposta": resposta, "risco": float(risco_de_desistir(aluno))})
    except Exception:
        return jsonify({"erro": "A Kiara não conseguiu responder agora. Tente novamente."}), 500


# ---------------------------------------------------------------- Treinos
@app.get("/api/serie")
def api_serie():
    """Aquecimento + treino principal + secundário por nível e objetivo."""
    nivel = request.args.get("nivel", "iniciante")
    objetivo = request.args.get("objetivo", "saúde geral")
    return jsonify(catalogo.montar_serie(nivel, objetivo))


# ---------------------------------------------------------------- Agendamento
HORARIOS = [f"{h:02d}:00" for h in range(6, 22)]  # 06:00 a 21:00
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
    """Retorna {'HH:MM': quantidade} de aulas agendadas na data."""
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
def api_agendar():
    corpo = request.get_json(silent=True) or {}
    matricula = str(corpo.get("matricula", "")).strip()
    horario = str(corpo.get("horario", "")).strip()
    modalidade = str(corpo.get("modalidade", "musculação")).strip().lower()
    data_aula = _parse_data(corpo.get("data", ""))

    if not matricula.isdigit() or not 4 <= len(matricula) <= 12:
        return jsonify({"erro": "Matrícula inválida."}), 400
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
        aluno = buscar_aluno_por_matricula(matricula)
        if aluno is None:
            return jsonify({"erro": "Matrícula não encontrada."}), 404
        if contar_ocupacao(data_aula).get(horario, 0) >= CAPACIDADE_POR_HORARIO:
            return jsonify({"erro": "Horário lotado. Escolha outro horário."}), 409
        id_ag = inserir_agendamento(aluno["id_aluno"], data_aula, horario, modalidade)
    except Error as e:
        if getattr(e, "errno", None) == 1062:  # UNIQUE (aluno, data, horário)
            return jsonify({"erro": "Você já tem aula agendada nesse horário."}), 409
        return jsonify({"erro": "Erro ao salvar agendamento."}), 500

    return jsonify({"mensagem": f"Aula de {modalidade} agendada para {data_aula.strftime('%d/%m/%Y')} às {horario}.",
                    "id_agendamento": id_ag}), 201


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5000)
