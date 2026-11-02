"""Testes das regras de agenda, sem informações pessoais reais."""
import sqlite3

import pytest

from app import create_app
from app.db import get_db
from app.agendamentos import DadosInvalidos, HorarioIndisponivel, registrar_agendamento


@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "agenda.sqlite3"),
        "SECRET_KEY": "segredo-exclusivo-do-teste",
    })


@pytest.fixture
def dados(app):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO clientes(id, nome) VALUES (1, 'Lucas Ferreira')")
        db.execute("INSERT INTO profissionais(id, nome) VALUES (1, 'Rafael Costa')")
        db.execute("INSERT INTO profissionais(id, nome) VALUES (2, 'Outro profissional')")
        db.execute("INSERT INTO servicos(id, nome, duracao_minutos) VALUES (1, 'Corte masculino', 30)")
        db.commit()
    return app


def registrar(**alteracoes):
    parametros = {
        "cliente_id": 1,
        "profissional_id": 1,
        "servico_id": 1,
        "inicio": "2026-11-10T14:00",
        "origem": "encaixe",
    }
    parametros.update(alteracoes)
    return registrar_agendamento(**parametros)


def test_registra_encaixe_com_duracao_e_estado(dados):
    with dados.app_context():
        agendamento_id = registrar()
        item = get_db().execute(
            "SELECT inicio, fim, origem, status FROM agendamentos WHERE id = ?",
            (agendamento_id,),
        ).fetchone()
        assert tuple(item) == ("2026-11-10T14:00", "2026-11-10T14:30", "encaixe", "confirmado")


def test_impede_sobreposicao_e_preserva_atendimento_original(dados):
    with dados.app_context():
        registrar()
        with pytest.raises(HorarioIndisponivel):
            registrar(inicio="2026-11-10T14:15", origem="agendado")
        quantidade = get_db().execute("SELECT COUNT(*) FROM agendamentos").fetchone()[0]
        assert quantidade == 1


def test_aceita_horarios_adjacentes_e_outro_profissional(dados):
    with dados.app_context():
        registrar()
        registrar(inicio="2026-11-10T14:30")
        registrar(profissional_id=2, inicio="2026-11-10T14:00")
        assert get_db().execute("SELECT COUNT(*) FROM agendamentos").fetchone()[0] == 3


@pytest.mark.parametrize("inicio", [
    "2026-02-30T14:00",
    "10/11/2026 14:00",
    "2026-11-10T25:00",
])
def test_rejeita_data_ou_hora_invalida_sem_gravar(dados, inicio):
    with dados.app_context():
        with pytest.raises(DadosInvalidos):
            registrar(inicio=inicio)
        assert get_db().execute("SELECT COUNT(*) FROM agendamentos").fetchone()[0] == 0


def test_rejeita_referencias_inexistentes(dados):
    with dados.app_context():
        with pytest.raises(DadosInvalidos):
            registrar(cliente_id=999)
        assert get_db().execute("SELECT COUNT(*) FROM agendamentos").fetchone()[0] == 0


def test_nao_registra_em_profissional_inativo(dados):
    with dados.app_context():
        db = get_db()
        db.execute("UPDATE profissionais SET ativo = 0 WHERE id = 1")
        db.commit()
        with pytest.raises(DadosInvalidos):
            registrar()


def test_cancelados_nao_bloqueiam_novo_horario(dados):
    with dados.app_context():
        primeiro = registrar()
        db = get_db()
        db.execute("UPDATE agendamentos SET status = 'cancelado' WHERE id = ?", (primeiro,))
        db.commit()
        segundo = registrar()
        assert segundo != primeiro
