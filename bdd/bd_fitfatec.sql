-- DROP DATABASE IF EXISTS fitfatec;
CREATE DATABASE IF NOT EXISTS fitfatec CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE fitfatec;

-- --------------------------------------------------------
-- Tabela de Alunos (Estrutura original mantida + novos campos)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS aluno (
    id_aluno  INT  PRIMARY KEY AUTO_INCREMENT,
    nome   VARCHAR(100) NOT NULL,
    matricula VARCHAR(12) NULL UNIQUE,
    email  VARCHAR(120) NOT NULL UNIQUE,
    data_nascimento DATE NULL,
    objetivo VARCHAR(30) NULL,
    nivel VARCHAR(15) NULL,
    data_matricula DATE NULL,
    desistiu  BOOLEAN NOT NULL DEFAULT FALSE,
    data_desistencia  DATE,
    senha_hash VARCHAR(255) NULL,
    papel ENUM('aluno','instrutor','admin') NOT NULL DEFAULT 'aluno',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    -- Novos campos (UX/UI Evolution)
    telefone VARCHAR(20) NULL,
    avatar_url VARCHAR(255) NULL,
    treinos_semana INT DEFAULT 3,
    modalidade_principal VARCHAR(80) DEFAULT 'Musculação',
    notificacoes TINYINT(1) DEFAULT 1,
    acessibilidade VARCHAR(50) DEFAULT 'padrao',
    tema VARCHAR(30) DEFAULT 'escuro',
    token_recuperacao VARCHAR(255) NULL,
    token_expiracao DATETIME NULL
);

-- --------------------------------------------------------
-- Tabela de Frequência (Mantida)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS frequencia (
    id_frequencia  INT PRIMARY KEY  AUTO_INCREMENT,
    id_aluno  INT NOT NULL,
    data_registro  DATE NOT NULL,
    status  CHAR(5) NOT NULL,
    FOREIGN KEY (id_aluno) REFERENCES aluno (id_aluno),
    UNIQUE (id_aluno, data_registro)
);

-- --------------------------------------------------------
-- Tabela de Exercícios (Catálogo base - Mantida)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS exercicio (
    id_exercicio   INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL UNIQUE,
    grupo_muscular  VARCHAR(40)  NOT NULL,
    nivel VARCHAR(15)  NOT NULL
);

-- --------------------------------------------------------
-- Tabela de Treinos (Legado - Mantida para compatibilidade)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS treino (
    id_treino INT PRIMARY KEY AUTO_INCREMENT,
    id_aluno INT NOT NULL,
    id_exercicio INT NOT NULL,
    id_frequencia  INT,
    carga_kg   DECIMAL(5,1),
    nome VARCHAR(80)  NOT NULL,
    origem  VARCHAR(10)  NOT NULL,
    series  INT NOT NULL,
    repeticoes VARCHAR(15) NOT NULL,
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_aluno) REFERENCES aluno (id_aluno),
    FOREIGN KEY (id_exercicio) REFERENCES exercicio (id_exercicio),
    FOREIGN KEY (id_frequencia) REFERENCES frequencia (id_frequencia)
);

-- --------------------------------------------------------
-- NOVAS TABELAS (UX/UI Evolution)
-- --------------------------------------------------------

-- Tabela Treinos (Header)
CREATE TABLE IF NOT EXISTS treinos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    subtitulo VARCHAR(150) NULL,
    dia_semana VARCHAR(30) NOT NULL,
    origem ENUM('kiara', 'manual') NOT NULL DEFAULT 'kiara',
    semana_inicio DATE NULL,
    observacoes TEXT NULL,
    ativo TINYINT(1) DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (aluno_id) REFERENCES aluno (id_aluno)
);

-- Tabela Treino Exercícios (Items)
CREATE TABLE IF NOT EXISTS treino_exercicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    treino_id INT NOT NULL,
    exercicio_id VARCHAR(100) NULL,
    nome_exercicio VARCHAR(150) NOT NULL,
    grupo_muscular VARCHAR(80) NULL,
    series INT NOT NULL DEFAULT 3,
    repeticoes VARCHAR(30) NOT NULL DEFAULT '8 - 12',
    descanso_segundos INT NOT NULL DEFAULT 60,
    ordem INT NOT NULL DEFAULT 1,
    FOREIGN KEY (treino_id) REFERENCES treinos (id) ON DELETE CASCADE
);

-- Tabela Grade de Horários
CREATE TABLE IF NOT EXISTS grade_horarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    modalidade VARCHAR(80) NOT NULL,
    dia_semana TINYINT NOT NULL,
    horario VARCHAR(30) NOT NULL,
    vagas_totais INT NOT NULL DEFAULT 20,
    ativo TINYINT(1) DEFAULT 1
);

-- Tabela Agendamento (Mantida com ajustes)
CREATE TABLE IF NOT EXISTS agendamento (
    id_agendamento INT PRIMARY KEY AUTO_INCREMENT,
    id_aluno INT NOT NULL,
    data_aula DATE NOT NULL,
    horario VARCHAR(30) NOT NULL, -- Alterado para VARCHAR p/ compatibilidade
    modalidade VARCHAR(80) NOT NULL DEFAULT 'musculação',
    observacoes VARCHAR(200) NULL,
    -- Mantendo enum legado + novos valores
    status ENUM('agendada','cancelada','concluida','agendado','concluido','cancelado') NOT NULL DEFAULT 'agendada',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_aluno) REFERENCES aluno (id_aluno),
    UNIQUE (id_aluno, data_aula, horario)
);

-- --------------------------------------------------------
-- SEED DE DEMONSTRAÇÃO (Idempotente)
-- --------------------------------------------------------

-- Inserir aluno de teste
INSERT IGNORE INTO aluno (id_aluno, nome, matricula, email, objetivo, nivel, telefone, modalidade_principal)
VALUES (1, 'João Silva', '20260001', 'joao.silva@fatec.sp.gov.br', 'Ganhar massa muscular', 'Intermediário', '(11) 99999-0000', 'Musculação');

-- Inserir treinos
INSERT IGNORE INTO treinos (id, aluno_id, titulo, subtitulo, dia_semana, origem) VALUES
(1, 1, 'Treino A', 'Peito • Ombro • Tríceps', 'Segunda-feira', 'kiara'),
(2, 1, 'Treino B', 'Costas • Bíceps', 'Quarta-feira', 'manual'),
(3, 1, 'Treino C', 'Pernas • Glúteos', 'Sexta-feira', 'kiara');

-- Inserir exercícios do Treino A
INSERT IGNORE INTO treino_exercicios (treino_id, nome_exercicio, grupo_muscular, ordem) VALUES
(1, 'Supino reto (barra)', 'peito', 1),
(1, 'Supino inclinado (halteres)', 'peito', 2),
(1, 'Crucifixo no cabo', 'peito', 3),
(1, 'Desenvolvimento (halteres)', 'ombros', 4),
(1, 'Elevação lateral', 'ombros', 5),
(1, 'Tríceps na polia', 'tríceps', 6);

-- Inserir grade
INSERT IGNORE INTO grade_horarios (modalidade, dia_semana, horario, vagas_totais) VALUES
('Musculação', 1, '08:00 - 09:00', 20),
('Funcional', 2, '18:00 - 19:00', 15);

-- Inserir agendamento exemplo
INSERT IGNORE INTO agendamento (id_aluno, data_aula, horario, modalidade, status) VALUES
(1, '2026-11-16', '08:00 - 09:00', 'Musculação', 'concluido');
