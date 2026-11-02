"""Prova de concorrência: duas solicitações para o mesmo profissional/horário.

Utiliza duas conexões SQLite independentes, simultaneamente, no mesmo arquivo.
"""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from app import create_app
from app.agendamentos import HorarioIndisponivel, registrar_agendamento
from app.db import get_db


def test_duas_reservas_simultaneas_nao_sobrepoem(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "concorrencia.sqlite3"),
        "SECRET_KEY": "chave-longa-exclusiva-para-teste-de-concorrencia",
    })
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO clientes (id, nome) VALUES (1, 'Cliente fictício A')")
        db.execute("INSERT INTO clientes (id, nome) VALUES (2, 'Cliente fictício B')")
        db.execute("INSERT INTO profissionais (id, nome) VALUES (1, 'Barbeiro fictício')")
        db.execute(
            "INSERT INTO servicos (id, nome, duracao_minutos) VALUES (1, 'Corte masculino', 30)"
        )
        db.commit()

    sincronizar = Barrier(2)

    def tentar(cliente_id):
        with app.app_context():
            sincronizar.wait(timeout=5)
            try:
                registrar_agendamento(
                    cliente_id=cliente_id, profissional_id=1, servico_id=1,
                    inicio="2026-11-10T14:00", origem="encaixe",
                )
            except HorarioIndisponivel:
                return "conflito"
            return "confirmado"

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(tentar, [1, 2]))

    assert sorted(resultados) == ["confirmado", "conflito"]
    with app.app_context():
        db = get_db()
        agendamentos = db.execute(
            "SELECT inicio, fim, status FROM agendamentos"
        ).fetchall()
        assert len(agendamentos) == 1
        assert tuple(agendamentos[0]) == (
            "2026-11-10T14:00", "2026-11-10T14:30", "confirmado",
        )
