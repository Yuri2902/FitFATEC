import unicodedata

TIPOS = ("forca", "cardio", "mobilidade", "core", "alongamento")
NIVEIS = ("iniciante", "intermediario", "avancado")


def _ex(codigo, nome, tipo, grupo, nivel, equipamento, casa, execucao,
        restricoes=(), medida="repeticoes"):
    return {
        "codigo": codigo,
        "nome": nome,
        "tipo": tipo,
        "grupo": grupo,
        "nivel": nivel,
        "equipamento": equipamento,
        "casa": casa,
        "medida": medida,
        "restricoes": tuple(restricoes),
        "execucao": execucao,
    }


# Dentro de cada grupo a ordem importa: o gerador escolhe os primeiros da lista.
# Campos: codigo, nome, tipo, grupo, nivel, equipamento, pode fazer em casa, execucao
EXERCICIOS = [
    # Peito
    _ex("supino_maquina", "Supino na máquina", "forca", "peito", "iniciante", "maquina", False,
        "Costas bem apoiadas no encosto. Empurre as alças até quase estender os cotovelos e volte devagar.",
        ("ombro",)),
    _ex("flexao_inclinada", "Flexão de braço inclinada", "forca", "peito", "iniciante", "nenhum", True,
        "Mãos apoiadas em um banco ou mesa firme e corpo reto da cabeça aos pés. Desça o peito até perto do apoio e empurre de volta.",
        ("punho",)),
    _ex("crucifixo_maquina", "Crucifixo na máquina (voador)", "forca", "peito", "iniciante", "maquina", False,
        "Cotovelos levemente dobrados. Feche os braços à frente do peito e abra devagar, sem passar da linha dos ombros.",
        ("ombro",)),
    _ex("supino_reto_barra", "Supino reto com barra", "forca", "peito", "intermediario", "barra", False,
        "Pés firmes no chão e escápulas contraídas. Desça a barra até o meio do peito e empurre para cima. Com carga alta, peça ajuda para alguém acompanhar.",
        ("ombro",)),
    _ex("flexao", "Flexão de braço", "forca", "peito", "intermediario", "nenhum", True,
        "Mãos um pouco mais abertas que os ombros e corpo alinhado. Desça até o peito ficar perto do chão sem deixar o quadril cair.",
        ("punho", "ombro")),
    _ex("supino_inclinado_halteres", "Supino inclinado com halteres", "forca", "peito", "intermediario", "halter", False,
        "Banco inclinado entre 30 e 45 graus. Desça os halteres ao lado do peito e empurre para cima, juntando no alto.",
        ("ombro",)),
    _ex("crossover", "Crossover na polia", "forca", "peito", "intermediario", "polia", False,
        "Um pé à frente e tronco levemente inclinado. Traga as mãos para a frente e para baixo até se encontrarem e volte controlando.",
        ("ombro",)),
    _ex("flexao_declinada", "Flexão de braço declinada", "forca", "peito", "avancado", "nenhum", True,
        "Pés apoiados em um banco ou degrau e mãos no chão. Mantenha o corpo reto e desça o peito com controle.",
        ("punho", "ombro")),
    _ex("mergulho_paralelas", "Mergulho nas paralelas", "forca", "peito", "avancado", "paralelas", False,
        "Corpo levemente inclinado à frente. Desça dobrando os cotovelos até cerca de 90 graus e suba sem travar os braços.",
        ("ombro",)),

    # Costas
    _ex("puxada_frontal", "Puxada frontal na polia", "forca", "costas", "iniciante", "polia", False,
        "Sentado, mãos afastadas na barra. Puxe até a parte de cima do peito levando os cotovelos para baixo e suba devagar."),
    _ex("remada_sentada", "Remada sentada na polia", "forca", "costas", "iniciante", "polia", False,
        "Coluna reta e peito aberto. Puxe o triângulo em direção ao abdômen juntando as escápulas e volte sem curvar as costas."),
    _ex("remada_elastico", "Remada com elástico", "forca", "costas", "iniciante", "elastico", True,
        "Prenda o elástico em um ponto firme na altura do peito. Puxe as pontas até o lado do corpo juntando as escápulas."),
    _ex("superman", "Superman (extensão de tronco no chão)", "forca", "costas", "iniciante", "nenhum", True,
        "Deitado de barriga para baixo, eleve braços e pernas alguns centímetros do chão, segure 2 segundos e desça.",
        ("lombar",)),
    _ex("remada_unilateral", "Remada unilateral com halter (serrote)", "forca", "costas", "intermediario", "halter", False,
        "Um joelho e uma mão apoiados no banco, costas retas. Puxe o halter em direção ao quadril e desça controlando."),
    _ex("remada_curvada", "Remada curvada com barra", "forca", "costas", "intermediario", "barra", False,
        "Joelhos levemente dobrados e tronco inclinado à frente com a coluna reta. Puxe a barra em direção ao umbigo.",
        ("lombar",)),
    _ex("pulldown_bracos_estendidos", "Pulldown com braços estendidos", "forca", "costas", "intermediario", "polia", False,
        "De frente para a polia alta, braços quase retos. Traga a barra até as coxas e volte devagar."),
    _ex("barra_fixa", "Barra fixa", "forca", "costas", "avancado", "barra fixa", False,
        "Pegada um pouco mais aberta que os ombros. Puxe até o queixo passar da barra e desça até estender os braços, sem balançar.",
        ("ombro",)),

    # Ombros
    _ex("desenvolvimento_maquina", "Desenvolvimento na máquina", "forca", "ombros", "iniciante", "maquina", False,
        "Costas apoiadas. Empurre as alças para cima até quase estender os braços e desça até a altura das orelhas.",
        ("ombro",)),
    _ex("elevacao_lateral", "Elevação lateral com halteres", "forca", "ombros", "iniciante", "halter", False,
        "Cotovelos levemente dobrados. Eleve os halteres para os lados até a altura dos ombros e desça devagar.",
        ("ombro",)),
    _ex("elevacao_lateral_elastico", "Elevação lateral com elástico", "forca", "ombros", "iniciante", "elastico", True,
        "Pise no meio do elástico e segure as pontas. Eleve os braços para os lados até a altura dos ombros.",
        ("ombro",)),
    _ex("desenvolvimento_halteres", "Desenvolvimento com halteres", "forca", "ombros", "intermediario", "halter", False,
        "Sentado com as costas apoiadas. Empurre os halteres para cima a partir da altura das orelhas sem arquear a lombar.",
        ("ombro",)),
    _ex("face_pull", "Face pull na polia", "forca", "ombros", "intermediario", "polia", False,
        "Corda na altura do rosto. Puxe em direção à testa abrindo os cotovelos para os lados. Ajuda na postura dos ombros."),
    _ex("flexao_pike", "Flexão pike", "forca", "ombros", "intermediario", "nenhum", True,
        "Quadril alto, formando um V invertido. Dobre os cotovelos levando a cabeça em direção ao chão e empurre de volta.",
        ("ombro", "punho")),
    _ex("desenvolvimento_barra", "Desenvolvimento militar com barra", "forca", "ombros", "avancado", "barra", False,
        "Em pé e com o abdômen firme. Empurre a barra da altura do queixo até acima da cabeça sem jogar o quadril à frente.",
        ("ombro", "lombar")),

    # Bíceps
    _ex("rosca_alternada", "Rosca alternada com halteres", "forca", "biceps", "iniciante", "halter", False,
        "Cotovelos colados ao corpo. Suba um halter de cada vez girando a palma para cima e desça devagar."),
    _ex("rosca_polia", "Rosca na polia", "forca", "biceps", "iniciante", "polia", False,
        "De frente para a polia baixa. Suba a barra até perto dos ombros sem mexer os cotovelos."),
    _ex("rosca_elastico", "Rosca com elástico", "forca", "biceps", "iniciante", "elastico", True,
        "Pise no elástico e segure as pontas com as palmas para a frente. Dobre os cotovelos sem afastá-los do corpo."),
    _ex("rosca_martelo", "Rosca martelo", "forca", "biceps", "iniciante", "halter", False,
        "Palmas viradas uma para a outra o tempo todo. Suba os halteres sem balançar o tronco."),
    _ex("rosca_direta_barra", "Rosca direta com barra", "forca", "biceps", "intermediario", "barra", False,
        "Pegada na largura dos ombros. Suba a barra sem jogar o corpo para trás e desça até quase estender os braços.",
        ("punho",)),
    _ex("rosca_concentrada", "Rosca concentrada", "forca", "biceps", "intermediario", "halter", False,
        "Sentado, cotovelo apoiado na parte de dentro da coxa. Suba o halter devagar e segure um segundo no alto."),

    # Tríceps
    _ex("triceps_polia", "Tríceps na polia", "forca", "triceps", "iniciante", "polia", False,
        "Cotovelos parados ao lado do corpo. Empurre a barra ou a corda para baixo até estender os braços."),
    _ex("triceps_elastico", "Tríceps com elástico", "forca", "triceps", "iniciante", "elastico", True,
        "Prenda o elástico no alto, como numa porta. Com os cotovelos fixos ao lado do corpo, estenda os braços para baixo."),
    _ex("triceps_coice", "Tríceps coice com halter", "forca", "triceps", "iniciante", "halter", False,
        "Tronco inclinado e cotovelo junto ao corpo. Estenda o braço para trás até ficar reto e volte devagar."),
    _ex("triceps_frances", "Tríceps francês com halter", "forca", "triceps", "intermediario", "halter", False,
        "Sentado, segure um halter com as duas mãos acima da cabeça. Desça atrás da cabeça dobrando os cotovelos e suba.",
        ("ombro",)),
    _ex("mergulho_banco", "Mergulho no banco", "forca", "triceps", "intermediario", "nenhum", True,
        "Mãos na beirada de um banco ou cadeira firme. Desça o quadril dobrando os cotovelos até 90 graus e suba.",
        ("ombro", "punho")),
    _ex("flexao_diamante", "Flexão diamante", "forca", "triceps", "avancado", "nenhum", True,
        "Mãos juntas embaixo do peito, formando um losango com os dedos. Desça mantendo os cotovelos perto do corpo.",
        ("punho", "ombro")),

    # Quadríceps
    _ex("leg_press", "Leg press 45", "forca", "quadriceps", "iniciante", "maquina", False,
        "Pés na largura do quadril no meio da plataforma. Desça até os joelhos formarem cerca de 90 graus sem tirar a lombar do encosto.",
        ("joelho",)),
    _ex("agachamento_livre", "Agachamento livre (peso do corpo)", "forca", "quadriceps", "iniciante", "nenhum", True,
        "Pés na largura dos ombros. Leve o quadril para trás e para baixo como se fosse sentar, com os joelhos na direção dos pés.",
        ("joelho",)),
    _ex("cadeira_extensora", "Cadeira extensora", "forca", "quadriceps", "iniciante", "maquina", False,
        "Ajuste o encosto para o joelho ficar alinhado ao eixo da máquina. Estenda as pernas e desça devagar.",
        ("joelho",)),
    _ex("agachamento_goblet", "Agachamento goblet", "forca", "quadriceps", "intermediario", "halter", False,
        "Segure um halter junto ao peito. Agache com o tronco ereto e os cotovelos passando entre os joelhos.",
        ("joelho",)),
    _ex("afundo", "Afundo", "forca", "quadriceps", "intermediario", "nenhum", True,
        "Dê um passo à frente e desça até os dois joelhos formarem cerca de 90 graus. Volte empurrando com a perna da frente.",
        ("joelho",)),
    _ex("agachamento_barra", "Agachamento livre com barra", "forca", "quadriceps", "avancado", "barra", False,
        "Barra apoiada no alto das costas. Desça com a coluna neutra até as coxas ficarem paralelas ao chão e suba empurrando o chão.",
        ("joelho", "lombar")),
    _ex("agachamento_bulgaro", "Agachamento búlgaro", "forca", "quadriceps", "avancado", "nenhum", True,
        "Peito do pé de trás apoiado em um banco. Desça o joelho de trás em direção ao chão e suba com a perna da frente.",
        ("joelho",)),

    # Posterior de coxa
    _ex("mesa_flexora", "Mesa flexora", "forca", "posterior", "iniciante", "maquina", False,
        "Deitado de barriga para baixo, rolo acima do calcanhar. Traga o rolo em direção ao glúteo e desça devagar."),
    _ex("cadeira_flexora", "Cadeira flexora", "forca", "posterior", "iniciante", "maquina", False,
        "Sentado com o rolo atrás das pernas. Puxe para baixo dobrando os joelhos e volte controlando."),
    _ex("bom_dia", "Bom-dia com peso do corpo", "forca", "posterior", "iniciante", "nenhum", True,
        "Mãos atrás da cabeça e joelhos levemente dobrados. Incline o tronco à frente levando o quadril para trás, com a coluna reta.",
        ("lombar",)),
    _ex("stiff_halteres", "Stiff com halteres", "forca", "posterior", "intermediario", "halter", False,
        "Joelhos levemente dobrados. Desça os halteres rente às pernas levando o quadril para trás, sempre com a coluna reta.",
        ("lombar",)),
    _ex("stiff_unilateral", "Stiff unilateral (peso do corpo)", "forca", "posterior", "intermediario", "nenhum", True,
        "Apoiado em uma perna, incline o tronco à frente estendendo a outra perna para trás, com o quadril alinhado.",
        ("lombar",)),
    _ex("levantamento_terra", "Levantamento terra", "forca", "posterior", "avancado", "barra", False,
        "Barra junto às canelas, coluna neutra e abdômen firme. Suba estendendo quadril e joelhos juntos, com a barra rente ao corpo.",
        ("lombar",)),

    # Glúteos
    _ex("ponte_gluteo", "Ponte de glúteo", "forca", "gluteos", "iniciante", "nenhum", True,
        "Deitado de costas com os joelhos dobrados. Eleve o quadril contraindo o glúteo até alinhar tronco e coxas."),
    _ex("cadeira_abdutora", "Cadeira abdutora", "forca", "gluteos", "iniciante", "maquina", False,
        "Costas apoiadas. Abra as pernas contra a resistência e feche devagar."),
    _ex("caminhada_lateral_elastico", "Caminhada lateral com elástico", "forca", "gluteos", "iniciante", "elastico", True,
        "Elástico acima dos joelhos e pernas semiflexionadas. Dê passos para o lado sem deixar os joelhos caírem para dentro."),
    _ex("elevacao_pelvica", "Elevação pélvica com barra", "forca", "gluteos", "intermediario", "barra", False,
        "Costas apoiadas no banco e barra sobre o quadril, com proteção. Eleve o quadril até alinhar com o tronco e segure um segundo."),
    _ex("gluteo_polia", "Glúteo na polia (coice)", "forca", "gluteos", "intermediario", "polia", False,
        "Tornozeleira presa à polia baixa. Leve a perna para trás e um pouco para cima sem arquear a lombar."),
    _ex("ponte_unilateral", "Ponte de glúteo unilateral", "forca", "gluteos", "intermediario", "nenhum", True,
        "Igual à ponte de glúteo, mas com uma perna estendida no ar. Mantenha o quadril nivelado."),

    # Panturrilha
    _ex("panturrilha_em_pe", "Elevação de panturrilha em pé", "forca", "panturrilha", "iniciante", "nenhum", True,
        "Ponta dos pés na beirada de um degrau. Suba o máximo que conseguir e desça até alongar."),
    _ex("panturrilha_sentado", "Panturrilha sentado na máquina", "forca", "panturrilha", "iniciante", "maquina", False,
        "Joelhos sob o apoio. Suba os calcanhares o máximo possível e desça devagar."),

    # Core
    _ex("prancha", "Prancha", "core", "core", "iniciante", "nenhum", True,
        "Antebraços no chão e corpo reto da cabeça aos pés. Contraia abdômen e glúteos sem deixar o quadril cair.",
        medida="segundos"),
    _ex("inseto_morto", "Inseto morto (dead bug)", "core", "core", "iniciante", "nenhum", True,
        "Deitado de costas, braços para cima e joelhos a 90 graus. Estenda braço e perna opostos sem tirar a lombar do chão."),
    _ex("abdominal_supra", "Abdominal supra", "core", "core", "iniciante", "nenhum", True,
        "Joelhos dobrados. Suba só até tirar as escápulas do chão soltando o ar e desça devagar."),
    _ex("prancha_lateral", "Prancha lateral", "core", "core", "intermediario", "nenhum", True,
        "Apoiado no antebraço e na lateral do pé. Mantenha o corpo reto e o quadril alto.",
        ("ombro",), medida="segundos"),
    _ex("abdominal_bicicleta", "Abdominal bicicleta", "core", "core", "intermediario", "nenhum", True,
        "Deitado, leve o cotovelo em direção ao joelho oposto enquanto estende a outra perna, alternando os lados."),
    _ex("elevacao_pernas", "Elevação de pernas", "core", "core", "intermediario", "nenhum", True,
        "Deitado de costas, mãos ao lado do corpo. Eleve as pernas estendidas até 90 graus e desça sem encostar no chão.",
        ("lombar",)),
    _ex("abdominal_roda", "Abdominal com roda", "core", "core", "avancado", "roda", False,
        "Ajoelhado, role a roda para a frente com o abdômen firme e volte sem arquear as costas.",
        ("lombar", "ombro")),

    # Cardio: os primeiros são os de menor impacto
    _ex("bicicleta_ergometrica", "Bicicleta ergométrica", "cardio", "cardio", "iniciante", "bicicleta", False,
        "Ajuste o banco para a perna ficar quase estendida embaixo. Pedale em ritmo constante.",
        medida="minutos"),
    _ex("esteira_caminhada", "Caminhada na esteira", "cardio", "cardio", "iniciante", "esteira", False,
        "Passos naturais, sem se segurar no apoio. Aumente a inclinação para deixar mais intenso.",
        medida="minutos"),
    _ex("eliptico", "Elíptico (transport)", "cardio", "cardio", "iniciante", "eliptico", False,
        "Movimento contínuo de braços e pernas, sem impacto nas articulações.",
        medida="minutos"),
    _ex("marcha_estacionaria", "Marcha estacionária", "cardio", "cardio", "iniciante", "nenhum", True,
        "Marche no lugar elevando bem os joelhos e movimentando os braços.",
        medida="minutos"),
    _ex("caminhada_rapida", "Caminhada rápida", "cardio", "cardio", "iniciante", "nenhum", True,
        "Caminhe em ritmo acelerado, num passo em que ainda dá para falar, mas não para cantar.",
        medida="minutos"),
    _ex("polichinelo", "Polichinelo", "cardio", "cardio", "iniciante", "nenhum", True,
        "Salte abrindo pernas e braços ao mesmo tempo e volte fechando.",
        ("joelho",), medida="minutos"),
    _ex("remo_ergometro", "Remo ergômetro", "cardio", "cardio", "intermediario", "remo", False,
        "Empurre primeiro com as pernas, depois incline o tronco um pouco para trás e puxe com os braços.",
        ("lombar",), medida="minutos"),
    _ex("corrida_esteira", "Corrida na esteira", "cardio", "cardio", "intermediario", "esteira", False,
        "Passadas curtas e leves, tronco ereto. Comece devagar e aumente a velocidade aos poucos.",
        ("joelho",), medida="minutos"),
    _ex("pular_corda", "Pular corda", "cardio", "cardio", "intermediario", "corda", True,
        "Saltos baixos na ponta dos pés, girando a corda com os punhos e não com os braços inteiros.",
        ("joelho",), medida="minutos"),
    _ex("escalador", "Escalador (mountain climber)", "cardio", "cardio", "intermediario", "nenhum", True,
        "Na posição de prancha alta, traga os joelhos em direção ao peito alternando rápido.",
        ("punho",), medida="minutos"),
    _ex("burpee", "Burpee", "cardio", "cardio", "avancado", "nenhum", True,
        "Agache, apoie as mãos no chão, jogue as pernas para trás, volte e salte. Mantenha um ritmo que dê para sustentar.",
        ("joelho", "punho", "lombar"), medida="minutos"),

    # Mobilidade (usada no aquecimento). O grupo aqui é a região do corpo.
    _ex("rotacao_ombros", "Rotação de ombros", "mobilidade", "ombros", "iniciante", "nenhum", True,
        "Braços abertos para os lados. Faça círculos que começam pequenos e vão aumentando, para a frente e para trás."),
    _ex("abraco_abertura", "Abraço e abertura de braços", "mobilidade", "ombros", "iniciante", "nenhum", True,
        "Abra os braços para trás estufando o peito e depois cruze à frente como num abraço, em ritmo contínuo."),
    _ex("gato_camelo", "Gato e camelo", "mobilidade", "coluna", "iniciante", "nenhum", True,
        "Em quatro apoios, arredonde as costas olhando para o umbigo e depois afunde a coluna olhando para a frente, devagar."),
    _ex("rotacao_tronco", "Rotação de tronco", "mobilidade", "coluna", "iniciante", "nenhum", True,
        "Em pé, braços cruzados no peito. Gire o tronco para um lado e para o outro sem mexer o quadril."),
    _ex("rotacao_quadril", "Rotação de quadril", "mobilidade", "quadril", "iniciante", "nenhum", True,
        "Mãos na cintura. Faça círculos amplos com o quadril para os dois lados."),
    _ex("balanco_pernas", "Balanço de pernas", "mobilidade", "quadril", "iniciante", "nenhum", True,
        "Apoiado na parede, balance uma perna para a frente e para trás de forma controlada e depois troque."),
    _ex("mobilidade_tornozelo", "Mobilidade de tornozelo", "mobilidade", "tornozelo", "iniciante", "nenhum", True,
        "Pé perto de uma parede. Leve o joelho em direção à parede sem tirar o calcanhar do chão."),

    # Alongamento
    _ex("alongamento_geral", "Alongamento geral", "alongamento", "corpo_inteiro", "iniciante", "nenhum", True,
        "Alongue os músculos trabalhados no treino, segurando cada posição de 20 a 30 segundos, sem sentir dor.",
        medida="minutos"),
]

_POR_CODIGO = {e["codigo"]: e for e in EXERCICIOS}

MODALIDADES_AQUECIMENTO = [
    {
        "codigo": "geral",
        "nome": "Aquecimento geral",
        "duracao": "5 a 10 minutos",
        "descricao": "Atividade aeróbica leve para subir os batimentos e a temperatura do corpo antes do treino.",
        "exemplos": ["bicicleta_ergometrica", "esteira_caminhada", "eliptico", "marcha_estacionaria"],
    },
    {
        "codigo": "mobilidade",
        "nome": "Mobilidade articular",
        "duracao": "2 a 5 minutos",
        "descricao": "Movimentos controlados das articulações que vão trabalhar no dia, como ombros, quadril e tornozelos.",
        "exemplos": ["rotacao_ombros", "gato_camelo", "rotacao_quadril", "mobilidade_tornozelo"],
    },
    {
        "codigo": "especifico",
        "nome": "Aquecimento específico",
        "duracao": "1 ou 2 séries",
        "descricao": "Séries leves do primeiro exercício do treino, com cerca de metade da carga, para ensaiar o movimento.",
        "exemplos": [],
    },
]


def sem_acento(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c)).strip().lower()


def buscar_exercicio(codigo):
    return _POR_CODIGO.get(codigo)


def filtrar_exercicios(tipo=None, grupo=None, nivel=None, local=None, busca=None):
    resultado = EXERCICIOS
    if tipo:
        resultado = [e for e in resultado if e["tipo"] == tipo]
    if grupo:
        resultado = [e for e in resultado if e["grupo"] == grupo]
    if nivel:
        nivel = sem_acento(nivel)
        resultado = [e for e in resultado if e["nivel"] == nivel]
    if local and sem_acento(local) == "casa":
        resultado = [e for e in resultado if e["casa"]]
    if busca:
        termo = sem_acento(busca)
        resultado = [e for e in resultado if termo in sem_acento(e["nome"])]
    return list(resultado)


def modalidades_aquecimento():
    modalidades = []
    for m in MODALIDADES_AQUECIMENTO:
        exemplos = [{"codigo": c, "nome": _POR_CODIGO[c]["nome"]} for c in m["exemplos"]]
        modalidades.append({**m, "exemplos": exemplos})
    return modalidades
