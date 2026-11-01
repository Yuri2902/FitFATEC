drop database fitfatec;
CREATE DATABASE IF NOT EXISTS fitfatec CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE fitfatec;

CREATE TABLE aluno (
    id_aluno  INT  PRIMARY KEY AUTO_INCREMENT,
    nome   VARCHAR(100) NOT NULL,
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
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE frequencia (
    id_frequencia  INT PRIMARY KEY  AUTO_INCREMENT,
    id_aluno  INT NOT NULL,
    data_registro  DATE NOT NULL,
    status  CHAR(5) NOT NULL,-- BOA, RUIM, MÉDIA
    FOREIGN KEY (id_aluno) REFERENCES aluno (id_aluno),
    UNIQUE (id_aluno, data_registro)
);

CREATE TABLE exercicio (
    id_exercicio   INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL UNIQUE,
    grupo_muscular  VARCHAR(40)  NOT NULL,
    nivel VARCHAR(15)  NOT NULL
);

CREATE TABLE treino (
    id_treino INT PRIMARY KEY AUTO_INCREMENT,
    id_aluno INT NOT NULL,
    id_exercicio INT NOT NULL,
    id_frequencia  INT,
    carga_kg   DECIMAL(5,1),
    nome VARCHAR(80)  NOT NULL,
    origem  VARCHAR(10)  NOT NULL,
    series  INT NOT NULL,
    repeticoes VARCHAR(15) NOT NULL,
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,-- CURRENT_TIMESTAMP É PRA REGISTRAR HR E MOMENTO ATUAL
    FOREIGN KEY (id_aluno) REFERENCES aluno (id_aluno),
    FOREIGN KEY (id_exercicio) REFERENCES exercicio (id_exercicio),
    FOREIGN KEY (id_frequencia) REFERENCES frequencia (id_frequencia)
);