import os
import re
import secrets
import planejamento
import configuracao  # carrega .env ANTES de importar assistente e ler DB_CONFIG
from datetime import date, datetime, timedelta
from functools import wraps
from time import perf_counter
from flask import Flask, request, jsonify, send_from_directory, send_file, session, redirect
from werkzeug.utils import secure_filename
from assistente import responder_com_plano
from voz_kiara import gerar_audio_wav
import catalogo
import biblioteca_exercicios
import plano_kiara
import avaliacao_inicial
import personalidades  # Dev 3: personalidades da Kiara (maromba, nerd, sem filtro +18...)
from treinos import plano_semanal  # Dev 3: plano de treino semanal salvo em Meus treinos
from treinos.regras import ErroPerfil
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


# A estrutura oficial é criada apenas pelo bdd/bd_fitfatec.sql (instalação limpa).


def salvar_aluno_no_banco(nome, email, senha_hash):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_aluno FROM aluno WHERE email = %s", (email,))
        if cursor.fetchone():
            raise ValueError("E-mail já cadastrado.")

        cursor.execute(
            """
            INSERT INTO aluno (nome, email, senha_hash, created_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (nome, email, senha_hash),
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
    """Campos do perfil de treino consumidos pelo chat (sem dados fictícios de evasão)."""
    try:
        aluno = {
            "idade": int(dados["idade"]),
            "objetivo": str(dados["objetivo"]),
            "nivel": str(dados["nivel"]),
            "frequencia_semanal": int(dados["frequencia_semanal"]),
        }
        duracao = dados.get("minutos_por_sessao")
        if duracao not in (None, ""):
            duracao = int(duracao)
            if not 10 <= duracao <= 240:
                return None
            aluno["minutos_por_sessao"] = duracao
        return aluno
    except (KeyError, ValueError, TypeError, AttributeError):
        return None


# A detecção de fichas deve aceitar duração (cardio), além de séries/repetições.
# O frontend usa o mesmo critério em public/visual.js.
_PADRAO_FICHA_CHAT = re.compile(
    r"(?:^|\n)\s*(?:[-•*]\s*)?[^\n:]{3,100}:\s*"
    r"(?:\d+\s*[xX×]\s*\d+|\d+\s*min(?:utos?)?\b)",
    re.IGNORECASE,
)


def _parece_ficha_chat(texto):
    return bool(_PADRAO_FICHA_CHAT.search(texto or ""))


def _pedido_para_salvar_ficha_anterior(texto):
    """Somente pedidos explícitos de salvar algo JÁ gerado, nunca gerar outra ficha."""
    pedido = " ".join((texto or "").lower().split())
    if not re.search(r"\b(?:salvar|salve|guardar|guarde|gravar)\b", pedido):
        return False
    if re.search(r"\b(?:novo|nova|outro|outra|criar|crie|gerar|gere|montar|monte|alterar|altere)\b", pedido):
        return False
    # "o treino para eu salvar" aponta para o treino já sugerido. Não confundir
    # com "um treino de costas para salvar", que pede uma ficha nova.
    if re.search(r"\b(?:um|uma)\s+(?:treino|ficha)\b|\btreino\s+de\b", pedido):
        return False
    return bool(re.search(
        r"\b(?:esse|essa|este|esta|anterior|último|ultimo|agora|ele|isso|ficha|treino)\b"
        r"|\bpara\s+(?:eu\s+)?salvar\b", pedido,
    ))


# Apenas atividades claramente identificáveis podem ser extraídas de uma dica
# informal. Não inferir grupo muscular ou inventar exercícios ao pedir para salvar.
_ATIVIDADES_COM_DURACAO = (
    (r"caminhada\s+na\s+esteira", "Caminhada na esteira"),
    (r"corrida\s+na\s+esteira", "Corrida na esteira"),
    (r"bicicleta\s+ergom[eé]trica", "Bicicleta ergométrica"),
    (r"pular\s+corda", "Pular corda"),
    (r"caminhada", "Caminhada"),
    (r"corrida", "Corrida"),
    (r"esteira", "Esteira"),
    (r"bicicleta", "Bicicleta"),
    (r"el[ií]ptico", "Elíptico"),
)
_PALAVRAS_ATIVIDADE = "(?:" + "|".join(p[0] for p in _ATIVIDADES_COM_DURACAO) + ")"
_PADROES_DICA_COM_DURACAO = (
    # "20 minutos de esteira" / "15 min de bicicleta ergométrica"
    re.compile(
        rf"(?P<duracao>\d{{1,3}})\s*min(?:utos?)?\s+(?:de|na|no|em)\s+(?P<atividade>{_PALAVRAS_ATIVIDADE})\b",
        re.IGNORECASE,
    ),
    # "caminhada na esteira por 20 minutos" / "bicicleta durante 10 min"
    re.compile(
        rf"(?P<atividade>{_PALAVRAS_ATIVIDADE})\s+(?:por|durante|de)\s+(?P<duracao>\d{{1,3}})\s*min(?:utos?)?\b",
        re.IGNORECASE,
    ),
)


# O intervalo é uma INSTRUÇÃO do exercício principal, não outro exercício.
# A identificação é conservadora: sem atividade e duração principal explícitas,
# a ficha não é criada automaticamente.
_MARCADOR_INTERVALO = re.compile(
    r"\b(?:alternando|alternar|alterne|intercalando|intercalar|intercale)\b",
    re.IGNORECASE,
)


def _ficha_de_dica_informal(texto):
    """Estrutura uma sugestão explícita, preservando protocolos intervalados.

    Ex.: 30 min de esteira alternando trote/caminhada = UM exercício de 30 min.
    As instruções originais permanecem no texto da ficha (e, ao salvar,
    em treinos.observacoes), sem criar exercícios extras de 1 minuto.
    """
    if not isinstance(texto, str) or not texto.strip():
        return None

    # Delimita trechos de alternância. Durações dentro de um protocolo
    # não são prescrições independentes e não viram itens da ficha.
    intervalos = []
    for marcador in _MARCADOR_INTERVALO.finditer(texto):
        fim = re.search(r"[.,;!?\n]", texto[marcador.start():marcador.start() + 220])
        fim = marcador.start() + fim.start() if fim else min(len(texto), marcador.start() + 220)
        instrucao = " ".join(texto[marcador.start():fim].split()).strip(" ,;:.-")
        if instrucao:
            intervalos.append((marcador.start(), fim, instrucao))

    encontrados = []
    for padrao in _PADROES_DICA_COM_DURACAO:
        for m in padrao.finditer(texto):
            # O 1 min de caminhada numa alternância não é um treino adicional.
            if any(inicio <= m.start() < fim for inicio, fim, _ in intervalos):
                continue
            # Recusa instruções negativas como "evite 20 minutos de esteira".
            trecho = texto[max(0, m.start() - 45):m.start()].lower()
            trecho = re.split(r"[.!?;\n]", trecho)[-1]
            if re.search(r"\b(?:evite|evitar|dispense|não faça|nao faca|não recomendo|nao recomendo)\b", trecho):
                continue
            minutos = int(m.group("duracao"))
            if not 1 <= minutos <= 180:
                continue
            atividade = m.group("atividade")
            nome = next((rotulo for expr, rotulo in _ATIVIDADES_COM_DURACAO
                         if re.fullmatch(expr, atividade, re.IGNORECASE)), None)
            if nome:
                encontrados.append((m.start(), m.end(), nome, minutos))

    # Dois padrões podem encontrar a mesma prescrição; não duplicar.
    encontrados = sorted(set(encontrados), key=lambda e: e[0])
    if not encontrados:
        return None

    linhas = []
    ja_vistos = set()
    tem_intervalo = False
    for inicio, fim, nome, minutos in encontrados:
        protocolo = None
        for pos, _fim_intervalo, instrucao in intervalos:
            trecho_entre = texto[fim:pos] if pos >= fim else ""
            # O protocolo deve estar próximo do exercício, na mesma frase.
            # Vírgula é permitida em "esteira intervalada, alternando...".
            if 0 <= pos - fim <= 100 and not re.search(r"[.;!?\n]", trecho_entre):
                # Se houve outra prescrição principal entre os dois,
                # o intervalo pertence àquela mais próxima.
                if any(fim <= outro_inicio < pos for outro_inicio, _, _, _ in encontrados):
                    continue
                protocolo = instrucao
                break
        if protocolo:
            tem_intervalo = True
            if "intervalad" not in nome.lower():
                nome += " intervalada" if nome.lower().endswith("esteira") else " intervalado"
        chave = (nome, minutos, protocolo)
        if chave in ja_vistos:
            continue
        ja_vistos.add(chave)
        detalhes = f" ({protocolo})" if protocolo else ""
        linhas.append(f"- {nome}: 1x{minutos} min{detalhes}")
        if len(linhas) >= 10:
            break

    if not linhas:
        return None
    return ("Cardio intervalado:" if tem_intervalo else "Cardio sugerido:") + "\n" + "\n".join(linhas)


def _ultima_ficha_no_historico(historico):
    """Usa somente a última resposta da Kiara, mesmo quando é uma dica informal."""
    for mensagem in reversed(historico[:-1]):
        if mensagem.get("role") == "assistant":
            conteudo = mensagem.get("content", "")
            if _parece_ficha_chat(conteudo):
                return conteudo
            return _ficha_de_dica_informal(conteudo)
    return None


def _serializar_agendamento(ag):
    if not ag:
        return None
    copia = dict(ag)
    if isinstance(copia.get("data_treino"), (date, datetime)):
        copia["data_treino"] = copia["data_treino"].strftime("%Y-%m-%d")
    if isinstance(copia.get("horario"), timedelta):
        total = int(copia["horario"].total_seconds())
        copia["horario"] = f"{total // 3600:02d}:{(total % 3600) // 60:02d}"
    elif copia.get("horario") is not None:
        copia["horario"] = str(copia["horario"])[:5]
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
    copia["telefone"] = copia.get("telefone") or ""
    copia["avatar_url"] = copia.get("avatar_url") or ""
    copia["treinos_semana"] = copia.get("treinos_semana")
    copia["minutos_por_sessao"] = copia.get("minutos_por_sessao")
    copia["modalidade_principal"] = copia.get("modalidade_principal") or "Musculação"
    copia["notificacoes"] = bool(copia.get("notificacoes", 1))
    copia["acessibilidade"] = copia.get("acessibilidade") or "padrao"
    copia["tema"] = copia.get("tema") or "escuro"
    # Dev 3: a data de nascimento vira texto AAAA-MM-DD para caber na sessão e no JSON.
    # Quando ela existe, a idade real passa a ir para o chat (sem ela, a tela manda 22).
    nascimento = copia.get("data_nascimento")
    if isinstance(nascimento, (date, datetime)):
        copia["data_nascimento"] = nascimento.strftime("%Y-%m-%d")
    copia["idade"] = personalidades.calcular_idade(copia.get("data_nascimento"))
    copia["personalidade"] = copia.get("personalidade") or personalidades.PADRAO
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


def ultimo_id_mensagem(id_aluno):
    """Marca o fim das conversas anteriores, sem apagar mensagens do MySQL."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COALESCE(MAX(id), 0) FROM chat_mensagens WHERE id_aluno = %s",
                (id_aluno,),
            )
            linha = cursor.fetchone()
            return int(linha[0]) if linha else 0
        finally:
            cursor.close()
    finally:
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

    # Cada login começa uma conversa nova, mesmo que mensagens antigas ainda estejam no banco.
    # A marcação por ID mantém o histórico da sessão atual após atualizar o navegador.
    try:
        chat_inicio_id = ultimo_id_mensagem(aluno["id_aluno"])
    except Error:
        return jsonify({"erro": "Não foi possível iniciar sua conversa. Tente novamente."}), 503

    session.clear()  # não reutilizar o estado de outro login
    session["usuario"] = formatar_aluno_publico(aluno)
    session["chat_inicio_id"] = chat_inicio_id

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
    try:
        aluno = buscar_aluno_por_id(usuario["id_aluno"])
    except Error:
        return jsonify({"erro": "Não foi possível verificar a sessão no banco."}), 503
    if not aluno:
        session.clear()
        return jsonify({"erro": "Sessão expirada. Entre novamente."}), 401
    session["usuario"] = formatar_aluno_publico(aluno)
    return jsonify({"usuario": session["usuario"]}), 200


@app.get("/api/chat/historico")
@login_obrigatorio
def api_chat_historico():
    id_aluno = session["usuario"]["id_aluno"]
    # Só carrega as mensagens criadas depois do login atual.
    # Para sessões abertas antes desta atualização, mantém a compatibilidade.
    chat_inicio_id = int(session.get("chat_inicio_id", 0))
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, role, content, eh_treino FROM chat_mensagens "
            "WHERE id_aluno = %s AND id > %s ORDER BY id ASC LIMIT 50",
            (id_aluno, chat_inicio_id),
        )
        mensagens = cursor.fetchall()
        return jsonify({"ok": True, "mensagens": mensagens})
    finally:
        cursor.close()
        conn.close()


@app.get("/api/kiara/inicio")
@login_obrigatorio
def api_kiara_inicio():
    """Abre a avaliação apenas quando o perfil ainda não foi configurado."""
    usuario = session["usuario"]
    aluno = buscar_aluno_por_id(usuario["id_aluno"])
    if not aluno:
        session.clear()
        return jsonify({"erro": "Sua sessão expirou. Faça login novamente."}), 401
    if not avaliacao_inicial.precisa_configurar(aluno) or session.get("avaliacao_pulada"):
        session.pop("avaliacao_inicial", None)
        return jsonify({"pendente": False})
    estado = session.get("avaliacao_inicial") or avaliacao_inicial.criar_estado(aluno)
    session["avaliacao_inicial"] = estado
    return jsonify({"pendente": True, "mensagem": avaliacao_inicial.pergunta(estado),
                    "opcoes": avaliacao_inicial.opcoes(estado), "etapa": estado["etapa"]})


def _responder_avaliacao_inicial(usuario, mensagem):
    """Processa a primeira conversa sem pedir à IA para escrever no banco."""
    id_aluno = usuario["id_aluno"]
    aluno = buscar_aluno_por_id(id_aluno)
    if aluno is None:
        session.clear()
        return jsonify({"erro": "Sua sessão expirou. Faça login novamente."}), 401
    estado = session.get("avaliacao_inicial")
    if not estado:
        if not avaliacao_inicial.precisa_configurar(aluno) or session.get("avaliacao_pulada"):
            return None
        estado = avaliacao_inicial.criar_estado(aluno)
    idade = personalidades.calcular_idade(aluno.get("data_nascimento"))
    resposta, acao, estado = avaliacao_inicial.responder(estado, mensagem, idade=idade)
    session["avaliacao_inicial"] = estado
    atualizado = None
    if acao == 'confirmar':
        dados = estado['dados']
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            # O modo +18 só pode ser confirmado com idade válida, mesmo se a
            # sessão da avaliação estiver desatualizada.
            nascimento = dados.get('data_nascimento') or aluno.get('data_nascimento')
            idade_final = personalidades.calcular_idade(nascimento)
            permitido, motivo = personalidades.verificar_acesso(dados.get('personalidade') or 'padrao', idade_final)
            if not permitido:
                return jsonify({'erro': motivo}), 403
            cursor.execute(
                """UPDATE aluno SET objetivo = %s, nivel = %s, treinos_semana = %s,
                      minutos_por_sessao = %s, personalidade = %s,
                      data_nascimento = COALESCE(%s, data_nascimento) WHERE id_aluno = %s""",
                (dados['objetivo'], dados['nivel'], dados['treinos_semana'],
                 dados.get('minutos_por_sessao'), dados.get('personalidade') or 'padrao',
                 nascimento, id_aluno)
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()
        atualizado = formatar_aluno_publico(buscar_aluno_por_id(id_aluno))
        session['usuario'] = atualizado
        session.pop('avaliacao_inicial', None)
        resposta = ('Pronto! Seu perfil foi atualizado. Posso usar essas informações '
                    'para sugerir treinos adequados ao seu objetivo. O que gostaria de treinar?')
    elif acao == 'pular':
        session.pop('avaliacao_inicial', None)
        session['avaliacao_pulada'] = True
    # Histórico da avaliação também fica registrado para reaparecer após recarregar.
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_mensagens (id_aluno, role, content, eh_treino) VALUES (%s, 'user', %s, 0)",
            (id_aluno, mensagem))
        cursor.execute(
            "INSERT INTO chat_mensagens (id_aluno, role, content, eh_treino) VALUES (%s, 'assistant', %s, 0)",
            (id_aluno, resposta))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    payload = {'resposta': resposta, 'modo': 'configuracao' if acao == 'continuar' else 'aguardando',
               'eh_treino': False, 'avaliacao_pendente': acao == 'continuar',
               'opcoes': avaliacao_inicial.opcoes(estado) if acao == 'continuar' else [],
               'etapa': estado['etapa'] if acao == 'continuar' else None}
    if atualizado is not None:
        payload['usuario'] = atualizado
    return jsonify(payload)


@app.post("/api/kiara/voz")
@login_obrigatorio
def api_kiara_voz():
    """Devolve áudio WAV produzido pelo Kokoro local, sem depender do Gemini."""
    corpo = request.get_json(silent=True) or {}
    texto = corpo.get("texto", "")
    if not isinstance(texto, str) or not texto.strip():
        return jsonify({"erro": "Não há texto para transformar em voz."}), 400
    if len(texto) > 12000:
        return jsonify({"erro": "O texto é muito longo para a síntese de voz."}), 413

    try:
        audio = gerar_audio_wav(texto)
        return send_file(
            audio,
            mimetype="audio/wav",
            as_attachment=False,
            download_name="kiara.wav",
            max_age=0,
        )
    except FileNotFoundError:
        return jsonify({
            "erro": "A voz neural ainda não foi instalada. Execute configurar.ps1 na raiz do FitFATEC."
        }), 503
    except RuntimeError as erro:
        app.logger.exception("[Kiara][voz] Dependência ou motor de voz indisponível")
        return jsonify({"erro": str(erro)}), 503
    except Exception:
        app.logger.exception("[Kiara][voz] Falha ao gerar áudio local")
        return jsonify({"erro": "Não foi possível gerar o áudio local da Kiara."}), 500


@app.post("/api/chat")
@login_obrigatorio
def api_chat():
    # Diagnóstico apenas no terminal: tempos, sem mensagens ou dados pessoais.
    _inicio_requisicao = perf_counter()
    _tempos = {}
    corpo = request.get_json(silent=True) or {}
    historico = corpo.get("historico", [])
    if (not isinstance(historico, list) or not historico
            or any(not isinstance(m, dict)
                   or m.get("role") not in ("user", "assistant")
                   or not isinstance(m.get("content"), str)
                   or not 1 <= len(m["content"]) <= 12000 for m in historico)
            or historico[-1]["role"] != "user"):
        return jsonify({"erro": "Dados inválidos"}), 400

    # Mantém apenas as últimas 30 mensagens para enviar à IA sem estourar o limite
    historico = historico[-30:]

    usuario = session["usuario"]
    if not session.get('avaliacao_pulada'):
        try:
            retorno = _responder_avaliacao_inicial(usuario, historico[-1]['content'])
        except Error:
            return jsonify({'erro': 'Não foi possível salvar a avaliação. Tente novamente.'}), 500
        if retorno is not None:
            return retorno
    aluno = limpar_aluno(corpo.get("aluno", {}))
    if aluno is None:
        return jsonify({'erro': 'Dados do aluno inválidos.'}), 400
    id_aluno = usuario["id_aluno"]
    aluno["nome"] = usuario.get("nome", "Aluno")
    ultima_msg_user = historico[-1]["content"]

    # Dev 3: personalidade da Kiara. Lê o aluno no banco a cada mensagem para a trava
    # do modo +18 valer mesmo com a sessão desatualizada; se o banco falhar, usa a sessão.
    _inicio_perfil = perf_counter()
    try:
        dados_aluno = buscar_aluno_por_id(id_aluno) or usuario
    except Exception:
        dados_aluno = usuario
    finally:
        _tempos["perfil_mysql"] = perf_counter() - _inicio_perfil
    idade_real = personalidades.calcular_idade(dados_aluno.get("data_nascimento"))
    if idade_real is not None:
        aluno["idade"] = idade_real
    aluno["personalidade"] = personalidades.resolver(dados_aluno.get("personalidade"), idade_real)
    # Dev 3: treinos salvos do aluno, para a Kiara saber qual é o treino de hoje.
    _inicio_treinos = perf_counter()
    try:
        aluno["plano_semana"] = resumo_treinos_para_kiara(id_aluno)
    finally:
        _tempos["treinos_mysql"] = perf_counter() - _inicio_treinos

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

        editar_id = corpo.get('editar_treino_id')
        _inicio_edicao = perf_counter()
        if editar_id:
            try:
                editar_id = int(editar_id)
                conn_ctx = get_db_connection()
                cur_ctx = conn_ctx.cursor(dictionary=True)
                try:
                    cur_ctx.execute('SELECT id,titulo FROM treinos WHERE id=%s AND aluno_id=%s AND ativo=1',
                                    (editar_id,id_aluno))
                    ficha_ctx = cur_ctx.fetchone()
                    if not ficha_ctx:
                        return jsonify({'erro':'Ficha não encontrada para edição.'}),404
                    cur_ctx.execute('SELECT nome_exercicio,series,repeticoes,descanso_segundos '
                                       'FROM treino_exercicios WHERE treino_id=%s ORDER BY ordem',(editar_id,))
                    itens_ctx = cur_ctx.fetchall()
                finally:
                    cur_ctx.close();conn_ctx.close()
                ficha_texto = '\n'.join(f"- {x['nome_exercicio']}: {x['series']}x{x['repeticoes']} ({x['descanso_segundos']}s)" for x in itens_ctx)
                contexto = (f"Estamos editando a ficha existente '{ficha_ctx['titulo']}' (ID {editar_id}).\n"
                            f"Exercícios atuais:\n{ficha_texto}\n"
                            "Responda ao pedido do aluno devolvendo a FICHA COMPLETA revisada em linhas "
                            "'- Nome: 3x10 (60s)'; preserve o que ele não pediu para mudar. "
                            "Não grave nada automaticamente; o aluno confirmará pelo botão.")
                historico_para_ia = [{'role':'user','content':contexto}]+historico_para_ia
            except (TypeError,ValueError):
                return jsonify({'erro':'Identificador de treino inválido.'}),400
        _tempos["contexto_edicao_mysql"] = perf_counter() - _inicio_edicao

        _inicio_resposta = perf_counter()
        texto_ficha_anterior = None
        try:
            if _pedido_para_salvar_ficha_anterior(ultima_msg_user):
                texto_ficha_anterior = _ultima_ficha_no_historico(historico)
                resposta = (
                    "Organizei a sugestão anterior para salvar, sem acrescentar exercícios:\n\n"
                    + texto_ficha_anterior
                    if texto_ficha_anterior else
                    "A sugestão anterior não tinha exercícios e durações/repetições "
                    "suficientes para montar uma ficha. Diga qual exercício e por "
                    "quanto tempo quer fazer; não vou inventar outro treino."
                )
                modo, plano = "local", plano_anterior
            else:
                resposta, modo, plano = responder_com_plano(aluno, historico_para_ia, plano_anterior)
        finally:
            _tempos["resposta_kiara"] = perf_counter() - _inicio_resposta
        session["plano_kiara"] = plano

        eh_treino = int(_parece_ficha_chat(resposta))

        _inicio_gravacao = perf_counter()
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
            _tempos["salvar_chat_mysql"] = perf_counter() - _inicio_gravacao

        return jsonify({
            "resposta": resposta,
            "modo": modo,
            "eh_treino": bool(eh_treino),
            "personalidade": aluno["personalidade"],  # Dev 3: modo usado nesta resposta
            "treino_anterior_texto": texto_ficha_anterior,
        })
    except Exception as e:
        print("Erro no chat:", e)
        return jsonify({"erro": "A Kiara não conseguiu responder agora. Tente novamente."}), 500
    finally:
        _tempos["total"] = perf_counter() - _inicio_requisicao
        print("[Kiara][tempos Flask] " + " | ".join(
            f"{etapa}={segundos:.3f}s" for etapa, segundos in _tempos.items()
        ), flush=True)

@app.post("/api/chat/limpar")
@login_obrigatorio
def api_limpar_chat():
    """Remove somente as mensagens do aluno autenticado; não mexe em fichas nem agendamentos."""
    id_aluno = session["usuario"]["id_aluno"]
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM chat_mensagens WHERE id_aluno = %s", (id_aluno,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    except Exception:
        return jsonify({"erro": "Não foi possível limpar a conversa. Tente novamente."}), 500
    finally:
        conn.close()
    session.pop("plano_kiara", None)
    session.pop("avaliacao_inicial", None)
    return jsonify({"ok": True, "mensagem": "Histórico da conversa removido."}), 200


# ---------------------------------------------------------------- Personalidade da Kiara (Dev 3)
# O aluno escolhe como a Kiara fala com ele (ver personalidades.py). A escolha fica em
# aluno.personalidade; o modo "Sem filtro" exige 18 anos pela data de nascimento do perfil.

def salvar_personalidade(id_aluno, codigo):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE aluno SET personalidade = %s WHERE id_aluno = %s", (codigo, id_aluno))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def resumo_treinos_para_kiara(id_aluno):
    """Texto com os treinos salvos do aluno para o prompt. Vazio se não houver ou se o banco falhar."""
    try:
        conn = get_db_connection()
    except Exception:
        return ""
    try:
        return plano_semanal.resumo_para_kiara(conn, id_aluno)
    except Exception:
        return ""
    finally:
        conn.close()


@app.get("/api/personalidades")
@login_obrigatorio
def api_personalidades():
    """Lista os modos para o seletor, dizendo quais estão liberados para este aluno."""
    try:
        aluno = buscar_aluno_por_id(session["usuario"]["id_aluno"]) or session["usuario"]
    except Error:
        aluno = session["usuario"]
    idade = personalidades.calcular_idade(aluno.get("data_nascimento"))
    return jsonify({
        "ok": True,
        "atual": personalidades.resolver(aluno.get("personalidade"), idade),
        "idade": idade,
        "personalidades": personalidades.listar_para_aluno(idade),
    })


@app.put("/api/perfil/personalidade")
@app.post("/api/perfil/personalidade")
@login_obrigatorio
def api_salvar_personalidade():
    """Salva o modo escolhido. Responde 403 se o modo for +18 e o aluno não puder usar."""
    corpo = request.get_json(silent=True) or {}
    codigo = str(corpo.get("personalidade") or "").strip().lower()
    if codigo not in personalidades.PERSONALIDADES:
        return jsonify({"ok": False, "erro": "Personalidade inválida."}), 400

    id_aluno = session["usuario"]["id_aluno"]
    try:
        aluno = buscar_aluno_por_id(id_aluno) or {}
        # A idade vem do banco, nunca do navegador, para a trava não ser contornada.
        idade = personalidades.calcular_idade(aluno.get("data_nascimento"))
        liberada, motivo = personalidades.verificar_acesso(codigo, idade)
        if not liberada:
            return jsonify({"ok": False, "erro": motivo}), 403
        salvar_personalidade(id_aluno, codigo)
    except Error:
        return jsonify({"ok": False, "erro": "Erro ao salvar a personalidade."}), 500

    session["usuario"]["personalidade"] = codigo
    session.modified = True
    escolhida = personalidades.PERSONALIDADES[codigo]
    return jsonify({
        "ok": True,
        "personalidade": codigo,
        "nome": escolhida["nome"],
        "saudacao": escolhida["saudacao"],
        "mensagem": f"Kiara agora está no modo {escolhida['nome']}.",
    })


# ---------------------------------------------------------------- Treinos
@app.get("/api/serie")
def api_serie():
    nivel = request.args.get("nivel", "iniciante")
    objetivo = request.args.get("objetivo", "saúde geral")
    return jsonify(catalogo.montar_serie(nivel, objetivo))


# ---------------------------------------------------------------- Agendamento
HORARIOS = [f"{h:02d}:00" for h in range(6, 22)]
CAPACIDADE_POR_HORARIO = 10
def _parse_data(texto):
    try:
        return date.fromisoformat(str(texto))
    except (ValueError, TypeError):
        return None


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


def recorrencias_proximas(conn, aluno_id, dias=30):
    # Ocorrencias planejadas para dashboard e perfil, sem criar linhas infinitas.
    inicio=date.today(); fim=inicio+timedelta(days=dias)
    c=conn.cursor(dictionary=True)
    try:
        c.execute('''SELECT r.*,t.titulo AS treino_titulo FROM treino_recorrencia r
                     JOIN treinos t ON t.id=r.treino_id
                     WHERE r.aluno_id=%s AND t.ativo=1''',(aluno_id,))
        regras=c.fetchall()
        c.execute('''SELECT e.recorrencia_id,e.data_treino FROM treino_recorrencia_excecao e
                     JOIN treino_recorrencia r ON e.recorrencia_id=r.id
                     WHERE r.aluno_id=%s AND e.data_treino BETWEEN %s AND %s''',
                  (aluno_id,inicio,fim))
        excecoes={(e['recorrencia_id'],e['data_treino']) for e in c.fetchall()}
        eventos=[]
        for r in regras:
            dia=max(inicio,r['data_inicio'])
            dia+=timedelta(days=(r['dia_semana']-dia.weekday())%7)
            while dia<=fim:
                if (r['id'],dia) not in excecoes:
                    eventos.append({'id_agendamento':f"r:{r['id']}:{dia.isoformat()}",
                                    'recorrencia_id':r['id'],'treino_id':r['treino_id'],
                                    'treino_titulo':r['treino_titulo'],'data_treino':dia,
                                    'horario':r['horario'],'status':'planejado','recorrente':True})
                dia+=timedelta(days=7)
        return sorted(eventos,key=lambda a:(a['data_treino'],str(a.get('horario') or '')))
    finally:c.close()


# ---------------------------------------------------------------- Dashboard
@app.get("/api/dashboard")
@login_obrigatorio
def api_dashboard():
    usuario = session["usuario"]
    aluno = buscar_aluno_por_id(usuario["id_aluno"])

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # O treino do dia vem do calendário real, não de um dia fixo na ficha.
        cursor.execute("""SELECT t.* FROM agendamento a
            JOIN treinos t ON t.id = a.treino_id
            WHERE a.id_aluno = %s AND a.data_treino = CURDATE()
              AND a.status = 'planejado' AND t.ativo = 1
            ORDER BY a.horario IS NULL, a.horario, a.id_agendamento LIMIT 1""",
            (aluno["id_aluno"],))
        treino_hoje = cursor.fetchone()
        agenda_recorrente=recorrencias_proximas(conn,aluno['id_aluno'])
        if not treino_hoje:
            rec_hoje=next((a for a in agenda_recorrente if a['data_treino']==date.today()),None)
            if rec_hoje:
                cursor.execute('SELECT * FROM treinos WHERE id=%s AND aluno_id=%s',
                               (rec_hoje['treino_id'],aluno['id_aluno']))
                treino_hoje=cursor.fetchone()
        if treino_hoje:
            cursor.execute("SELECT * FROM treino_exercicios WHERE treino_id = %s ORDER BY ordem", (treino_hoje["id"],))
            treino_hoje["exercicios"] = cursor.fetchall()

        cursor.execute("""SELECT a.*, t.titulo AS treino_titulo, t.dia_semana AS treino_dia,
                   t.plano_id, COALESCE(p.cor_hex, t.cor_hex) AS cor_hex FROM agendamento a
            JOIN treinos t ON t.id = a.treino_id
            LEFT JOIN plano_treino p ON p.id = t.plano_id
            WHERE a.id_aluno = %s AND a.data_treino >= CURDATE() AND a.status = 'planejado'
            ORDER BY a.data_treino, a.horario IS NULL, a.horario LIMIT 3""", (aluno["id_aluno"],))
        proximos = cursor.fetchall() + agenda_recorrente
        proximos.sort(key=lambda a:(a['data_treino'],str(a.get('horario') or '')))
        proximos=proximos[:3]
        cursor.execute("""SELECT id, titulo, subtitulo, dia_semana, criado_em FROM treinos
            WHERE aluno_id = %s AND ativo = 1 ORDER BY criado_em DESC, id DESC LIMIT 1""", (aluno["id_aluno"],))
        ultimo_treino = cursor.fetchone()
        return jsonify({
            "ok": True,
            "aluno": formatar_aluno_publico(aluno),
            "treino_hoje": treino_hoje,
            "ultimo_treino": ultimo_treino,
            "proximo_treino": _serializar_agendamento(proximos[0]) if proximos else None,
            "proximos_agendamentos": [_serializar_agendamento(a) for a in proximos]
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
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS qtd FROM treino_execucoes WHERE aluno_id = %s", (aluno["id_aluno"],))
        concluido = cursor.fetchone()["qtd"]
        cursor.execute("""SELECT COUNT(*) AS qtd FROM agendamento WHERE id_aluno = %s
            AND status = 'planejado' AND data_treino >= CURDATE()""", (aluno["id_aluno"],))
        programados = cursor.fetchone()["qtd"]
        ocorrencias=recorrencias_proximas(conn,aluno['id_aluno'])
        programados+=len(ocorrencias)
        cursor.execute("""SELECT a.data_treino, a.horario, t.titulo AS treino_titulo
            FROM agendamento a JOIN treinos t ON t.id = a.treino_id
            WHERE a.id_aluno = %s AND a.status = 'planejado' AND a.data_treino >= CURDATE()
            ORDER BY a.data_treino, a.horario IS NULL, a.horario LIMIT 1""", (aluno["id_aluno"],))
        proximo = cursor.fetchone()
        if ocorrencias and (proximo is None or ocorrencias[0]['data_treino']<proximo['data_treino']):
            proximo=ocorrencias[0]
    finally:
        cursor.close()
        conn.close()

    return jsonify({
        "ok": True,
        "aluno": formatar_aluno_publico(aluno),
        "proximo_treino": _serializar_agendamento(proximo),
        "progresso": {
            "treinos_concluidos": concluido,
            "frequencia": (f"{aluno['treinos_semana']}/sem (meta)" if aluno.get("treinos_semana") else "Não definida"),
            "treinos_programados": programados
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

    # Dev 3: data de nascimento (libera o modo +18 da Kiara). Vazio apaga a data.
    if "data_nascimento" in corpo:
        texto_nascimento = str(corpo.get("data_nascimento") or "").strip()
        if texto_nascimento:
            nascimento = _parse_data(texto_nascimento)
            idade = personalidades.calcular_idade(nascimento) if nascimento else None
            if idade is None or not 5 <= idade <= 120:
                return jsonify({"ok": False, "erro": "Data de nascimento inválida."}), 400
            corpo["data_nascimento"] = nascimento
        else:
            corpo["data_nascimento"] = None

    campos_permitidos = ['nome', 'email', 'telefone', 'objetivo', 'nivel', 'treinos_semana', 'modalidade_principal', 'notificacoes', 'acessibilidade', 'tema',
                         'data_nascimento']  # Dev 3: data_nascimento
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

    # Dev 3: se a nova data de nascimento tirar o acesso ao modo escolhido (+18),
    # a Kiara volta para o modo padrão também no banco.
    escolhido = aluno_atualizado.get("personalidade") or personalidades.PADRAO
    idade_atual = personalidades.calcular_idade(aluno_atualizado.get("data_nascimento"))
    if personalidades.resolver(escolhido, idade_atual) != escolhido:
        salvar_personalidade(usuario["id_aluno"], personalidades.PADRAO)
        aluno_atualizado["personalidade"] = personalidades.PADRAO

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
        cursor.execute("""SELECT t.*, p.titulo AS plano_titulo, p.dias_semana AS plano_dias,
                          p.minutos_sessao AS plano_minutos, p.cor_hex AS plano_cor FROM treinos t
                          LEFT JOIN plano_treino p ON p.id=t.plano_id
                          WHERE t.aluno_id = %s AND t.ativo = 1 ORDER BY t.id DESC""", (id_aluno,))
        treinos = cursor.fetchall()
        for t in treinos:
            cursor.execute("SELECT * FROM treino_exercicios WHERE treino_id = %s ORDER BY ordem", (t["id"],))
            t["exercicios"] = cursor.fetchall()
        return jsonify({"ok": True, "treinos": treinos})
    finally:
        cursor.close()
        conn.close()


@app.get("/api/planos")
@login_obrigatorio
def api_listar_planos():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""SELECT p.* FROM plano_treino p
                        WHERE p.aluno_id=%s AND EXISTS (
                        SELECT 1 FROM treinos t WHERE t.plano_id=p.id AND t.ativo=1)
                        ORDER BY p.id DESC""",
                    (session['usuario']['id_aluno'],))
        return jsonify({'ok': True, 'planos': cur.fetchall()})
    finally:
        cur.close()
        conn.close()


# Cores são configuráveis: uma por plano, ou por ficha avulsa.
# Não modifica outras fichas nem agendamentos; as consultas sempre leem a cor atual.
@app.patch("/api/planos/<int:plano_id>/cor")
@login_obrigatorio
def api_cor_plano(plano_id):
    cor = str((request.get_json(silent=True) or {}).get('cor_hex', '')).strip().upper()
    if not re.fullmatch(r'#[0-9A-F]{6}', cor):
        return jsonify({'erro': 'Escolha uma cor hexadecimal válida.'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE plano_treino SET cor_hex=%s WHERE id=%s AND aluno_id=%s',
                       (cor, plano_id, session['usuario']['id_aluno']))
        if cursor.rowcount == 0:
            return jsonify({'erro': 'Plano não encontrado.'}), 404
        conn.commit()
        return jsonify({'ok': True, 'cor_hex': cor})
    finally:
        cursor.close()
        conn.close()


@app.patch("/api/treinos/<int:treino_id>/cor")
@login_obrigatorio
def api_cor_treino_avulso(treino_id):
    cor = str((request.get_json(silent=True) or {}).get('cor_hex', '')).strip().upper()
    if not re.fullmatch(r'#[0-9A-F]{6}', cor):
        return jsonify({'erro': 'Escolha uma cor hexadecimal válida.'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE treinos SET cor_hex=%s WHERE id=%s AND aluno_id=%s AND plano_id IS NULL',
                       (cor, treino_id, session['usuario']['id_aluno']))
        if cursor.rowcount == 0:
            return jsonify({'erro': 'Ficha individual não encontrada.'}), 404
        conn.commit()
        return jsonify({'ok': True, 'cor_hex': cor})
    finally:
        cursor.close()
        conn.close()


@app.post("/api/planos/previsualizar")
@login_obrigatorio
def api_previsualizar_plano():
    aluno_id = session['usuario']['id_aluno']
    try:
        aluno = buscar_aluno_por_id(aluno_id)
        if not aluno:
            session.clear()
            return jsonify({'erro':'Sessão inválida.'}),401
        conn = get_db_connection()
        try:
            preview = planejamento.criar_previa(conn, aluno, request.get_json(silent=True) or {})
        finally:
            conn.close()
        return jsonify({'ok': True, 'preview':preview,
                        'assinatura': planejamento.assinar(preview, aluno_id, app.secret_key)})
    except (ValueError, ErroPerfil) as e:
        return jsonify({'erro':str(e)}),400
    except Error:
        return jsonify({'erro':'Falha ao consultar dados do plano.'}),500


@app.post("/api/planos/salvar")
@login_obrigatorio
def api_salvar_plano_aprovado():
    dados = request.get_json(silent=True) or {}
    preview = dados.get('preview')
    aluno_id = session['usuario']['id_aluno']
    if not isinstance(preview,dict) or not planejamento.validar(preview,dados.get('assinatura',''),
                                                               aluno_id,app.secret_key):
        return jsonify({'erro':'Prévia inválida ou expirada. Gere novamente.'}),400
    conn = get_db_connection()
    try:
        id_plano, ids = planejamento.salvar_previa(conn,aluno_id,preview)
        return jsonify({'ok':True,'plano_id':id_plano,'treinos_ids':ids,
                        'mensagem':(f'Plano atualizado com {len(ids)} fichas. A agenda existente não foi alterada.' if preview.get('plano_id_edicao') else f'Novo plano salvo com {len(ids)} fichas. Os anteriores foram mantidos.')}),201
    except Error:
        return jsonify({'erro':'Não foi possível salvar o plano no MySQL.'}),500
    finally:
        conn.close()


@app.post("/api/treinos/gerar-kiara")
@login_obrigatorio
def api_gerar_treino_kiara():
    """Compatibilidade: não salva sem confirmação; devolve uma prévia."""
    return api_previsualizar_plano()

@app.post("/api/treinos/salvar-do-chat")
@login_obrigatorio
def api_salvar_treino_do_chat():
    corpo = request.get_json(silent=True) or {}
    texto_treino = (corpo.get("texto") or "").strip()
    # Duas ou mais seções por dia são um plano, não uma ficha individual.
    secoes_dia = re.findall(
        r"(?:^|\n)\s*(?:[-•*]\s*)?(?:segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)(?:-feira)?\s*[:(—-]",
        texto_treino, re.IGNORECASE,
    )
    if len(secoes_dia) >= 2:
        return jsonify({"erro": "Esta resposta contém treinos para vários dias. Use Gerar plano semanal para revisar as fichas antes de salvar."}), 400
    dia_semana = (corpo.get("dia_semana") or "").strip() or None
    titulo_informado = str(corpo.get("titulo") or "").strip()[:100]
    substituir_id = corpo.get('substituir_id')

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
            ) and not re.search(r"\d+\s*[xX×]\s*\d+", limpa) and len(limpa) <= 65:
                titulo_detectado = limpa.rstrip(":")
                continue

            # Verifica se a linha parece um exercício (tem ":", "—", " - " ou padrão "3x10" / "min")
            tem_padrao_sr = bool(re.search(r"\d+\s*[xX×]\s*\d+", limpa))
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
                m_split = re.search(r"(\(?\d+\s*[xX×]\s*[\d\s\-–]+.*|\(?\d+\s*min.*)", limpa, re.IGNORECASE)
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

            m_sr = re.search(
                r"(\d+)\s*[xX×]\s*(\d+(?:\s*[\-–]\s*\d+)?\s*(?:min(?:utos?)?|s(?:eg(?:undos?)?)?)?\b)",
                detalhes, re.IGNORECASE,
            )
            if m_sr:
                series = int(m_sr.group(1))
                repeticoes = m_sr.group(2).strip() or "10"
            elif "min" in detalhes.lower():
                series = 1
                m_min = re.search(r"(\d+\s*min)", detalhes, re.IGNORECASE)
                repeticoes = m_min.group(1) if m_min else "8 min"

            m_desc = re.search(r"(?:descanso\s*(\d+)|\((\d+)\s*s\))", detalhes, re.IGNORECASE)
            if m_desc:
                descanso = int(m_desc.group(1) or m_desc.group(2))
            elif "alternando" in detalhes.lower() or "intercalando" in detalhes.lower():
                # Intervalos estão contidos na duração total, não são descanso
                # adicional entre séries; protocolo integral fica em observacoes.
                descanso = 0

            exercicios_para_salvar.append({
                "nome_exercicio": nome_ex[:80],
                "series": series,
                "repeticoes": repeticoes[:25],
                "descanso_segundos": descanso,
            })

    if not exercicios_para_salvar:
        return jsonify({"ok": False, "erro": "Não encontrei uma ficha com exercícios, séries e repetições nesta resposta."}), 400

    id_aluno = session["usuario"]["id_aluno"]
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Conta quantos treinos o aluno já tem para numerar caso não tenha título específico
        cursor.execute("SELECT COUNT(*) FROM treinos WHERE aluno_id = %s AND ativo = 1", (id_aluno,))
        qtd_existente = cursor.fetchone()[0]
        titulo_final = titulo_informado or titulo_detectado or f"Treino Kiara #{qtd_existente + 1}"

        if substituir_id:
            try:
                substituir_id = int(substituir_id)
            except (TypeError, ValueError):
                return jsonify({'erro':'Treino inválido.'}),400
            cursor.execute('SELECT id,titulo FROM treinos WHERE id=%s AND aluno_id=%s AND ativo=1 FOR UPDATE',
                           (substituir_id,id_aluno))
            atual = cursor.fetchone()
            if not atual:
                return jsonify({'erro':'Ficha não encontrada.'}),404
            treino_id = substituir_id
            cursor.execute("UPDATE treinos SET subtitulo=%s, observacoes=%s WHERE id=%s",
                           (f'{len(exercicios_para_salvar)} exercícios', texto_treino[:1000],treino_id))
            cursor.execute('DELETE FROM treino_exercicios WHERE treino_id=%s',(treino_id,))
            titulo_final = atual[1]
        else:
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
        return jsonify({"ok": True, "treino_id": treino_id, "mensagem": f"{titulo_final} atualizado!" if substituir_id else f"{titulo_final} salvo em Meus treinos!"})
    except Exception:
        conn.rollback()
        raise
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
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


@app.post("/api/treinos/<int:treino_id>/concluir")
@login_obrigatorio
def api_concluir_treino(treino_id):
    """Registra execução mantendo a ficha salva para uso futuro."""
    id_aluno = session["usuario"]["id_aluno"]
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM treinos WHERE id = %s AND aluno_id = %s AND ativo = 1",
                       (treino_id, id_aluno))
        if not cursor.fetchone():
            return jsonify({"ok": False, "erro": "Treino não encontrado."}), 404
        cursor.execute("INSERT INTO treino_execucoes (treino_id, aluno_id) VALUES (%s, %s)",
                       (treino_id, id_aluno))
        conn.commit()
        return jsonify({"ok": True, "mensagem": "Execução registrada; treino mantido na lista."}), 201
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def _impacto_exclusao(cur, aluno_id, ids):
    if not ids: return {'agendamentos_futuros': 0, 'repeticoes': 0}
    placeholders = ','.join(['%s'] * len(ids))
    cur.execute(f"SELECT COUNT(*) FROM agendamento WHERE id_aluno=%s AND treino_id IN ({placeholders}) AND data_treino >= %s",
                (aluno_id, *ids, date.today()))
    agendamentos = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM treino_recorrencia WHERE aluno_id=%s AND treino_id IN ({placeholders})",
                (aluno_id, *ids))
    return {'agendamentos_futuros': agendamentos, 'repeticoes': cur.fetchone()[0]}


def _arquivar_treinos(cur, aluno_id, ids, cancelar):
    impacto = _impacto_exclusao(cur, aluno_id, ids)
    if (impacto['agendamentos_futuros'] or impacto['repeticoes']) and not cancelar:
        return impacto
    if not ids:
        return impacto
    placeholders = ','.join(['%s'] * len(ids))
    if cancelar:
        cur.execute(f"DELETE FROM agendamento WHERE id_aluno=%s AND treino_id IN ({placeholders}) AND data_treino >= %s",
                    (aluno_id, *ids, date.today()))
        cur.execute(f"DELETE FROM treino_recorrencia WHERE aluno_id=%s AND treino_id IN ({placeholders})",
                    (aluno_id, *ids))
    # Arquivar mantém a definição e treino_execucoes: exclusão definitiva seria ON DELETE CASCADE.
    cur.execute(f"UPDATE treinos SET ativo=0 WHERE aluno_id=%s AND id IN ({placeholders})",
                (aluno_id, *ids))
    return impacto


@app.delete('/api/treinos/<int:treino_id>')
@login_obrigatorio
def api_deletar_treino(treino_id):
    aluno_id = session['usuario']['id_aluno']
    cancelar = request.args.get('cancelar_programacoes') == '1'
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute('SELECT id FROM treinos WHERE id=%s AND aluno_id=%s AND ativo=1 FOR UPDATE',
                    (treino_id, aluno_id))
        if not cur.fetchone(): return jsonify({'erro':'Ficha não encontrada.'}),404
        impacto = _arquivar_treinos(cur, aluno_id, [treino_id], cancelar)
        if (impacto['agendamentos_futuros'] or impacto['repeticoes']) and not cancelar:
            conn.rollback()
            return jsonify({'erro':'Esta ficha tem programações futuras. Confirme o cancelamento para arquivá-la.',
                            'impacto':impacto}),409
        conn.commit()
        return jsonify({'ok':True,'mensagem':'Ficha removida da biblioteca; execuções anteriores preservadas.', 'impacto':impacto})
    except Exception:
        conn.rollback(); raise
    finally:cur.close();conn.close()


@app.delete('/api/planos/<int:plano_id>')
@login_obrigatorio
def api_excluir_plano(plano_id):
    aluno_id = session['usuario']['id_aluno']
    cancelar = request.args.get('cancelar_programacoes') == '1'
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute('SELECT id FROM plano_treino WHERE id=%s AND aluno_id=%s FOR UPDATE', (plano_id,aluno_id))
        if not cur.fetchone():return jsonify({'erro':'Plano não encontrado.'}),404
        cur.execute('SELECT id FROM treinos WHERE plano_id=%s AND aluno_id=%s AND ativo=1 FOR UPDATE', (plano_id,aluno_id))
        ids = [t[0] for t in cur.fetchall()]
        if not ids:return jsonify({'erro':'Plano já removido da biblioteca.'}),404
        impacto = _arquivar_treinos(cur, aluno_id, ids, cancelar)
        if (impacto['agendamentos_futuros'] or impacto['repeticoes']) and not cancelar:
            conn.rollback()
            return jsonify({'erro':'Este plano tem programações futuras. Confirme para cancelá-las e arquivar todas as fichas.',
                            'impacto':impacto}),409
        conn.commit()
        return jsonify({'ok':True,'mensagem':f'Plano removido da biblioteca ({len(ids)} fichas arquivadas).', 'impacto':impacto})
    except Exception:
        conn.rollback();raise
    finally:cur.close();conn.close()


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


# ---------------------------------------------------------------- Calendário pessoal de treinos
@app.get("/api/agendamentos")
@login_obrigatorio
def api_listar_agendamentos():
    id_aluno = session["usuario"]["id_aluno"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""SELECT a.*, t.titulo AS treino_titulo, t.dia_semana AS treino_dia,
                   t.plano_id, COALESCE(p.cor_hex, t.cor_hex) AS cor_hex FROM agendamento a
            JOIN treinos t ON t.id = a.treino_id
            LEFT JOIN plano_treino p ON p.id = t.plano_id
            WHERE a.id_aluno = %s ORDER BY a.data_treino ASC, a.horario ASC, a.id_agendamento""", (id_aluno,))
        registros = [_serializar_agendamento(a) for a in cursor.fetchall()]
        hoje = date.today().isoformat()
        proximos = [a for a in registros if a["data_treino"] >= hoje and a["status"] == "planejado"]
        # Expandir apenas a janela exibida: a recorrência em si não tem data final.
        inicio = _parse_data(request.args.get('inicio')) or (date.today()-timedelta(days=30))
        fim = _parse_data(request.args.get('fim')) or (date.today()+timedelta(days=120))
        if fim < inicio or (fim-inicio).days > 185:
            return jsonify({'erro':'Intervalo inválido (máximo 186 dias).'}),400
        cursor.execute("""SELECT r.*, t.titulo AS treino_titulo, t.dia_semana AS treino_dia,
                                 t.plano_id, COALESCE(p.cor_hex, t.cor_hex) AS cor_hex
                          FROM treino_recorrencia r JOIN treinos t ON t.id=r.treino_id
                          LEFT JOIN plano_treino p ON p.id=t.plano_id WHERE r.aluno_id=%s""",(id_aluno,))
        recorrencias = cursor.fetchall()
        cursor.execute("""SELECT e.recorrencia_id,e.data_treino,e.status FROM treino_recorrencia_excecao e
                          JOIN treino_recorrencia r ON r.id=e.recorrencia_id
                          WHERE r.aluno_id=%s AND e.data_treino BETWEEN %s AND %s""",
                       (id_aluno,inicio,fim))
        excecoes = {(e['recorrencia_id'],e['data_treino']):e['status'] for e in cursor.fetchall()}
        for rec in recorrencias:
            data = max(inicio,rec['data_inicio'])
            data += timedelta(days=(rec['dia_semana']-data.weekday())%7)
            while data <= fim:
                status = excecoes.get((rec['id'],data),'planejado')
                if status != 'cancelado':
                    virtual = {'id_agendamento':f"r:{rec['id']}:{data.isoformat()}",
                               'recorrencia_id':rec['id'], 'data_treino':data.isoformat(),
                               'horario':rec['horario'], 'treino_id':rec['treino_id'],
                               'treino_titulo':rec['treino_titulo'], 'treino_dia':rec['treino_dia'],
                               'plano_id':rec['plano_id'], 'cor_hex':rec['cor_hex'],
                               'status':status,'recorrente':True}
                    registros.append(_serializar_agendamento(virtual))
                data += timedelta(days=7)
        registros.sort(key=lambda a: (a['data_treino'],str(a.get('horario') or '')))
        hoje = date.today().isoformat()
        proximos = [a for a in registros if a['data_treino'] >= hoje and a['status']=='planejado']
        return jsonify({'ok': True, 'agendamentos':registros, 'proximos_agendamentos':proximos})
    finally:
        cursor.close()
        conn.close()


@app.post("/api/agendamentos")
@login_obrigatorio
def api_agendar_treino():
    corpo = request.get_json(silent=True) or {}
    id_aluno = session["usuario"]["id_aluno"]
    data_treino = _parse_data(corpo.get("data_treino"))
    try:
        treino_id = int(corpo.get("treino_id"))
    except (ValueError, TypeError):
        return jsonify({"ok": False, "erro": "Selecione um treino salvo."}), 400
    if not data_treino or data_treino < date.today():
        return jsonify({"ok": False, "erro": "Escolha uma data válida a partir de hoje."}), 400
    horario = str(corpo.get("horario") or "").strip() or None
    if horario and not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", horario):
        return jsonify({"ok": False, "erro": "Horário inválido. Use HH:MM."}), 400
    observacoes = str(corpo.get("observacoes") or "").strip()[:200] or None
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM treinos WHERE id = %s AND aluno_id = %s AND ativo = 1", (treino_id, id_aluno))
        if not cursor.fetchone():
            return jsonify({"ok": False, "erro": "Treino não encontrado na sua biblioteca."}), 404
        try:
            cursor.execute("""INSERT INTO agendamento (id_aluno, treino_id, data_treino, horario, observacoes)
                VALUES (%s, %s, %s, %s, %s)""", (id_aluno, treino_id, data_treino, horario, observacoes))
            novo_id = cursor.lastrowid
            conn.commit()
        except Error as erro:
            conn.rollback()
            if getattr(erro, "errno", None) == 1062:
                return jsonify({"ok": False, "erro": "Esse treino já foi programado para essa data."}), 409
            raise
        return jsonify({"ok": True, "id_agendamento": novo_id, "mensagem": "Treino incluído na agenda."}), 201
    finally:
        cursor.close()
        conn.close()


@app.post('/api/agendamentos/recorrencias')
@login_obrigatorio
def api_criar_recorrencia():
    """Cria uma ou mais recorrências semanais para uma ficha individual ou do plano.
    O usuário escolhe os dias; a data de início define quando começam.
    """
    body = request.get_json(silent=True) or {}
    inicio = _parse_data(body.get('data_inicio'))
    if not inicio or inicio < date.today():
        return jsonify({'erro': 'Selecione uma data de início válida.'}), 400
    try:
        treino_id = int(body.get('treino_id'))
    except (ValueError, TypeError):
        return jsonify({'erro': 'Escolha um treino salvo.'}), 400
    raw = body.get('dias_semana')
    if raw is None: raw = [inicio.weekday()]  # compatibilidade com clientes antigos
    if not isinstance(raw, list) or not raw or len(raw) > 7:
        return jsonify({'erro': 'Escolha de um a sete dias da semana.'}), 400
    try:
        dias = [int(n) for n in raw]
    except (ValueError, TypeError):
        return jsonify({'erro': 'Dias da semana inválidos.'}), 400
    if any(d < 0 or d > 6 for d in dias) or len(set(dias)) != len(dias):
        return jsonify({'erro': 'Seleção de dias inválida.'}), 400
    aluno_id = session['usuario']['id_aluno']
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute('SELECT id FROM treinos WHERE id=%s AND aluno_id=%s AND ativo=1', (treino_id,aluno_id))
        if not cur.fetchone(): return jsonify({'erro': 'Treino não pertence à sua conta.'}), 404
        cur.execute('SELECT dia_semana FROM treino_recorrencia WHERE aluno_id=%s AND treino_id=%s', (aluno_id,treino_id))
        existentes = {r[0] for r in cur.fetchall()}
        if existentes.intersection(dias):
            return jsonify({'erro': 'Esse treino já possui repetição em um dos dias escolhidos.'}), 409
        for dia in dias:
            primeiro = inicio + timedelta(days=(dia-inicio.weekday())%7)
            cur.execute("INSERT INTO treino_recorrencia (aluno_id,treino_id,dia_semana,data_inicio,horario) VALUES (%s,%s,%s,%s,NULL)", (aluno_id,treino_id,dia,primeiro))
        conn.commit()
        return jsonify({'ok': True, 'mensagem': f'Repetição criada para {len(dias)} dia(s) da semana.'}), 201
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close(); conn.close()


@app.post('/api/agendamentos/recorrencias/plano')
@login_obrigatorio
def api_programar_plano():
    body=request.get_json(silent=True) or {}
    inicio=_parse_data(body.get('data_inicio'))
    if not inicio or inicio<date.today():return jsonify({'erro':'Informe a data inicial.'}),400
    try:plano_id=int(body.get('plano_id'))
    except (ValueError,TypeError):return jsonify({'erro':'Selecione um plano.'}),400
    horario=str(body.get('horario') or '').strip() or None
    if horario and not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',horario):return jsonify({'erro':'Horário inválido.'}),400
    aluno_id=session['usuario']['id_aluno']
    conn=get_db_connection();cur=conn.cursor(dictionary=True)
    try:
        cur.execute('''SELECT t.id,t.dia_semana FROM treinos t JOIN plano_treino p ON p.id=t.plano_id
                       WHERE p.id=%s AND p.aluno_id=%s AND t.ativo=1''',(plano_id,aluno_id))
        fichas=cur.fetchall()
        if not fichas:return jsonify({'erro':'Plano sem fichas para agendar.'}),404
        dia_num={v:k for k,v in plano_semanal.DIAS_BANCO.items()}
        indices={'seg':0,'ter':1,'qua':2,'qui':3,'sex':4,'sab':5,'dom':6}
        for ficha in fichas:
            dia=indices.get(dia_num.get(ficha['dia_semana']))
            if dia is None:return jsonify({'erro':'Há ficha sem dia da semana definido.'}),400
            primeiro=inicio+timedelta(days=(dia-inicio.weekday())%7)
            cur.execute('''INSERT INTO treino_recorrencia (aluno_id,treino_id,dia_semana,data_inicio,horario)
                           VALUES (%s,%s,%s,%s,%s)''',(aluno_id,ficha['id'],dia,primeiro,horario))
        conn.commit()
        return jsonify({'ok':True,'mensagem':f'{len(fichas)} fichas programadas semanalmente.'}),201
    except Error as e:
        conn.rollback()
        if getattr(e,'errno',None)==1062:return jsonify({'erro':'Uma das repetições já existe. Nada foi duplicado.'}),409
        raise
    finally:cur.close();conn.close()


def _recorrencia_do_aluno(cur,rec_id,aluno_id):
    cur.execute('SELECT treino_id,dia_semana,data_inicio FROM treino_recorrencia WHERE id=%s AND aluno_id=%s',
                (rec_id,aluno_id))
    return cur.fetchone()


@app.delete('/api/agendamentos/recorrencias/<int:rec_id>')
@login_obrigatorio
def api_excluir_recorrencia(rec_id):
    conn=get_db_connection();cur=conn.cursor()
    try:
        cur.execute('DELETE FROM treino_recorrencia WHERE id=%s AND aluno_id=%s',
                    (rec_id,session['usuario']['id_aluno']))
        achou=cur.rowcount;conn.commit()
        return jsonify({'ok':bool(achou),'mensagem':'Repetição removida; ficha mantida.'}) if achou else (jsonify({'erro':'Repetição não encontrada.'}),404)
    finally:cur.close();conn.close()


@app.route('/api/agendamentos/recorrencias/<int:rec_id>/ocorrencias/<data_iso>',methods=['DELETE','PATCH'])
@login_obrigatorio
def api_excecao_recorrencia(rec_id,data_iso):
    dia=_parse_data(data_iso)
    if not dia:return jsonify({'erro':'Data inválida.'}),400
    aluno_id=session['usuario']['id_aluno']
    conn=get_db_connection();cur=conn.cursor(dictionary=True)
    try:
        rec=_recorrencia_do_aluno(cur,rec_id,aluno_id)
        if not rec or dia<rec['data_inicio'] or dia.weekday()!=rec['dia_semana']:
            return jsonify({'erro':'Ocorrência não encontrada.'}),404
        if request.method=='PATCH' and dia>date.today():
            return jsonify({'erro':'Não é possível concluir treino futuro.'}),400
        status='cancelado' if request.method=='DELETE' else 'concluido'
        cur.execute('SELECT status FROM treino_recorrencia_excecao WHERE recorrencia_id=%s AND data_treino=%s',
                    (rec_id,dia))
        atual=cur.fetchone()
        if atual and atual['status']==status:return jsonify({'erro':'Ocorrência já atualizada.'}),409
        if atual and atual['status']=='concluido':return jsonify({'erro':'Treino concluído não pode ser desfeito.'}),409
        cur.execute('''INSERT INTO treino_recorrencia_excecao (recorrencia_id,data_treino,status)
                       VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE status=VALUES(status)''',
                    (rec_id,dia,status))
        if status=='concluido':
            cur.execute('INSERT INTO treino_execucoes (treino_id,aluno_id) VALUES (%s,%s)',
                        (rec['treino_id'],aluno_id))
        conn.commit()
        return jsonify({'ok':True,'mensagem':'Ocorrência atualizada; ficha e demais semanas preservadas.'})
    except Exception:
        conn.rollback();raise
    finally:cur.close();conn.close()


@app.delete("/api/agendamentos/<int:agendamento_id>")
@login_obrigatorio
def api_excluir_agendamento(agendamento_id):
    # Exclusão física só do compromisso. Nenhum DELETE/UPDATE em 'treinos'.
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM agendamento WHERE id_agendamento = %s AND id_aluno = %s",
                       (agendamento_id, session["usuario"]["id_aluno"]))
        apagados = cursor.rowcount
        conn.commit()
        if not apagados:
            return jsonify({"ok": False, "erro": "Agendamento não encontrado."}), 404
        return jsonify({"ok": True, "mensagem": "Agendamento excluído; treino preservado."})
    finally:
        cursor.close()
        conn.close()


@app.patch("/api/agendamentos/<int:agendamento_id>")
@login_obrigatorio
def api_concluir_agendamento(agendamento_id):
    if (request.get_json(silent=True) or {}).get("status") != "concluido":
        return jsonify({"ok": False, "erro": "Status inválido."}), 400
    id_aluno = session["usuario"]["id_aluno"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""SELECT treino_id, data_treino, status FROM agendamento
            WHERE id_agendamento = %s AND id_aluno = %s FOR UPDATE""", (agendamento_id, id_aluno))
        registro = cursor.fetchone()
        if not registro:
            return jsonify({"ok": False, "erro": "Agendamento não encontrado."}), 404
        if registro["status"] != "planejado":
            return jsonify({"ok": False, "erro": "Treino já foi concluído."}), 409
        if registro["data_treino"] > date.today():
            return jsonify({"ok": False, "erro": "Não é possível concluir um treino futuro."}), 400
        try:
            cursor.execute("UPDATE agendamento SET status = 'concluido' WHERE id_agendamento = %s", (agendamento_id,))
            cursor.execute("INSERT INTO treino_execucoes (treino_id, aluno_id) VALUES (%s, %s)",
                           (registro["treino_id"], id_aluno))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return jsonify({"ok": True, "mensagem": "Treino concluído. Sua ficha continua salva."})
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5000)