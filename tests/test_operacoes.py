"""Integração HTTP do ciclo de vida: cliente, cancelamento e reagendamento."""
import sqlite3

import pytest

from app import create_app
from app.auth import cadastrar_usuario
from app.db import get_db
from app.agendamentos import registrar_agendamento


@pytest.fixture
def app(tmp_path):
    aplicativo = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "operacoes.sqlite3"),
        "SECRET_KEY": "chave-ficticia-longa-exclusiva-de-teste",
    })
    with aplicativo.app_context():
        cadastrar_usuario(nome="Barbeiro de Teste", login="barbeiro.demo",
                         senha="SenhaFicticia!2026", papel="barbeiro")
        db = get_db()
        db.executemany("INSERT INTO clientes(id, nome) VALUES (?, ?)", [
            (1, "Lucas Ferreira"), (2, "Pedro Almeida"),
        ])
        db.execute("INSERT INTO profissionais(id, nome) VALUES (1, 'Rafael Costa')")
        db.execute("INSERT INTO servicos(id, nome, duracao_minutos) VALUES (1, 'Corte masculino', 30)")
        db.commit()
        registrar_agendamento(cliente_id=1, profissional_id=1, servico_id=1,
                              inicio="2026-11-10T14:00", origem="encaixe")
        registrar_agendamento(cliente_id=2, profissional_id=1, servico_id=1,
                              inicio="2026-11-10T15:00", origem="agendado")
    return aplicativo


@pytest.fixture
def client(app):
    usuario = app.test_client()
    usuario.get("/login")
    with usuario.session_transaction() as session:
        csrf = session["csrf_token"]
    resposta = usuario.post("/login", data={
        "csrf_token": csrf, "usuario": "barbeiro.demo",
        "senha": "SenhaFicticia!2026",
    })
    assert resposta.status_code == 302
    return usuario


def token(client):
    with client.session_transaction() as session:
        return session["csrf_token"]


def atendimento(app, numero):
    with sqlite3.connect(app.config["DATABASE"]) as db:
        return db.execute(
            "SELECT inicio, fim, status FROM agendamentos WHERE id = ?", (numero,)
        ).fetchone()


def test_cadastro_cliente_alimenta_select_do_agendamento(client, app):
    resposta = client.post("/clientes/novo", data={
        "csrf_token": token(client),
        "nome": "Bruno Martins",
        "telefone": "(15) 99999-0000",
    })
    assert resposta.status_code == 303
    assert "/agendamentos/novo" in resposta.headers["Location"]
    assert "Bruno Martins" in client.get("/agendamentos/novo").get_data(as_text=True)
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute(
            "SELECT telefone FROM clientes WHERE nome = ?", ("Bruno Martins",)
        ).fetchone()[0] == "(15) 99999-0000"


def test_cadastro_sem_login_ou_sem_csrf_e_bloqueado(app, client):
    assert app.test_client().post("/clientes/novo", data={"nome": "Teste"}).status_code == 302
    assert client.post("/clientes/novo", data={"nome": "Teste"}).status_code == 400


@pytest.mark.parametrize("nome,telefone", [
    ("", ""), ("X", ""), ("Cliente", "invalido<script>"),
    ("A" * 121, ""),
])
def test_cliente_invalido_nao_e_gravado(client, app, nome, telefone):
    resposta = client.post("/clientes/novo", data={
        "csrf_token": token(client), "nome": nome, "telefone": telefone,
    })
    assert resposta.status_code == 400
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 2


def test_cancelamento_libera_horario_e_oculta_confirmado(client, app):
    resposta = client.post("/agendamentos/1/cancelar", data={"csrf_token": token(client)})
    assert resposta.status_code == 303
    assert atendimento(app, 1)[2] == "cancelado"
    pagina = client.get("/agenda?data=2026-11-10&profissional_id=1").get_data(as_text=True)
    assert "Lucas Ferreira" not in pagina
    assert "Pedro Almeida" in pagina
    novo = client.post("/agendamentos/novo", data={
        "csrf_token": token(client), "cliente_id": "1",
        "profissional_id": "1", "servico_id": "1",
        "data": "2026-11-10", "hora": "14:00", "origem": "encaixe",
    })
    assert novo.status_code == 303


def test_cancelamento_exige_post_e_csrf(client, app):
    assert client.get("/agendamentos/1/cancelar").status_code == 405
    assert client.post("/agendamentos/1/cancelar").status_code == 400
    assert atendimento(app, 1)[2] == "confirmado"


def test_cancelamento_duplicado_rejeitado(client, app):
    dados = {"csrf_token": token(client)}
    assert client.post("/agendamentos/1/cancelar", data=dados).status_code == 303
    assert client.post("/agendamentos/1/cancelar", data=dados).status_code == 409


def test_cancelamento_exige_autenticacao(app):
    assert app.test_client().post("/agendamentos/1/cancelar").status_code == 302


def test_reagendamento_altera_inicio_e_fim_sem_duplicacao(client, app):
    pagina = client.get("/agendamentos/1/reagendar")
    assert pagina.status_code == 200
    assert "Lucas Ferreira" in pagina.get_data(as_text=True)
    resposta = client.post("/agendamentos/1/reagendar", data={
        "csrf_token": token(client), "data": "2026-11-10", "hora": "16:00",
    })
    assert resposta.status_code == 303
    assert atendimento(app, 1) == ("2026-11-10T16:00", "2026-11-10T16:30", "confirmado")
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT COUNT(*) FROM agendamentos").fetchone()[0] == 2


def test_reagendamento_com_conflito_preserva_horario_original(client, app):
    resposta = client.post("/agendamentos/1/reagendar", data={
        "csrf_token": token(client), "data": "2026-11-10", "hora": "14:45",
    })
    assert resposta.status_code == 409
    assert "Já existe atendimento confirmado" in resposta.get_data(as_text=True)
    assert atendimento(app, 1) == ("2026-11-10T14:00", "2026-11-10T14:30", "confirmado")


def test_reagendamento_do_proprio_horario_nao_cria_conflito(client, app):
    resposta = client.post("/agendamentos/1/reagendar", data={
        "csrf_token": token(client), "data": "2026-11-10", "hora": "14:00",
    })
    assert resposta.status_code == 303
    assert atendimento(app, 1)[2] == "confirmado"


@pytest.mark.parametrize("data,hora", [
    ("2026-02-30", "14:00"),
    ("2026-11-10", "25:00"),
    ("", "16:00"),
])
def test_reagendamento_invalido_nao_apaga_horario(client, app, data, hora):
    resposta = client.post("/agendamentos/1/reagendar", data={
        "csrf_token": token(client), "data": data, "hora": hora,
    })
    assert resposta.status_code == 400
    assert atendimento(app, 1) == ("2026-11-10T14:00", "2026-11-10T14:30", "confirmado")


def test_reagendamento_sem_csrf_e_bloqueado(client, app):
    assert client.post("/agendamentos/1/reagendar",
                       data={"data": "2026-11-10", "hora": "16:00"}).status_code == 400
    assert atendimento(app, 1)[0] == "2026-11-10T14:00"


def test_cancelado_nao_pode_ser_reagendado(client, app):
    client.post("/agendamentos/1/cancelar", data={"csrf_token": token(client)})
    assert client.get("/agendamentos/1/reagendar").status_code == 409


def test_registro_inexistente_retorna_404(client):
    assert client.post("/agendamentos/999/cancelar",
                       data={"csrf_token": token(client)}).status_code == 404
    assert client.get("/agendamentos/999/reagendar").status_code == 404
