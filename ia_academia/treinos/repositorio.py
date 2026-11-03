from datetime import datetime, time, timedelta

from .catalogo import EXERCICIOS
from .gerador import ETAPAS, montar_semana
from .regras import DIAS_SEMANA, RESTRICOES, prescricao

_CODIGO_POR_NOME = {e["nome"]: e["codigo"] for e in EXERCICIOS}


class CatalogoIncompleto(Exception):
    pass


def _ids_exercicios(cursor, nomes):
    if not nomes:
        return {}
    marcadores = ", ".join(["%s"] * len(nomes))
    cursor.execute(f"SELECT id_exercicio, nome FROM exercicio WHERE nome IN ({marcadores})", tuple(nomes))
    return {nome: id_exercicio for id_exercicio, nome in cursor.fetchall()}


def salvar_plano(conn, id_aluno, plano):
    """Grava o plano como o plano ativo do aluno e desativa o anterior. Retorna o id_plano."""
    nomes = {item["nome"] for s in plano["sessoes"] for etapa in ETAPAS for item in s[etapa]}
    perfil = plano["perfil"]
    cursor = conn.cursor()
    try:
        ids = _ids_exercicios(cursor, nomes)
        faltando = nomes - ids.keys()
        if faltando:
            raise CatalogoIncompleto(
                "Exercícios que não estão na tabela exercicio: " + ", ".join(sorted(faltando))
                + ". Rode o script bdd/catalogo_exercicios.sql."
            )

        cursor.execute("UPDATE plano_treino SET ativo = FALSE WHERE id_aluno = %s AND ativo = TRUE", (id_aluno,))
        cursor.execute(
            """
            INSERT INTO plano_treino
                (id_aluno, objetivo, nivel, minutos_por_sessao, local_treino, divisao, observacoes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (id_aluno, perfil["objetivo"], perfil["nivel"], perfil["minutos_por_sessao"],
             perfil["local"], plano["divisao"], "\n".join(plano["observacoes"])),
        )
        id_plano = cursor.lastrowid

        for restricao in perfil["restricoes"]:
            cursor.execute(
                "INSERT INTO plano_restricao (id_plano, restricao) VALUES (%s, %s)",
                (id_plano, restricao),
            )

        for sessao in plano["sessoes"]:
            cursor.execute(
                "INSERT INTO plano_sessao (id_plano, letra, nome, duracao_estimada_min) VALUES (%s, %s, %s, %s)",
                (id_plano, sessao["letra"], sessao["nome"], sessao["duracao_estimada_min"]),
            )
            id_sessao = cursor.lastrowid
            for dia in sessao["dias"]:
                cursor.execute(
                    "INSERT INTO plano_dia (id_plano, dia_semana, letra) VALUES (%s, %s, %s)",
                    (id_plano, DIAS_SEMANA.index(dia) + 1, sessao["letra"]),
                )
            for etapa in ETAPAS:
                for ordem, item in enumerate(sessao[etapa], start=1):
                    cursor.execute(
                        """
                        INSERT INTO plano_item
                            (id_sessao, id_exercicio, etapa, ordem, series, repeticoes, intervalo_seg, observacao)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (id_sessao, ids[item["nome"]], etapa, ordem, item["series"], item["repeticoes"],
                         item["intervalo_seg"], item["observacao"] or None),
                    )
        conn.commit()
        return id_plano
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def buscar_plano_ativo(conn, id_aluno):
    """Monta o plano ativo do aluno no mesmo formato de gerar_plano. Retorna None se não houver."""
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id_plano, objetivo, nivel, minutos_por_sessao, local_treino, divisao, observacoes, criado_em
            FROM plano_treino
            WHERE id_aluno = %s AND ativo = TRUE
            ORDER BY id_plano DESC
            LIMIT 1
            """,
            (id_aluno,),
        )
        plano = cursor.fetchone()
        if plano is None:
            return None
        id_plano = plano["id_plano"]

        cursor.execute("SELECT restricao FROM plano_restricao WHERE id_plano = %s", (id_plano,))
        restricoes = {linha["restricao"] for linha in cursor.fetchall()}

        cursor.execute(
            "SELECT letra, nome, duracao_estimada_min FROM plano_sessao WHERE id_plano = %s ORDER BY letra",
            (id_plano,),
        )
        sessoes = {}
        for linha in cursor.fetchall():
            sessoes[linha["letra"]] = {
                "letra": linha["letra"],
                "nome": linha["nome"],
                "dias": [],
                "duracao_estimada_min": linha["duracao_estimada_min"],
                "aquecimento": [],
                "principal": [],
                "complementar": [],
            }

        cursor.execute(
            "SELECT dia_semana, letra FROM plano_dia WHERE id_plano = %s ORDER BY dia_semana",
            (id_plano,),
        )
        dias = []
        for linha in cursor.fetchall():
            dia = DIAS_SEMANA[linha["dia_semana"] - 1]
            dias.append(dia)
            sessoes[linha["letra"]]["dias"].append(dia)

        cursor.execute(
            """
            SELECT s.letra, i.etapa, e.nome, e.grupo_muscular, i.series, i.repeticoes,
                   i.intervalo_seg, i.observacao
            FROM plano_item i
            JOIN plano_sessao s ON s.id_sessao = i.id_sessao
            JOIN exercicio e ON e.id_exercicio = i.id_exercicio
            WHERE s.id_plano = %s
            ORDER BY s.letra, i.etapa, i.ordem
            """,
            (id_plano,),
        )
        for linha in cursor.fetchall():
            sessoes[linha["letra"]][linha["etapa"]].append({
                "codigo": _CODIGO_POR_NOME.get(linha["nome"]),
                "nome": linha["nome"],
                "grupo": linha["grupo_muscular"],
                "series": linha["series"],
                "repeticoes": linha["repeticoes"],
                "intervalo_seg": linha["intervalo_seg"],
                "observacao": linha["observacao"] or "",
            })
    finally:
        cursor.close()

    lista_sessoes = list(sessoes.values())
    return {
        "id_plano": id_plano,
        "criado_em": plano["criado_em"].isoformat(timespec="seconds"),
        "perfil": {
            "objetivo": plano["objetivo"],
            "nivel": plano["nivel"],
            "dias_semana": dias,
            "minutos_por_sessao": plano["minutos_por_sessao"],
            "local": plano["local_treino"],
            "restricoes": [r for r in RESTRICOES if r in restricoes],
        },
        "divisao": plano["divisao"],
        "prescricao": prescricao(plano["objetivo"], plano["nivel"]),
        "sessoes": lista_sessoes,
        "semana": montar_semana(lista_sessoes),
        "observacoes": plano["observacoes"].split("\n") if plano["observacoes"] else [],
    }


def ocupacao_do_dia(conn, atividade, dia):
    """Quantidade de reservas ativas por horário: {inicio: quantidade}."""
    comeco = datetime.combine(dia, time.min)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT inicio, COUNT(*)
            FROM agendamento
            WHERE atividade = %s AND status = 'agendado' AND inicio >= %s AND inicio < %s
            GROUP BY inicio
            """,
            (atividade, comeco, comeco + timedelta(days=1)),
        )
        return {inicio: quantidade for inicio, quantidade in cursor.fetchall()}
    finally:
        cursor.close()


def listar_agendamentos(conn, id_aluno, desde, ate=None):
    sql = "SELECT id_agendamento, atividade, inicio, status FROM agendamento WHERE id_aluno = %s AND inicio >= %s"
    parametros = [id_aluno, desde]
    if ate is not None:
        sql += " AND inicio < %s"
        parametros.append(ate)
    sql += " ORDER BY inicio"
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, tuple(parametros))
        return cursor.fetchall()
    finally:
        cursor.close()


def buscar_agendamento(conn, id_agendamento, id_aluno):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id_agendamento, atividade, inicio, status
            FROM agendamento
            WHERE id_agendamento = %s AND id_aluno = %s
            """,
            (id_agendamento, id_aluno),
        )
        return cursor.fetchone()
    finally:
        cursor.close()


def criar_agendamento(conn, id_aluno, atividade, inicio):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO agendamento (id_aluno, atividade, inicio) VALUES (%s, %s, %s)",
            (id_aluno, atividade, inicio),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()


def cancelar_agendamento(conn, id_agendamento):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE agendamento SET status = 'cancelado' WHERE id_agendamento = %s",
            (id_agendamento,),
        )
        conn.commit()
    finally:
        cursor.close()
