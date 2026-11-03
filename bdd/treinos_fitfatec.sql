-- Tabelas do módulo de treinos e agenda (Dev 3), como proposta para o Dev 5 revisar e juntar ao bd_fitfatec.sql.
-- Não altera nenhuma tabela existente. Ordem: bd_fitfatec.sql, este arquivo e depois catalogo_exercicios.sql.
USE fitfatec;

CREATE TABLE plano_treino (
    id_plano  INT PRIMARY KEY AUTO_INCREMENT,
    id_aluno  INT NOT NULL,
    objetivo  ENUM('hipertrofia','emagrecimento','condicionamento','saude') NOT NULL,
    nivel  ENUM('iniciante','intermediario','avancado') NOT NULL,
    minutos_por_sessao  SMALLINT NOT NULL,
    local_treino  ENUM('academia','casa') NOT NULL DEFAULT 'academia',
    divisao  VARCHAR(60) NOT NULL,
    observacoes  TEXT NULL,
    ativo  BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_aluno) REFERENCES aluno (id_aluno),
    INDEX idx_plano_aluno_ativo (id_aluno, ativo),
    CHECK (minutos_por_sessao BETWEEN 20 AND 120)
);

CREATE TABLE plano_restricao (
    id_plano  INT NOT NULL,
    restricao  ENUM('joelho','lombar','ombro','punho') NOT NULL,
    PRIMARY KEY (id_plano, restricao),
    FOREIGN KEY (id_plano) REFERENCES plano_treino (id_plano) ON DELETE CASCADE
);

CREATE TABLE plano_sessao (
    id_sessao  INT PRIMARY KEY AUTO_INCREMENT,
    id_plano  INT NOT NULL,
    letra  CHAR(1) NOT NULL,
    nome  VARCHAR(60) NOT NULL,
    duracao_estimada_min  SMALLINT NOT NULL,
    UNIQUE (id_plano, letra),
    FOREIGN KEY (id_plano) REFERENCES plano_treino (id_plano) ON DELETE CASCADE
);

CREATE TABLE plano_dia (
    id_plano  INT NOT NULL,
    dia_semana  TINYINT NOT NULL, -- 1 = segunda, 7 = domingo
    letra  CHAR(1) NOT NULL,
    PRIMARY KEY (id_plano, dia_semana),
    FOREIGN KEY (id_plano, letra) REFERENCES plano_sessao (id_plano, letra) ON DELETE CASCADE,
    CHECK (dia_semana BETWEEN 1 AND 7)
);

CREATE TABLE plano_item (
    id_item  INT PRIMARY KEY AUTO_INCREMENT,
    id_sessao  INT NOT NULL,
    id_exercicio  INT NOT NULL,
    etapa  ENUM('aquecimento','principal','complementar') NOT NULL,
    ordem  TINYINT NOT NULL,
    series  TINYINT NOT NULL,
    repeticoes  VARCHAR(15) NOT NULL, -- 10-12, 30 s ou 5 min
    intervalo_seg  SMALLINT NOT NULL DEFAULT 0,
    observacao  VARCHAR(200) NULL,
    UNIQUE (id_sessao, etapa, ordem),
    FOREIGN KEY (id_sessao) REFERENCES plano_sessao (id_sessao) ON DELETE CASCADE,
    FOREIGN KEY (id_exercicio) REFERENCES exercicio (id_exercicio),
    CHECK (series > 0)
);

CREATE TABLE agendamento (
    id_agendamento  INT PRIMARY KEY AUTO_INCREMENT,
    id_aluno  INT NOT NULL,
    atividade  ENUM('musculacao','funcional','spinning','alongamento') NOT NULL,
    inicio  DATETIME NOT NULL,
    status  ENUM('agendado','cancelado','concluido','faltou') NOT NULL DEFAULT 'agendado',
    criado_em  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_aluno) REFERENCES aluno (id_aluno),
    INDEX idx_agendamento_horario (atividade, inicio),
    INDEX idx_agendamento_aluno (id_aluno, inicio)
);
