"""Testes de integração: consulta autenticada da agenda SQLite.

Os atendimentos são semeados apenas no banco temporário de testes.
"""
import pytest

from app import create_app
from app.auth import cadastrar_usuario
from app.db import get_db
from app.agendamentos import registrar_agendamento


@pytest.fixture
def app(tmp_path):
    aplicativo = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "agenda-consulta.sqlite3"),
        "SECRET_KEY": "chave-longa-exclusivamente-para-testes",
    })
    with aplicativo.app_context():
        cadastrar_usuario(
            nome="Barbeiro de Teste", login="barbeiro.demo",
            senha="SenhaFicticia!2026", papel="barbeiro",
        )
        db = get_db()
        db.executemany("INSERT INTO clientes(id,nome) VALUES(?,?)", [
            (1, "Pedro Almeida"), (2, "Bruno Martins"), (3, "Lucas Ferreira"),
        ])
        db.executemany("INSERT INTO profissionais(id,nome) VALUES(?,?)", [
            (1, "Rafael Costa"), (2, "Outro barbeiro"),
        ])
        db.executemany("INSERT INTO servicos(id,nome,duracao_minutos) VALUES(?,?,?)", [
            (1, "Corte masculino", 30), (2, "Barba", 30),
        ])
        db.commit()
        for cliente_id, servico_id, inicio, origem in [
            (1, 1, "2026-11-10T09:00", "agendado"),
            (2, 2, "2026-11-10T10:00", "agendado"),
            (3, 1, "2026-11-10T14:00", "encaixe"),
        ]:
            registrar_agendamento(
                cliente_id=cliente_id, profissional_id=1, servico_id=servico_id,
                inicio=inicio, origem=origem,
            )
        registrar_agendamento(
            cliente_id=3, profissional_id=2, servico_id=1,
            inicio="2026-11-10T11:00", origem="agendado",
        )
        registrar_agendamento(
            cliente_id=3, profissional_id=1, servico_id=1,
            inicio="2026-11-11T14:00", origem="agendado",
        )
    return aplicativo


@pytest.fixture
def client(app):
    cliente = app.test_client()
    cliente.get("/login")
    with cliente.session_transaction() as sess:
        csrf = sess["csrf_token"]
    resposta = cliente.post("/login", data={
        "csrf_token": csrf, "usuario": "barbeiro.demo",
        "senha": "SenhaFicticia!2026",
    })
    assert resposta.status_code == 302
    return cliente


def test_filtra_profissional_e_data_com_tres_atendimentos(client):
    resposta = client.get("/agenda?data=2026-11-10&profissional_id=1")
    texto = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert "Atendimentos confirmados: 3" in texto
    assert "09:00–09:30" in texto
    assert "10:00–10:30" in texto
    assert "14:00–14:30" in texto
    assert "Pedro Almeida" in texto
    assert "Bruno Martins" in texto
    assert "Lucas Ferreira" in texto
    assert "Encaixe" in texto
    assert "11:00–11:30" not in texto


def test_sem_filtro_de_profissional_exibe_quatro_atendimentos(client):
    resposta = client.get("/agenda?data=2026-11-10")
    assert "Atendimentos confirmados: 4" in resposta.get_data(as_text=True)


def test_ordem_e_cronologica(client):
    texto = client.get("/agenda?data=2026-11-10&profissional_id=1").get_data(as_text=True)
    assert texto.index("Pedro Almeida") < texto.index("Bruno Martins") < texto.index("Lucas Ferreira")


def test_data_diferente_nao_mistura_agendamentos(client):
    texto = client.get("/agenda?data=2026-11-11&profissional_id=1").get_data(as_text=True)
    assert "Atendimentos confirmados: 1" in texto
    assert "Pedro Almeida" not in texto


def test_data_sem_atendimentos_mostra_estado_vazio(client):
    resposta = client.get("/agenda?data=2026-11-12")
    assert resposta.status_code == 200
    assert "Nenhum atendimento confirmado" in resposta.get_data(as_text=True)


@pytest.mark.parametrize("query", [
    "data=2026-02-30",
    "data=10/11/2026",
    "data=2026-11-10&profissional_id=-1",
    "data=2026-11-10&profissional_id=abc",
    "data=2026-11-10&profissional_id=999",
])
def test_filtro_invalido_rejeitado_sem_erro_500(client, query):
    resposta = client.get("/agenda?" + query)
    assert resposta.status_code == 400


def test_consulta_exige_login_mesmo_com_filtros(app):
    resposta = app.test_client().get("/agenda?data=2026-11-10&profissional_id=1")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/login")


def test_cancelado_nao_aparece_na_consulta(client, app):
    with app.app_context():
        db = get_db()
        db.execute(
            "UPDATE agendamentos SET status='cancelado' WHERE inicio='2026-11-10T09:00'"
        )
        db.commit()
    texto = client.get("/agenda?data=2026-11-10&profissional_id=1").get_data(as_text=True)
    assert "Atendimentos confirmados: 2" in texto
    assert "Pedro Almeida" not in texto


def test_dados_sao_escapados_no_html(client, app):
    with app.app_context():
        db = get_db()
        db.execute("UPDATE clientes SET nome = ? WHERE id = 1", ("<script>alert(1)</script>",))
        db.commit()
    texto = client.get("/agenda?data=2026-11-10&profissional_id=1").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in texto
    assert "&lt;script&gt;" in texto
