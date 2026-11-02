"""Testes de autenticação, autorização e proteção CSRF."""
import sqlite3

import pytest
from werkzeug.security import check_password_hash

from app import create_app
from app.auth import cadastrar_usuario


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "auth.sqlite3"),
        "SECRET_KEY": "segredo-longo-exclusivamente-para-testes",
    })
    with app.app_context():
        cadastrar_usuario(
            nome="Barbeiro de Teste", login="barbeiro.demo",
            senha="SenhaFicticia!2026", papel="barbeiro",
        )
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def token(client):
    with client.session_transaction() as sess:
        return sess["csrf_token"]


def test_agenda_exige_login(client):
    resposta = client.get("/agenda")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/login")


def test_senha_e_armazenada_com_scrypt(app):
    with sqlite3.connect(app.config["DATABASE"]) as db:
        senha_hash = db.execute(
            "SELECT senha_hash FROM usuarios WHERE login = ?", ("barbeiro.demo",)
        ).fetchone()[0]
    assert senha_hash.startswith("scrypt:")
    assert "SenhaFicticia!2026" not in senha_hash
    assert check_password_hash(senha_hash, "SenhaFicticia!2026")


def test_login_valido_e_acesso_a_agenda(client):
    assert client.get("/login").status_code == 200
    resposta = client.post("/login", data={
        "csrf_token": token(client),
        "usuario": "barbeiro.demo",
        "senha": "SenhaFicticia!2026",
    })
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/agenda")
    agenda = client.get("/agenda")
    assert agenda.status_code == 200
    assert "Barbeiro de Teste" in agenda.get_data(as_text=True)


def test_login_invalido_nao_autentica(client):
    client.get("/login")
    client.post("/login", data={
        "csrf_token": token(client), "usuario": "barbeiro.demo", "senha": "errada"
    })
    assert client.get("/agenda").status_code == 302


def test_login_sem_csrf_e_recusado(client):
    client.get("/login")
    resposta = client.post("/login", data={
        "usuario": "barbeiro.demo", "senha": "SenhaFicticia!2026",
    })
    assert resposta.status_code == 400
    assert client.get("/agenda").status_code == 302


def test_logout_por_post_e_csrf(client):
    client.get("/login")
    client.post("/login", data={
        "csrf_token": token(client), "usuario": "barbeiro.demo", "senha": "SenhaFicticia!2026",
    })
    assert client.get("/logout").status_code == 405
    assert client.post("/logout", data={}).status_code == 400
    assert client.post("/logout", data={"csrf_token": token(client)}).status_code == 302
    assert client.get("/agenda").status_code == 302


def test_cadastro_rejeita_senha_curta_e_papel_invalido(app):
    with app.app_context():
        with pytest.raises(ValueError):
            cadastrar_usuario(nome="Teste", login="teste", senha="curta", papel="barbeiro")
        with pytest.raises(ValueError):
            cadastrar_usuario(nome="Teste", login="teste", senha="SenhaComTamanho!2026", papel="cliente")
