"""Conexão e estrutura inicial de persistência em SQLite."""

import sqlite3

from flask import current_app, g

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    papel TEXT NOT NULL CHECK (papel IN ('administrador', 'barbeiro'))
);

CREATE TABLE IF NOT EXISTS profissionais (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    telefone TEXT
);

CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    duracao_minutos INTEGER NOT NULL CHECK (duracao_minutos > 0)
);

CREATE TABLE IF NOT EXISTS agendamentos (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    servico_id INTEGER NOT NULL REFERENCES servicos(id),
    inicio TEXT NOT NULL,
    fim TEXT NOT NULL,
    origem TEXT NOT NULL CHECK (origem IN ('agendado', 'encaixe')),
    status TEXT NOT NULL DEFAULT 'confirmado'
        CHECK (status IN ('confirmado', 'cancelado')),
    CHECK (fim > inicio)
);

CREATE INDEX IF NOT EXISTS idx_agendamentos_profissional_inicio
    ON agendamentos (profissional_id, inicio);
"""


def get_db():
    if "db" not in g:
        db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        g.db = db
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()
