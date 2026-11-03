"""Verificações de regressão das melhorias móveis e acessibilidade.

São verificações do HTML/CSS/JS servido pelo Flask. A confirmação das dimensões
reais e do uso com tecnologia assistiva continua dependente de avaliação manual.
"""
import pytest
from app import create_app
from app.auth import cadastrar_usuario
from app.db import get_db


@pytest.fixture
def client(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "acessibilidade.sqlite3"),
        "SECRET_KEY": "segredo-ficticio-para-verificacoes-automatizadas",
    })
    with app.app_context():
        cadastrar_usuario(
            nome="Usuário demonstrativo", login="teste",
            senha="SenhaFicticia!2026", papel="barbeiro",
        )
        db = get_db()
        db.execute("INSERT INTO clientes(nome) VALUES ('Lucas Ferreira')")
        db.execute("INSERT INTO profissionais(nome) VALUES ('Rafael Costa')")
        db.execute("INSERT INTO servicos(nome,duracao_minutos) VALUES ('Corte masculino',30)")
        db.commit()

    client = app.test_client()
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post("/login", data={
        "usuario": "teste", "senha": "SenhaFicticia!2026", "csrf_token": csrf,
    })
    assert response.status_code == 302
    return client


def test_formulario_tem_previsao_acessivel_e_duracao_por_servico(client):
    resposta = client.get("/agendamentos/novo")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert 'id="previsao" role="status" aria-live="polite"' in html
    assert 'data-duracao="30"' in html
    assert "Previsão:" in html
    assert "Disponibilidade ainda não verificada." in html
    assert "A previsão não reserva o horário." in html
    assert "/^\\d{2}:\\d{2}$/".replace("\\\\", "\\") in html


def test_formulario_mantem_rotulos_e_atalhos_visiveis(client):
    html = client.get("/agendamentos/novo").get_data(as_text=True)
    for campo in ("cliente_id", "profissional_id", "servico_id", "data", "hora", "origem"):
        assert f'for="{campo}"' in html
    assert 'class="acao-link"' in html
    assert "min-height:44px" in html
    assert "Confirmar agendamento" in html


def test_acoes_da_agenda_tem_area_minima_de_toque(client):
    html = client.get("/agenda?data=2026-11-10").get_data(as_text=True)
    assert ".acao-link{display:inline-flex;" in html
    assert "min-height:44px" in html
    assert 'class="acao-link" href=' in html
