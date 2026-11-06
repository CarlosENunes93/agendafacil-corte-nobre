"""Testes da primeira entrega executável, sem depender de banco local do usuário."""

import sqlite3

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "teste.sqlite3"),
        "SECRET_KEY": "segredo-longo-exclusivamente-para-testes",
    })


@pytest.fixture
def client(app):
    return app.test_client()



def test_pagina_inicial_redireciona_para_login(client):
    resposta = client.get("/")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/login")



def test_endpoint_health_retorna_json(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok", "aplicacao": "AgendaFácil"}


def test_banco_cria_as_cinco_entidades(app):
    database = app.config["DATABASE"]
    with sqlite3.connect(database) as conn:
        nomes = {
            linha[0]
            for linha in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"usuarios", "profissionais", "clientes", "servicos", "agendamentos"} <= nomes


def test_banco_rejeita_servico_com_duracao_invalida(app):
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO servicos (nome, duracao_minutos) VALUES (?, ?)",
                ("Corte masculino", 0),
            )
