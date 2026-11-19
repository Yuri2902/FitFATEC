

CREATE DATABASE IF NOT EXISTS fitfatec
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE fitfatec;

CREATE TABLE IF NOT EXISTS aluno (
    id_aluno INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    matricula VARCHAR(12) NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    data_nascimento DATE NULL,
    objetivo VARCHAR(30) NULL,
    nivel VARCHAR(15) NULL,
    data_matricula DATE NULL,
    desistiu BOOLEAN NOT NULL DEFAULT FALSE,
    data_desistencia DATE NULL,
    senha_hash VARCHAR(255) NULL,
    papel ENUM('aluno', 'instrutor', 'admin')
        NOT NULL DEFAULT 'aluno',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL
        ON UPDATE CURRENT_TIMESTAMP,
    telefone VARCHAR(20) NULL,
    avatar_url VARCHAR(255) NULL,
    treinos_semana INT DEFAULT 3,
    modalidade_principal VARCHAR(80) DEFAULT 'Musculação',
    notificacoes TINYINT(1) DEFAULT 1,
    acessibilidade VARCHAR(50) DEFAULT 'padrao',

    -- Recuperação de senha
    token_recuperacao VARCHAR(255) NULL,
    token_expiracao DATETIME NULL,

    personalidade VARCHAR(20) NOT NULL DEFAULT 'padrao'
);



CREATE TABLE IF NOT EXISTS frequencia (
    id_frequencia INT PRIMARY KEY AUTO_INCREMENT,
    id_aluno INT NOT NULL,
    data_registro DATE NOT NULL,
    status ENUM('presente', 'ausente', 'justificado')
        NOT NULL DEFAULT 'presente',

    FOREIGN KEY (id_aluno)
        REFERENCES aluno(id_aluno)
        ON DELETE CASCADE,

    UNIQUE KEY uq_frequencia_aluno_data
        (id_aluno, data_registro)
);

CREATE TABLE IF NOT EXISTS exercicio (
    id_exercicio INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL UNIQUE,
    grupo_muscular VARCHAR(40) NOT NULL,
    nivel VARCHAR(15) NOT NULL
);



CREATE TABLE IF NOT EXISTS treino (
    id_treino INT PRIMARY KEY AUTO_INCREMENT,
    id_aluno INT NOT NULL,
    nome VARCHAR(80) NOT NULL,
    origem VARCHAR(10) NOT NULL,
    series INT NOT NULL,
    repeticoes VARCHAR(15) NOT NULL,
    dia_semana VARCHAR(30) NOT NULL,
    semana_inicio DATE NULL,
    observacoes TEXT NULL,
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (id_aluno)
        REFERENCES aluno(id_aluno)
        ON DELETE CASCADE,

    INDEX idx_treinos_aluno_ativo (id_aluno, ativo)
);


CREATE TABLE IF NOT EXISTS treino_exercicios (
    treino_exercicios_id INT PRIMARY KEY AUTO_INCREMENT,
    id_treino INT NOT NULL,
  -- Identificador externo do catálogo MIT
    exercicio_id VARCHAR(100) NULL,
    id_exercicio INT NULL,
    nome_exercicio VARCHAR(150) NOT NULL,
    grupo_muscular VARCHAR(80) NULL,
    series INT NOT NULL DEFAULT 3,
    repeticoes VARCHAR(30) NOT NULL DEFAULT '8 - 12',
    descanso_segundos INT NOT NULL DEFAULT 60,
    ordem INT NOT NULL DEFAULT 1,
    etapa VARCHAR(20) NULL,

    FOREIGN KEY (id_treino)
        REFERENCES treino(id_treino)
        ON DELETE CASCADE,

    FOREIGN KEY (id_exercicio)
        REFERENCES exercicio(id_exercicio)
        ON DELETE SET NULL,

    INDEX idx_te_treino_ordem (id_treino, ordem),
    INDEX idx_te_exercicio (id_exercicio)
);



CREATE TABLE IF NOT EXISTS grade_hrarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    modalidade VARCHAR(80) NOT NULL,
    dia_semana TINYINT NOT NULL DEFAULT 0,
    horario VARCHAR(30) NOT NULL,
    vagas_totais INT NOT NULL DEFAULT 20,
    ativo TINYINT(1) NOT NULL DEFAULT 1,

    UNIQUE KEY uq_grade
        (modalidade, dia_semana, horario)
);



CREATE TABLE IF NOT EXISTS agendamento (
    id_agendamento INT PRIMARY KEY AUTO_INCREMENT,
    id_aluno INT NOT NULL,
    id_grade_horario INT NULL,
    data_aula DATE NOT NULL,
    horario VARCHAR(30) NOT NULL,
    modalidade VARCHAR(80) NOT NULL DEFAULT 'Musculação',
    observacoes VARCHAR(200) NULL,

    status ENUM('agendada', 'cancelada', 'concluida')
        NOT NULL DEFAULT 'agendada',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_aluno)
        REFERENCES aluno(id_aluno)
        ON DELETE CASCADE,

    FOREIGN KEY (id_grade_horario)
        REFERENCES grade_hrarios(id)
        ON DELETE SET NULL,

    UNIQUE KEY uq_agendamento_aluno
        (id_aluno, data_aula, horario),

    INDEX idx_agend_data_modalidade
        (data_aula, modalidade, status),
    INDEX idx_agend_grade
        (id_grade_horario)
);



CREATE TABLE IF NOT EXISTS chat_mensagens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_aluno INT NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    eh_treino TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_aluno)
        REFERENCES aluno(id_aluno)
        ON DELETE CASCADE,

    INDEX idx_chat_aluno (id_aluno)
);

/*
-- insets
USE fitfatec;

INSERT INTO aluno
(nome, matricula, email, data_nascimento, objetivo, nivel,
 data_matricula, telefone, treinos_semana,
 modalidade_principal, papel)
VALUES
('Lucas Almeida', '20260001', 'lucas@email.com', '2004-05-12',
 'Hipertrofia', 'intermediario', '2026-08-01',
 '11988881111', 5, 'Musculação', 'aluno'),

('Mariana Santos', '20260002', 'mariana@email.com', '2003-09-20',
 'Condicionamento', 'iniciante', '2026-08-05',
 '11988882222', 3, 'Funcional', 'aluno'),

('Pedro Oliveira', '20260003', 'pedro@email.com', '2002-03-15',
 'Resistencia', 'avancado', '2026-08-10',
 '11988883333', 4, 'Musculação', 'aluno'),

('Ana Costa', '20260004', 'ana@email.com', '2005-11-08',
 'Condicionamento', 'iniciante', '2026-09-01',
 '11988884444', 3, 'Pilates', 'aluno'),

('Rafael Souza', '20260005', 'rafael@email.com', '2001-07-22',
 'Hipertrofia', 'intermediario', '2026-09-05',
 '11988885555', 5, 'Musculação', 'aluno');




INSERT INTO frequencia
(id_aluno, data_registro, status)
SELECT id_aluno, '2026-11-16', 'presente'
FROM aluno WHERE email = 'lucas@email.com';

INSERT INTO frequencia
(id_aluno, data_registro, status)
SELECT id_aluno, '2026-11-17', 'presente'
FROM aluno WHERE email = 'lucas@email.com';

INSERT INTO frequencia
(id_aluno, data_registro, status)
SELECT id_aluno, '2026-11-16', 'ausente'
FROM aluno WHERE email = 'mariana@email.com';

INSERT INTO frequencia
(id_aluno, data_registro, status)
SELECT id_aluno, '2026-11-16', 'presente'
FROM aluno WHERE email = 'pedro@email.com';

INSERT INTO frequencia
(id_aluno, data_registro, status)
SELECT id_aluno, '2026-11-17', 'justificado'
FROM aluno WHERE email = 'ana@email.com';




INSERT INTO exercicio
(nome, grupo_muscular, nivel)
VALUES
('Supino reto', 'Peito', 'intermediario'),
('Agachamento livre', 'Pernas', 'avancado'),
('Rosca direta', 'Biceps', 'iniciante'),
('Puxada frontal', 'Costas', 'intermediario'),
('Desenvolvimento', 'Ombros', 'intermediario'),
('Leg press', 'Pernas', 'iniciante'),
('Prancha abdominal', 'Abdomen', 'iniciante');




INSERT INTO treino
(id_aluno, nome, origem, series, repeticoes,
 dia_semana, semana_inicio, observacoes)
SELECT id_aluno, 'Treino A - Superior', 'manual', 3, '10 - 12',
'Segunda-feira', '2026-11-16', 'Foco em membros superiores'
FROM aluno WHERE email = 'lucas@email.com';

INSERT INTO treino
(id_aluno, nome, origem, series, repeticoes,
 dia_semana, semana_inicio, observacoes)
SELECT id_aluno, 'Treino B - Inferior', 'manual', 4, '8 - 12',
'Quarta-feira', '2026-11-16', 'Foco em pernas'
FROM aluno WHERE email = 'lucas@email.com';

INSERT INTO treino
(id_aluno, nome, origem, series, repeticoes,
 dia_semana, semana_inicio, observacoes)
SELECT id_aluno, 'Treino Inicial', 'ia', 3, '12 - 15',
'Terça-feira', '2026-11-16', 'Treino para iniciantes'
FROM aluno WHERE email = 'mariana@email.com';


INSERT INTO treino_exercicios
(id_treino, id_exercicio, nome_exercicio,
 grupo_muscular, series, repeticoes, descanso_segundos,
 ordem, etapa)

SELECT t.id_treino, e.id_exercicio, e.nome,
e.grupo_muscular, 3, '10 - 12', 60, 1, 'principal'
FROM treino t
INNER JOIN aluno a ON a.id_aluno = t.id_aluno
CROSS JOIN exercicio e
WHERE a.email = 'lucas@email.com'
AND t.nome = 'Treino A - Superior'
AND e.nome = 'Supino reto';

INSERT INTO treino_exercicios
(id_treino, id_exercicio, nome_exercicio,
 grupo_muscular, series, repeticoes, descanso_segundos,
 ordem, etapa)

SELECT t.id_treino, e.id_exercicio, e.nome,
e.grupo_muscular, 3, '10 - 12', 60, 2, 'principal'
FROM treino t
INNER JOIN aluno a ON a.id_aluno = t.id_aluno
CROSS JOIN exercicio e
WHERE a.email = 'lucas@email.com'
AND t.nome = 'Treino A - Superior'
AND e.nome = 'Rosca direta';


INSERT INTO grade_horarios
(modalidade, dia_semana, horario, vagas_totais)
VALUES
('Musculação', 1, '07:00 - 08:00', 20),
('Musculação', 2, '08:00 - 09:00', 20),
('Funcional', 3, '18:00 - 19:00', 15),
('Pilates', 4, '09:00 - 10:00', 12),
('Musculação', 5, '19:00 - 20:00', 20);



INSERT INTO agendamento
(id_aluno, id_grade_horario, data_aula,
 horario, modalidade, observacoes, status)

SELECT a.id_aluno, g.id, '2026-11-23',
g.horario, g.modalidade, 'Treino de superior', 'agendada'
FROM aluno a
CROSS JOIN grade_horarios g
WHERE a.email = 'lucas@email.com'
AND g.modalidade = 'Musculação'
AND g.dia_semana = 1;

INSERT INTO agendamento
(id_aluno, id_grade_horario, data_aula,
 horario, modalidade, observacoes, status)

SELECT a.id_aluno, g.id, '2026-11-25',
g.horario, g.modalidade, 'Primeira aula', 'agendada'
FROM aluno a
CROSS JOIN grade_horarios g
WHERE a.email = 'mariana@email.com'
AND g.modalidade = 'Funcional'
AND g.dia_semana = 3;


INSERT INTO chat_mensagens
(id_aluno, role, content, eh_treino)

SELECT id_aluno, 'user',
'Quero um treino para hipertrofia.', 0
FROM aluno WHERE email = 'lucas@email.com';

INSERT INTO chat_mensagens
(id_aluno, role, content, eh_treino)

SELECT id_aluno, 'assistant',
'Vamos organizar seu treino de hipertrofia.', 1
FROM aluno WHERE email = 'lucas@email.com';

INSERT INTO chat_mensagens
(id_aluno, role, content, eh_treino)

SELECT id_aluno, 'user',
'Sou iniciante. Como posso começar?', 0
FROM aluno WHERE email = 'mariana@email.com';

*/
