from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from functools import wraps

from flask import Blueprint, current_app, jsonify, request, session
from mysql.connector import Error as ErroBanco

from . import agenda, repositorio
from .catalogo import buscar_exercicio, filtrar_exercicios, modalidades_aquecimento
from .contexto_ia import contexto_para_ia
from .gerador import gerar_plano, sessao_do_dia
from .regras import ErroPerfil, avaliar_nivel

bp = Blueprint("treinos", __name__)


class ErroRequisicao(ValueError):
    pass


def registrar_treinos(app, conexao_bd):
    """Liga as rotas de treino e agenda ao app Flask, usando a função de conexão do servidor."""
    app.config["TREINOS_CONEXAO_BD"] = conexao_bd
    app.register_blueprint(bp)


@contextmanager
def _conexao():
    conn = current_app.config["TREINOS_CONEXAO_BD"]()
    try:
        yield conn
    finally:
        conn.close()


def _exige_login(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if "usuario" not in session:
            return jsonify({"erro": "Não autenticado."}), 401
        return f(*args, **kwargs)
    return decorada


def _id_aluno():
    return session["usuario"]["id_aluno"]


def _ler_data(texto):
    if not texto:
        return date.today()
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ErroRequisicao("Data inválida. Use o formato AAAA-MM-DD.")


def _ler_data_hora(texto):
    try:
        valor = datetime.fromisoformat(str(texto))
    except ValueError:
        raise ErroRequisicao("Horário inválido. Use o formato AAAA-MM-DDTHH:MM.")
    if valor.tzinfo is not None:
        raise ErroRequisicao("Envie o horário local, sem fuso horário.")
    return valor


def _agendamento_json(a):
    return {
        "id_agendamento": a["id_agendamento"],
        "atividade": a["atividade"],
        "nome_atividade": agenda.ATIVIDADES.get(a["atividade"], {}).get("nome", a["atividade"]),
        "inicio": a["inicio"].isoformat(timespec="minutes"),
        "status": a["status"],
    }


@bp.errorhandler(ErroPerfil)
@bp.errorhandler(agenda.ErroAgenda)
@bp.errorhandler(ErroRequisicao)
def _erro_nos_dados(erro):
    return jsonify({"erro": str(erro)}), 400


@bp.errorhandler(repositorio.CatalogoIncompleto)
def _catalogo_incompleto(erro):
    return jsonify({"erro": str(erro)}), 500


@bp.errorhandler(ErroBanco)
def _erro_banco(erro):
    return jsonify({"erro": "Erro ao acessar o banco de dados."}), 500


@bp.get("/api/treinos/exercicios")
def listar_exercicios():
    filtros = {campo: request.args.get(campo) for campo in ("tipo", "grupo", "nivel", "local", "busca")}
    return jsonify({"exercicios": filtrar_exercicios(**filtros)})


@bp.get("/api/treinos/exercicios/<codigo>")
def detalhar_exercicio(codigo):
    exercicio = buscar_exercicio(codigo)
    if exercicio is None:
        return jsonify({"erro": "Exercício não encontrado."}), 404
    return jsonify({"exercicio": exercicio})


@bp.get("/api/treinos/aquecimento")
def listar_aquecimento():
    return jsonify({"modalidades": modalidades_aquecimento()})


@bp.post("/api/treinos/nivel")
def calcular_nivel():
    return jsonify(avaliar_nivel(request.get_json(silent=True) or {}))


@bp.post("/api/treinos/plano/simular")
def simular_plano():
    return jsonify({"plano": gerar_plano(request.get_json(silent=True) or {})})


@bp.post("/api/treinos/plano")
@_exige_login
def criar_plano():
    plano = gerar_plano(request.get_json(silent=True) or {})
    with _conexao() as conn:
        plano["id_plano"] = repositorio.salvar_plano(conn, _id_aluno(), plano)
    return jsonify({"mensagem": "Plano de treino salvo.", "plano": plano}), 201


@bp.get("/api/treinos/plano")
@_exige_login
def plano_atual():
    with _conexao() as conn:
        plano = repositorio.buscar_plano_ativo(conn, _id_aluno())
    if plano is None:
        return jsonify({"erro": "Você ainda não tem um plano de treino."}), 404
    return jsonify({"plano": plano})


@bp.get("/api/treinos/plano/hoje")
@_exige_login
def treino_do_dia():
    dia = _ler_data(request.args.get("data"))
    with _conexao() as conn:
        plano = repositorio.buscar_plano_ativo(conn, _id_aluno())
    if plano is None:
        return jsonify({"erro": "Você ainda não tem um plano de treino."}), 404
    sessao = sessao_do_dia(plano, dia)
    return jsonify({"data": dia.isoformat(), "descanso": sessao is None, "sessao": sessao})


@bp.get("/api/agenda/atividades")
def listar_atividades():
    return jsonify(agenda.listar_atividades())


@bp.get("/api/agenda/horarios")
def horarios_livres():
    atividade = request.args.get("atividade", "musculacao")
    agenda.validar_atividade(atividade)
    dia = _ler_data(request.args.get("data"))
    with _conexao() as conn:
        ocupacao = repositorio.ocupacao_do_dia(conn, atividade, dia)
    horarios = agenda.horarios_disponiveis(atividade, dia, ocupacao, datetime.now())
    return jsonify({"atividade": atividade, "data": dia.isoformat(), "horarios": horarios})


@bp.get("/api/agenda")
@_exige_login
def meus_agendamentos():
    hoje = datetime.combine(date.today(), time.min)
    with _conexao() as conn:
        lista = repositorio.listar_agendamentos(conn, _id_aluno(), hoje)
    return jsonify({"agendamentos": [_agendamento_json(a) for a in lista]})


@bp.post("/api/agenda")
@_exige_login
def agendar():
    dados = request.get_json(silent=True) or {}
    atividade = dados.get("atividade", "")
    agenda.validar_atividade(atividade)
    inicio = _ler_data_hora(dados.get("inicio"))
    comeco_do_dia = datetime.combine(inicio.date(), time.min)

    with _conexao() as conn:
        do_dia = repositorio.listar_agendamentos(
            conn, _id_aluno(), comeco_do_dia, comeco_do_dia + timedelta(days=1)
        )
        ocupados = repositorio.ocupacao_do_dia(conn, atividade, inicio.date()).get(inicio, 0)
        agenda.validar_agendamento(atividade, inicio, do_dia, ocupados, datetime.now())
        id_agendamento = repositorio.criar_agendamento(conn, _id_aluno(), atividade, inicio)

    novo = {"id_agendamento": id_agendamento, "atividade": atividade, "inicio": inicio, "status": "agendado"}
    return jsonify({"mensagem": "Agendamento confirmado.", "agendamento": _agendamento_json(novo)}), 201


@bp.post("/api/agenda/<int:id_agendamento>/cancelar")
@_exige_login
def cancelar(id_agendamento):
    with _conexao() as conn:
        existente = repositorio.buscar_agendamento(conn, id_agendamento, _id_aluno())
        if existente is None:
            return jsonify({"erro": "Agendamento não encontrado."}), 404
        agenda.validar_cancelamento(existente, datetime.now())
        repositorio.cancelar_agendamento(conn, id_agendamento)
    return jsonify({"mensagem": "Agendamento cancelado."})


def contexto_para_chat(aluno=None):
    """Texto com aquecimento, agenda e plano do aluno para ir no prompt da IA.

    Usa o plano salvo quando o aluno está logado. Se não houver, gera um plano sugerido
    com os dados que o chat já recebe (objetivo, nível e frequência semanal).
    """
    plano, salvo = None, False
    usuario = session.get("usuario")
    if usuario:
        try:
            with _conexao() as conn:
                plano = repositorio.buscar_plano_ativo(conn, usuario["id_aluno"])
            salvo = plano is not None
        except ErroBanco:
            plano = None
    if plano is None and aluno:
        try:
            plano = gerar_plano({
                "objetivo": aluno.get("objetivo"),
                "nivel": aluno.get("nivel"),
                "dias_por_semana": aluno.get("frequencia_semanal") or 3,
            })
        except ErroPerfil:
            plano = None
    return contexto_para_ia(plano, plano_salvo=salvo)
