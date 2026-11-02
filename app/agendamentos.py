"""Regras de negócio para registro de agendamentos e encaixes.

A operação de escrita é serializada por BEGIN IMMEDIATE, que permite verificar
a disponibilidade e persistir o novo horário na mesma transação SQLite.
"""
from datetime import datetime, timedelta

from .db import get_db


class DadosInvalidos(ValueError):
    """Dados ausentes ou inconsistentes para o atendimento."""


class HorarioIndisponivel(ValueError):
    """O profissional já tem atendimento confirmado no intervalo."""


def _instante(valor):
    if not isinstance(valor, str):
        raise DadosInvalidos("Data e horário devem ser informados como texto.")
    try:
        dt = datetime.strptime(valor, "%Y-%m-%dT%H:%M")
    except ValueError as exc:
        raise DadosInvalidos("Informe a data e hora no formato AAAA-MM-DDTHH:MM.") from exc
    return dt


def registrar_agendamento(*, cliente_id, profissional_id, servico_id, inicio, origem):
    """Registra atendimento sem sobreposição para o mesmo profissional.

    Retorna o identificador. Não substitui autenticação e autorização da API,
    que serão adicionadas antes de expor operações de escrita via HTTP.
    """
    if origem not in ("agendado", "encaixe"):
        raise DadosInvalidos("A origem deve ser 'agendado' ou 'encaixe'.")
    if any(type(valor) is not int or valor <= 0 for valor in (cliente_id, profissional_id, servico_id)):
        raise DadosInvalidos("Cliente, profissional e serviço devem ter IDs positivos.")

    inicio_dt = _instante(inicio)
    db = get_db()
    try:
        # O bloqueio de escrita começa ANTES da verificação de conflitos.
        db.execute("BEGIN IMMEDIATE")
        cliente = db.execute("SELECT id FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
        profissional = db.execute(
            "SELECT id FROM profissionais WHERE id = ? AND ativo = 1", (profissional_id,)
        ).fetchone()
        servico = db.execute(
            "SELECT duracao_minutos FROM servicos WHERE id = ?", (servico_id,)
        ).fetchone()

        if cliente is None or profissional is None or servico is None:
            raise DadosInvalidos("Cliente, profissional ativo ou serviço não encontrado.")

        fim_dt = inicio_dt + timedelta(minutes=servico["duracao_minutos"])
        if fim_dt.date() != inicio_dt.date():
            raise DadosInvalidos("O atendimento deve terminar na mesma data.")

        fim = fim_dt.strftime("%Y-%m-%dT%H:%M")
        conflito = db.execute(
            """SELECT 1 FROM agendamentos
               WHERE profissional_id = ? AND status = 'confirmado'
                 AND inicio < ? AND fim > ? LIMIT 1""",
            (profissional_id, fim, inicio),
        ).fetchone()
        if conflito is not None:
            raise HorarioIndisponivel("Já existe atendimento confirmado nesse intervalo.")

        cursor = db.execute(
            """INSERT INTO agendamentos
               (cliente_id, profissional_id, servico_id, inicio, fim, origem, status)
               VALUES (?, ?, ?, ?, ?, ?, 'confirmado')""",
            (cliente_id, profissional_id, servico_id, inicio, fim, origem),
        )
        db.commit()
        return cursor.lastrowid
    except Exception:
        db.rollback()
        raise
