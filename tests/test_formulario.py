"""Testes HTTP do formulário de agendamentos: login, CSRF, persistência e conflitos."""
import sqlite3

import pytest

from app import create_app
from app.auth import cadastrar_usuario
from app.db import get_db


@pytest.fixture
def app(tmp_path):
    application = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "formulario.sqlite3"),
        "SECRET_KEY": "segredo-longo-para-testes-do-formulario",
    })
    with application.app_context():
        cadastrar_usuario(
            nome="Profissional de teste",
            login="barbeiro.demo",
            senha="SenhaFicticia!2026",
            papel="barbeiro",
        )
        db = get_db()
        db.execute("INSERT INTO clientes(id, nome) VALUES (1, 'Lucas Ferreira')")
        db.execute("INSERT INTO profissionais(id, nome) VALUES (1, 'Rafael Costa')")
        db.execute("INSERT INTO servicos(id, nome, duracao_minutos) VALUES (1, 'Corte masculino', 30)")
        db.commit()
    return application


@pytest.fixture
def client(app):
    client = app.test_client()
    client.get("/login")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    response = client.post("/login", data={
        "csrf_token": csrf, "usuario": "barbeiro.demo",
        "senha": "SenhaFicticia!2026",
    })
    assert response.status_code == 302
    return client


def payload(client, **alteracoes):
    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    dados = {
        "csrf_token": csrf, "cliente_id": "1", "profissional_id": "1",
        "servico_id": "1", "data": "2026-11-10", "hora": "14:00",
        "origem": "encaixe",
    }
    dados.update(alteracoes)
    return dados


def test_formulario_exige_login(app):
    resposta = app.test_client().get("/agendamentos/novo")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/login")


def test_formulario_oferece_dados_e_origens(client):
    resposta = client.get("/agendamentos/novo")
    texto = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    for nome in ("Lucas Ferreira", "Rafael Costa", "Corte masculino", "Encaixe", "Agendado"):
        assert nome in texto


def test_registra_encaixe_e_exibe_confirmacao_na_agenda(client, app):
    resposta = client.post("/agendamentos/novo", data=payload(client))
    assert resposta.status_code == 303
    assert "/agenda?" in resposta.headers["Location"]
    agenda = client.get(resposta.headers["Location"])
    texto = agenda.get_data(as_text=True)
    assert agenda.status_code == 200
    assert "Agendamento confirmado com sucesso!" in texto
    assert "14:00–14:30" in texto
    assert "Lucas Ferreira" in texto
    assert "Encaixe" in texto
    with sqlite3.connect(app.config["DATABASE"]) as db:
        registro = db.execute(
            "SELECT inicio, fim, origem, status FROM agendamentos"
        ).fetchone()
    assert registro == ("2026-11-10T14:00", "2026-11-10T14:30", "encaixe", "confirmado")


def test_conflito_rejeitado_com_409_sem_duplicacao(client, app):
    assert client.post("/agendamentos/novo", data=payload(client)).status_code == 303
    resposta = client.post("/agendamentos/novo", data=payload(client, hora="14:15"))
    assert resposta.status_code == 409
    assert "Já existe atendimento confirmado" in resposta.get_data(as_text=True)
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT COUNT(*) FROM agendamentos").fetchone()[0] == 1


def test_post_sem_csrf_e_bloqueado(client, app):
    dados = payload(client)
    del dados["csrf_token"]
    assert client.post("/agendamentos/novo", data=dados).status_code == 400
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT COUNT(*) FROM agendamentos").fetchone()[0] == 0


@pytest.mark.parametrize("alteracao", [
    {"cliente_id": "999"},
    {"profissional_id": "-1"},
    {"servico_id": "abc"},
    {"data": "2026-02-30"},
    {"hora": "25:00"},
    {"origem": "invalida"},
])
def test_entrada_invalida_nao_gera_agendamento(client, app, alteracao):
    resposta = client.post("/agendamentos/novo", data=payload(client, **alteracao))
    assert resposta.status_code == 400
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT COUNT(*) FROM agendamentos").fetchone()[0] == 0


def test_get_do_formulario_nao_altera_o_banco(client, app):
    assert client.get("/agendamentos/novo").status_code == 200
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT COUNT(*) FROM agendamentos").fetchone()[0] == 0
