-- FitFATEC: esquema CANÔNICO para instalação nova (MySQL 8+).
-- Instalação limpa: recrie apenas bancos de teste descartáveis, com backup antes.
-- Dados fictícios não são inseridos automaticamente.

CREATE DATABASE IF NOT EXISTS fitfatec
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE fitfatec;

CREATE TABLE IF NOT EXISTS aluno (
    id_aluno INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    matricula VARCHAR(12) UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    data_nascimento DATE,
    objetivo VARCHAR(30),
    nivel VARCHAR(15),
    data_matricula DATE,
    desistiu BOOLEAN NOT NULL DEFAULT FALSE,
    data_desistencia DATE,
    senha_hash VARCHAR(255),
    papel ENUM('aluno','instrutor','admin') NOT NULL DEFAULT 'aluno',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    telefone VARCHAR(20),
    avatar_url VARCHAR(255),
    treinos_semana INT NULL DEFAULT NULL,
    minutos_por_sessao INT NULL DEFAULT NULL,
    modalidade_principal VARCHAR(80) NOT NULL DEFAULT 'Musculação',
    notificacoes TINYINT(1) NOT NULL DEFAULT 1,
    acessibilidade VARCHAR(50) NOT NULL DEFAULT 'padrao',
    tema VARCHAR(30) NOT NULL DEFAULT 'escuro',
    personalidade VARCHAR(20) NOT NULL DEFAULT 'padrao',
    token_recuperacao VARCHAR(255),
    token_expiracao DATETIME
);

CREATE TABLE IF NOT EXISTS exercicio (
    id_exercicio INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    grupo_muscular VARCHAR(40) NOT NULL,
    nivel VARCHAR(15) NOT NULL
);


-- Um plano é um agrupador de fichas. Treinos individuais não têm plano_id.
CREATE TABLE IF NOT EXISTS plano_treino (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    cor_hex CHAR(7) NOT NULL DEFAULT '#F97316',
    objetivo VARCHAR(30),
    dias_semana TINYINT NOT NULL,
    minutos_sessao SMALLINT NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_plano_aluno FOREIGN KEY (aluno_id) REFERENCES aluno(id_aluno) ON DELETE CASCADE
);

-- Cabeçalho da ficha. Séries/repetições pertencem a cada exercício,
-- não ao cabeçalho: um treino pode ter exercícios com prescrições distintas.
CREATE TABLE IF NOT EXISTS treinos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    plano_id INT NULL,
    cor_hex CHAR(7) NOT NULL DEFAULT '#06B6D4',
    titulo VARCHAR(100) NOT NULL,
    subtitulo VARCHAR(150),
    dia_semana VARCHAR(30) NULL,
    origem VARCHAR(20) NOT NULL DEFAULT 'manual',
    semana_inicio DATE,
    observacoes TEXT,
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_treino_plano FOREIGN KEY (plano_id) REFERENCES plano_treino(id) ON DELETE RESTRICT,
    CONSTRAINT fk_treinos_aluno FOREIGN KEY (aluno_id)
        REFERENCES aluno(id_aluno) ON DELETE CASCADE,
    INDEX idx_treinos_aluno_ativo (aluno_id, ativo),
    INDEX idx_treinos_semana (aluno_id, dia_semana, ativo)
);

-- exercicio_id = código TEXTO do catálogo externo MIT; id_exercicio =
-- id NUMÉRICO do catálogo local, opcional. São identificadores distintos.
CREATE TABLE IF NOT EXISTS treino_exercicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    treino_id INT NOT NULL,
    exercicio_id VARCHAR(100),
    id_exercicio INT,
    nome_exercicio VARCHAR(150) NOT NULL,
    grupo_muscular VARCHAR(80),
    series INT NOT NULL DEFAULT 3,
    repeticoes VARCHAR(30) NOT NULL DEFAULT '8 - 12',
    descanso_segundos INT NOT NULL DEFAULT 60,
    ordem INT NOT NULL DEFAULT 1,
    etapa VARCHAR(20),
    CONSTRAINT fk_itens_treino FOREIGN KEY (treino_id)
        REFERENCES treinos(id) ON DELETE CASCADE,
    CONSTRAINT fk_itens_exercicio_local FOREIGN KEY (id_exercicio)
        REFERENCES exercicio(id_exercicio) ON DELETE SET NULL,
    INDEX idx_itens_ordem (treino_id, ordem)
);

-- Execução é diferente da definição da ficha. Concluir não apaga o treino.
CREATE TABLE IF NOT EXISTS treino_execucoes (
    id_execucao INT AUTO_INCREMENT PRIMARY KEY,
    treino_id INT NOT NULL,
    aluno_id INT NOT NULL,
    concluido_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_execucao_treino FOREIGN KEY (treino_id)
        REFERENCES treinos(id) ON DELETE CASCADE,
    CONSTRAINT fk_execucao_aluno FOREIGN KEY (aluno_id)
        REFERENCES aluno(id_aluno) ON DELETE CASCADE,
    INDEX idx_execucao_aluno_data (aluno_id, concluido_em)
);

-- Calendário pessoal: uma data aponta para uma ficha já salva.
-- Remover um agendamento NUNCA remove o treino. Não há vagas nem aulas físicas.
CREATE TABLE IF NOT EXISTS agendamento (
    id_agendamento INT AUTO_INCREMENT PRIMARY KEY,
    id_aluno INT NOT NULL,
    treino_id INT NOT NULL,
    data_treino DATE NOT NULL,
    horario TIME NULL,
    observacoes VARCHAR(200),
    status ENUM('planejado','concluido') NOT NULL DEFAULT 'planejado',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_agend_aluno FOREIGN KEY (id_aluno)
        REFERENCES aluno(id_aluno) ON DELETE CASCADE,
    CONSTRAINT fk_agend_treino FOREIGN KEY (treino_id)
        REFERENCES treinos(id) ON DELETE RESTRICT,
    UNIQUE KEY uq_agend_aluno_treino_data (id_aluno, treino_id, data_treino),
    INDEX idx_agend_aluno_data (id_aluno, data_treino, status)
);

-- Regra semanal independente da ficha. Sem data final = repetição até cancelamento.
CREATE TABLE IF NOT EXISTS treino_recorrencia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    treino_id INT NOT NULL,
    dia_semana TINYINT NOT NULL, -- 0=segunda ... 6=domingo
    data_inicio DATE NOT NULL,
    horario TIME NULL,
    CONSTRAINT fk_rec_aluno FOREIGN KEY (aluno_id) REFERENCES aluno(id_aluno) ON DELETE CASCADE,
    CONSTRAINT fk_rec_treino FOREIGN KEY (treino_id) REFERENCES treinos(id) ON DELETE RESTRICT,
    CONSTRAINT uq_rec_semana UNIQUE (aluno_id, treino_id, dia_semana, data_inicio)
);

-- Exclui ou conclui uma ocorrência sem apagar a repetição inteira.
CREATE TABLE IF NOT EXISTS treino_recorrencia_excecao (
    recorrencia_id INT NOT NULL,
    data_treino DATE NOT NULL,
    status ENUM('cancelado','concluido') NOT NULL,
    PRIMARY KEY (recorrencia_id, data_treino),
    CONSTRAINT fk_excecao_rec FOREIGN KEY (recorrencia_id) REFERENCES treino_recorrencia(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS frequencia (
    id_frequencia INT AUTO_INCREMENT PRIMARY KEY,
    id_aluno INT NOT NULL,
    data_registro DATE NOT NULL,
    status ENUM('presente','ausente','justificado') NOT NULL DEFAULT 'presente',
    CONSTRAINT fk_frequencia_aluno FOREIGN KEY (id_aluno)
        REFERENCES aluno(id_aluno) ON DELETE CASCADE,
    UNIQUE KEY uq_frequencia_aluno_data (id_aluno, data_registro)
);

CREATE TABLE IF NOT EXISTS chat_mensagens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_aluno INT NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    eh_treino TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chat_aluno FOREIGN KEY (id_aluno)
        REFERENCES aluno(id_aluno) ON DELETE CASCADE,
    INDEX idx_chat_aluno (id_aluno)
);
