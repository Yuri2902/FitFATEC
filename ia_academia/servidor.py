import os
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, session
from assistente import responder, risco_de_desistir
from auth_utils import validar_cadastro, gerar_hash_senha, verificar_senha
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

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
        conn.commit()
        return cursor.lastrowid
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
            SELECT id_aluno, nome, email, senha_hash, papel
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
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
