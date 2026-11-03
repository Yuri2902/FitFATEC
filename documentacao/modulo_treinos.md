# Módulo de treinos e agenda (Dev 3)

Este módulo gera e organiza os planos de treino do FitFATEC, guarda o catálogo de exercícios, aplica as regras de agendamento de aulas e monta o texto com essas informações para a IA usar nas respostas.

## Serviços do trabalho atendidos

| Serviço pedido | Onde está |
|---|---|
| 1. Agendar horário de aula | `treinos/agenda.py` e rotas `/api/agenda` |
| 2. Ofertar série de exercícios segundo a necessidade do aluno | `treinos/gerador.py` e rotas `/api/treinos/plano` |
| 3. Informar modalidades de aquecimento | `MODALIDADES_AQUECIMENTO` em `treinos/catalogo.py` e rota `/api/treinos/aquecimento` |
| 4. Informar treino principal e secundário | Toda sessão do plano tem as etapas `aquecimento`, `principal` e `complementar` |
| 5. Nível de condicionamento | `avaliar_nivel` em `treinos/regras.py` e rota `/api/treinos/nivel` |

## Arquivos

```
ia_academia/
  treinos/
    catalogo.py            83 exercícios (força, cardio, mobilidade, core e alongamento) e modalidades de aquecimento
    regras.py              objetivos, níveis, divisão semanal, séries e repetições, avaliação de nível
    gerador.py             monta o plano a partir do perfil do aluno
    agenda.py              grade de aulas, vagas e regras de agendamento
    repositorio.py         leitura e gravação no MySQL
    contexto_ia.py         texto com plano, aquecimento e agenda para o prompt da IA
    rotas.py               rotas Flask do módulo
    gerar_sql_catalogo.py  gera bdd/catalogo_exercicios.sql a partir do catalogo.py
  personalidades.py        estilos de conversa do assistente (proposta, ver seção própria)
  test_treinos_gerador.py, test_treinos_agenda.py, test_treinos_rotas.py, test_treinos_banco.py, test_personalidades.py
bdd/
  treinos_fitfatec.sql     tabelas novas (proposta para o Dev 5)
  catalogo_exercicios.sql  carga do catálogo na tabela exercicio
```

No `servidor.py` entram só duas linhas para ligar o módulo: o import de `registrar_treinos` e a chamada `registrar_treinos(app, get_db_connection)`. As regras ficam em Python puro e não dependem de Flask nem de banco, então dá para testar e reaproveitar em qualquer lugar.

## Como o plano é montado

### Perfil de entrada

| Campo | Valores aceitos | Padrão |
|---|---|---|
| `objetivo` | `hipertrofia`, `emagrecimento`, `condicionamento`, `saude` (também aceita os textos da tela, como "ganhar massa muscular" e "emagrecer") | obrigatório |
| `nivel` | `iniciante`, `intermediario`, `avancado` (com ou sem acento) | obrigatório |
| `dias_semana` | lista de dias: `["seg", "qua", "sex"]`, `"segunda"`, `1` a `7` | |
| `dias_por_semana` | 1 a 7, usado quando não vem `dias_semana` | 3 |
| `minutos_por_sessao` | 20 a 120 | 60 |
| `local` | `academia` ou `casa` | `academia` |
| `restricoes` | `joelho`, `lombar`, `ombro`, `punho` | nenhuma |

### Divisão semanal

| Dias de treino | Iniciante | Intermediário e avançado |
|---|---|---|
| 1 ou 2 | Corpo inteiro | Corpo inteiro |
| 3 | Corpo inteiro A/B alternado | ABC (empurrar, puxar e pernas) |
| 4 | Superiores e inferiores | Superiores e inferiores |
| 5 ou 6 | 4 dias de musculação, o resto vira recuperação ativa | ABC com superiores e inferiores (5) ou ABC duas vezes (6) |
| 7 | igual a 6, com domingo livre | igual a 6, com domingo livre |

### Séries, repetições e descanso do treino principal

| Objetivo | Iniciante | Intermediário | Avançado |
|---|---|---|---|
| Hipertrofia | 3 x 10-12, 60 s | 4 x 8-12, 75 s | 4 x 6-10, 90 s |
| Emagrecimento | 2 x 12-15, 45 s | 3 x 12-15, 40 s | 3 x 15-20, 30 s |
| Condicionamento | 2 x 12-15, 45 s | 3 x 15, 30 s | 4 x 15-20, 20 s |
| Saúde | 2 x 10-12, 60 s | 3 x 10-12, 60 s | 3 x 8-12, 60 s |

### Etapas de cada sessão

- **Aquecimento:** 5 minutos de cardio leve e 2 exercícios de mobilidade escolhidos pelo foco do dia (superior, inferior ou geral). O primeiro exercício principal leva o aviso de fazer uma série leve antes (aquecimento específico).
- **Principal:** exercícios de força na ordem dos grupos musculares do dia. A quantidade depende do tempo disponível (mínimo 3, máximo 6, 7 ou 8 conforme o nível).
- **Complementar:** 1 ou 2 exercícios de core, cardio no final quando o objetivo pede (emagrecimento, condicionamento e saúde) e alongamento. Se a sessão passar do tempo, o cardio final é encurtado até 10 minutos.

O iniciante só recebe exercícios de nível iniciante, os outros níveis recebem primeiro os do próprio nível. Em casa só entram exercícios sem aparelho ou com elástico. Exercícios que forçam uma região com restrição ficam de fora, e o plano ganha uma observação recomendando procurar um profissional.

## Agenda

- Funcionamento: segunda a sexta das 06:00 às 22:00, sábado das 08:00 às 14:00, domingo fechado.
- Musculação: horário livre, reservas de hora em hora, 25 vagas por horário.
- Treino funcional (45 min, 15 vagas): segunda, quarta e sexta às 07:00 e 19:00.
- Spinning (45 min, 20 vagas): terça e quinta às 07:00 e 20:00, sábado às 09:00.
- Alongamento e mobilidade (30 min, 15 vagas): segunda e quarta às 18:00, sábado às 10:30.
- Regras: reservar com pelo menos 1h de antecedência e até 14 dias antes, horário precisa existir na grade, não pode passar das vagas, não pode coincidir com outra reserva do aluno, no máximo 2 reservas por dia e cancelamento até 2h antes.

Os horários e regras ficam em constantes no topo de `treinos/agenda.py`.

## Rotas

| Método | Rota | Login | O que faz |
|---|---|---|---|
| GET | `/api/treinos/exercicios` | não | Lista o catálogo. Filtros: `tipo`, `grupo`, `nivel`, `local`, `busca` |
| GET | `/api/treinos/exercicios/<codigo>` | não | Detalhe de um exercício, com o texto de execução |
| GET | `/api/treinos/aquecimento` | não | Modalidades de aquecimento com exemplos |
| POST | `/api/treinos/nivel` | não | Calcula o nível a partir de `meses_treinando`, `treinos_por_semana`, `flexoes` e `aguenta_20min_aerobico` |
| POST | `/api/treinos/plano/simular` | não | Gera um plano sem salvar |
| POST | `/api/treinos/plano` | sim | Gera e salva como plano ativo do aluno (o anterior fica inativo) |
| GET | `/api/treinos/plano` | sim | Plano ativo do aluno |
| GET | `/api/treinos/plano/hoje?data=AAAA-MM-DD` | sim | Sessão do dia ou `"descanso": true` |
| GET | `/api/agenda/atividades` | não | Atividades, grade, funcionamento e regras |
| GET | `/api/agenda/horarios?atividade=spinning&data=AAAA-MM-DD` | não | Horários com vagas |
| GET | `/api/agenda` | sim | Reservas do aluno a partir de hoje |
| POST | `/api/agenda` | sim | Reserva. Corpo: `{"atividade": "spinning", "inicio": "2026-11-10T20:00"}` |
| POST | `/api/agenda/<id>/cancelar` | sim | Cancela uma reserva do próprio aluno |

Erros de dados voltam com status 400 e `{"erro": "mensagem"}`, sem login com 401 e falha de banco com 500, no mesmo padrão das rotas de autenticação.

Exemplo de pedido de plano:

```json
POST /api/treinos/plano
{"objetivo": "emagrecer", "nivel": "intermediário", "dias_semana": ["seg", "qua", "sex"], "minutos_por_sessao": 50}
```

Formato da resposta (resumido):

```json
{
  "plano": {
    "id_plano": 4,
    "perfil": {"objetivo": "emagrecimento", "nivel": "intermediario", "dias_semana": ["seg", "qua", "sex"], "minutos_por_sessao": 50, "local": "academia", "restricoes": []},
    "divisao": "ABC (empurrar, puxar e pernas)",
    "prescricao": {"series": 3, "repeticoes": "12-15", "intervalo_seg": 40, "carga": "..."},
    "sessoes": [
      {
        "letra": "A", "nome": "Peito, ombros e tríceps", "dias": ["seg"], "duracao_estimada_min": 50,
        "aquecimento": [{"codigo": "bicicleta_ergometrica", "nome": "Bicicleta ergométrica", "grupo": "cardio", "series": 1, "repeticoes": "5 min", "intervalo_seg": 0, "observacao": "Ritmo leve, só para aquecer."}],
        "principal": ["..."],
        "complementar": ["..."]
      }
    ],
    "semana": [{"dia": "seg", "sessao": "A"}, {"dia": "ter", "sessao": null}],
    "observacoes": ["..."]
  }
}
```

O `codigo` de cada exercício serve para buscar a execução em `/api/treinos/exercicios/<codigo>` e para ligar imagens ou animações na tela.

## Banco de dados (para o Dev 5 revisar)

`bdd/treinos_fitfatec.sql` não altera nenhuma tabela existente, só cria as novas:

| Tabela | Conteúdo | Relacionamento |
|---|---|---|
| `plano_treino` | objetivo, nível, tempo, local, divisão, observações, se está ativo | N:1 com `aluno` |
| `plano_restricao` | restrições usadas para gerar o plano | N:1 com `plano_treino` |
| `plano_sessao` | treino A, B, C... com nome e duração estimada | N:1 com `plano_treino`, letra única por plano |
| `plano_dia` | qual treino cai em cada dia da semana | chave (plano, dia), aponta para a sessão por (plano, letra) |
| `plano_item` | exercício, etapa, ordem, séries, repetições, descanso | N:1 com `plano_sessao` e com `exercicio` |
| `agendamento` | atividade, início, status (`agendado`, `cancelado`, `concluido`, `faltou`) | N:1 com `aluno` |

O catálogo entra na tabela `exercicio` que já existe, usando `nome` (que já é `UNIQUE`) como ligação com o `catalogo.py`. Os detalhes de cada exercício (execução, equipamento, restrições) ficam no Python e saem pela API. Para mudar o catálogo, edite `treinos/catalogo.py` e rode `python -m treinos.gerar_sql_catalogo` para gerar o SQL de novo.

A tabela `treino` atual parece servir para registrar o que o aluno fez (carga e ligação com `frequencia`). A prescrição fica em `plano_item`, então as duas não se sobrepõem. Fica a critério do Dev 5 manter, renomear ou juntar.

Ordem dos scripts: `bd_fitfatec.sql`, `treinos_fitfatec.sql` e `catalogo_exercicios.sql`. O catálogo pode ser rodado mais de uma vez.

## Integração com a IA (para o Dev 2)

`contexto_para_chat(aluno)`, em `treinos/rotas.py`, devolve um texto pronto para o prompt com as modalidades de aquecimento, a agenda com as regras e o plano do aluno. Com o aluno logado, usa o plano salvo. Se não houver plano, gera um sugerido com o `objetivo`, o `nivel` e a `frequencia_semanal` que o `/api/chat` já recebe. Se o banco falhar, o chat continua funcionando com o plano sugerido.

Para ligar, basta passar o texto para o `responder` e incluir no prompt:

```python
from treinos.rotas import contexto_para_chat

resposta = responder(aluno, historico, contexto_treino=contexto_para_chat(aluno))
```

```python
def responder(aluno, historico, contexto_treino=""):
    ...
    instrucoes = f"""
    ...regras atuais...

{contexto_treino}
"""
```

Se depois quiserem que o chatbot faça a reserva sozinho (chamada de função), as funções de `treinos/agenda.py` e `treinos/repositorio.py` já recebem e devolvem dados simples e podem virar ferramentas da IA.

## Personalidades do assistente (proposta)

A ideia é o aluno escolher o jeito que quer ser tratado e o chatbot adaptar o vocabulário. A personalidade muda só o jeito de falar. Exercícios, séries, horários e regras de segurança continuam os mesmos.

| id | Nome | Tom | Exemplo de vocabulário |
|---|---|---|---|
| `amigavel` (padrão) | Amigável | amigável | bora, beleza, mandou bem |
| `formal` | Formal | formal | sem gírias, termos técnicos explicados |
| `maromba` | Maromba | jovem | tá pago, shape, parça, dia de perna, foco total |
| `motivacional` | Motivacional | motivacional | sem desculpa, mais uma série, disciplina |
| `gamer` | Gamer | jovem | missão, XP, upar, chefão, checkpoint, GG |

Todas carregam as mesmas regras fixas: sem palavrão, sem piada com corpo ou peso, gíria de lado quando o assunto é dor ou lesão, e mais acolhimento quando o risco de desistência está alto.

O arquivo `ia_academia/personalidades.py` já tem o catálogo, a saudação de cada estilo e a função `instrucoes_personalidade(id)`, que devolve o trecho do prompt. Ele não está ligado a nada ainda. Onde cada parte entraria:

**Dev 5, banco:** guardar a escolha do aluno.

```sql
ALTER TABLE aluno ADD COLUMN personalidade VARCHAR(20) NOT NULL DEFAULT 'amigavel';
```

**Dev 1, backend:** uma rota para listar os estilos e outra para salvar a escolha do aluno logado, e o `/api/chat` repassando o estilo recebido.

```python
from personalidades import listar_personalidades, personalidade_valida, PADRAO

@app.get("/api/personalidades")
def api_personalidades():
    return jsonify({"padrao": PADRAO, "personalidades": listar_personalidades()})

@app.put("/api/perfil/personalidade")
@login_obrigatorio
def api_salvar_personalidade():
    escolha = (request.get_json(silent=True) or {}).get("personalidade")
    if not personalidade_valida(escolha):
        return jsonify({"erro": "Personalidade inválida."}), 400
    # UPDATE aluno SET personalidade = %s WHERE id_aluno = %s
    return jsonify({"personalidade": escolha})

# no /api/chat
personalidade = corpo.get("personalidade")
resposta = responder(aluno, historico, personalidade=personalidade, contexto_treino=contexto_para_chat(aluno))
```

**Dev 2, IA:** colocar o trecho do estilo no prompt de sistema, depois das regras atuais.

```python
from personalidades import instrucoes_personalidade

def responder(aluno, historico, personalidade=None, contexto_treino=""):
    ...
    instrucoes = f"""
    ...regras atuais...

{instrucoes_personalidade(personalidade)}

{contexto_treino}
"""
```

**Dev 4, tela:** um seletor no perfil ou no chat preenchido por `GET /api/personalidades`, salvando com `PUT /api/perfil/personalidade` e mandando `"personalidade"` junto do corpo do `/api/chat`. A primeira mensagem do chat pode usar a `saudacao` do estilo escolhido.

A persona da assistente pedida no trabalho (nome, aparência, voz institucional) continua uma só. A personalidade escolhida pelo aluno é o modo de conversa dessa mesma assistente.

## Como testar

Na pasta `ia_academia`, com o ambiente virtual ativado:

```
python -m unittest test_treinos_gerador test_treinos_agenda test_treinos_rotas test_personalidades -v
```

Esses testes não precisam de banco nem de chave de API. Para testar a gravação no MySQL de verdade, rode separado, com o banco criado pelos três scripts:

```
$env:TESTAR_BANCO="1"
python -m unittest test_treinos_banco -v
```

As variáveis `DB_HOST`, `DB_NAME`, `DB_USER` e `DB_PASSWORD` são as mesmas do servidor.

O teste cria um aluno temporário, salva e lê planos, faz e cancela uma reserva e apaga tudo no final.
