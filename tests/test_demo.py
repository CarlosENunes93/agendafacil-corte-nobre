"""Testes do modo demonstrativo: opt-in, idempotência e cenário da entrevista."""
import pytest

from app import create_app
from app.auth import cadastrar_usuario
from app.db import get_db


@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "demo.sqlite3"),
        "SECRET_KEY": "chave-teste-com-mais-de-vinte-e-quatro-caracteres",
        "DEMO_ENABLED": True,
    })


def test_demo_exige_confirmacao_explicita(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["preparar-demo"])
    assert result.exit_code != 0
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 0


def test_demo_exige_flag_de_ambiente(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "sem-demo.sqlite3"),
        "SECRET_KEY": "chave-teste-com-mais-de-vinte-e-quatro-caracteres",
        "DEMO_ENABLED": False,
    })
    result = app.test_cli_runner().invoke(args=["preparar-demo", "--confirmar"])
    assert result.exit_code != 0


def test_demo_prepara_dois_agendamentos_sem_duplicar(app):
    runner = app.test_cli_runner()
    primeira = runner.invoke(args=["preparar-demo", "--confirmar"])
    segunda = runner.invoke(args=["preparar-demo", "--confirmar"])
    assert primeira.exit_code == 0, primeira.output
    assert segunda.exit_code == 0, segunda.output
    assert "Novos atendimentos: 2" in primeira.output
    assert "Novos atendimentos: 0" in segunda.output

    with app.app_context():
        db = get_db()
        atendimentos = db.execute(
            """SELECT c.nome, a.inicio, a.fim, a.origem
               FROM agendamentos a JOIN clientes c ON c.id = a.cliente_id
               ORDER BY a.inicio"""
        ).fetchall()
        assert [tuple(x) for x in atendimentos] == [
            ("Pedro Almeida", "2026-11-10T09:00", "2026-11-10T09:30", "agendado"),
            ("Bruno Martins", "2026-11-10T10:00", "2026-11-10T10:30", "agendado"),
        ]
        assert db.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 3
        assert db.execute("SELECT COUNT(*) FROM profissionais").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM servicos").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0


def test_fluxo_real_apos_demo_registra_encaixe_lucas(app):
    resultado = app.test_cli_runner().invoke(args=["preparar-demo", "--confirmar"])
    assert resultado.exit_code == 0, resultado.output
    with app.app_context():
        cadastrar_usuario(
            nome="Profissional de teste", login="barbeiro.demo",
            senha="SenhaFicticia!2026", papel="barbeiro",
        )

    client = app.test_client()
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    autenticar = client.post("/login", data={
        "csrf_token": csrf, "usuario": "barbeiro.demo",
        "senha": "SenhaFicticia!2026",
    })
    assert autenticar.status_code == 302

    with app.app_context():
        db = get_db()
        cliente_id = db.execute("SELECT id FROM clientes WHERE nome = 'Lucas Ferreira'").fetchone()[0]
        profissional_id = db.execute("SELECT id FROM profissionais WHERE nome = 'Rafael Costa'").fetchone()[0]
        servico_id = db.execute("SELECT id FROM servicos WHERE nome = 'Corte masculino'").fetchone()[0]

    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    criar = client.post("/agendamentos/novo", data={
        "csrf_token": csrf,
        "cliente_id": str(cliente_id),
        "profissional_id": str(profissional_id),
        "servico_id": str(servico_id),
        "data": "2026-11-10", "hora": "14:00", "origem": "encaixe",
    })
    assert criar.status_code == 303

    pagina = client.get(criar.headers["Location"]).get_data(as_text=True)
    assert "Atendimentos confirmados: 3" in pagina
    assert pagina.index("Pedro Almeida") < pagina.index("Bruno Martins") < pagina.index("Lucas Ferreira")
    assert "14:00–14:30" in pagina
    assert "Agendamento confirmado com sucesso!" in pagina
