"""Operações de ciclo de vida de atendimento em transações SQLite."""
from datetime import timedelta

from .agendamentos import DadosInvalidos, HorarioIndisponivel, _instante
from .db import get_db


def _id(valor):
    if type(valor) is not int or valor <= 0:
        raise DadosInvalidos("Identificador inválido.")
    return valor


def obter_atendimento(agendamento_id):
    return get_db().execute(
        """SELECT a.*, c.nome AS cliente, p.nome AS profissional,
                  s.nome AS servico, s.duracao_minutos
           FROM agendamentos a
           JOIN clientes c ON c.id = a.cliente_id
           JOIN profissionais p ON p.id = a.profissional_id
           JOIN servicos s ON s.id = a.servico_id
           WHERE a.id = ?""", (_id(agendamento_id),)
    ).fetchone()


def cancelar_agendamento(agendamento_id):
    """Cancela apenas um atendimento confirmado, preservando o histórico."""
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        cursor = db.execute(
            "UPDATE agendamentos SET status = 'cancelado' WHERE id = ? AND status = 'confirmado'",
            (_id(agendamento_id),),
        )
        if cursor.rowcount != 1:
            raise DadosInvalidos("Atendimento não encontrado ou já cancelado.")
        db.commit()
    except Exception:
        db.rollback()
        raise


def reagendar_agendamento(agendamento_id, novo_inicio):
    """Reagenda em transação, excluindo o próprio registro da busca de conflitos."""
    _id(agendamento_id)
    inicio_dt = _instante(novo_inicio)
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        atual = db.execute(
            """SELECT a.profissional_id, s.duracao_minutos
               FROM agendamentos a JOIN servicos s ON s.id = a.servico_id
               WHERE a.id = ? AND a.status = 'confirmado'""", (agendamento_id,)
        ).fetchone()
        if atual is None:
            raise DadosInvalidos("Atendimento não encontrado ou cancelado.")
        fim_dt = inicio_dt + timedelta(minutes=atual["duracao_minutos"])
        if fim_dt.date() != inicio_dt.date():
            raise DadosInvalidos("O atendimento deve terminar na mesma data.")
        fim = fim_dt.strftime("%Y-%m-%dT%H:%M")
        conflito = db.execute(
            """SELECT 1 FROM agendamentos
               WHERE id <> ? AND profissional_id = ? AND status = 'confirmado'
                 AND inicio < ? AND fim > ? LIMIT 1""",
            (agendamento_id, atual["profissional_id"], fim, novo_inicio),
        ).fetchone()
        if conflito is not None:
            raise HorarioIndisponivel("Já existe atendimento confirmado nesse intervalo.")
        db.execute(
            "UPDATE agendamentos SET inicio = ?, fim = ? WHERE id = ?",
            (novo_inicio, fim, agendamento_id),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise


def cadastrar_cliente(nome, telefone=""):
    """Cadastro mínimo por profissional autenticado; sem dados fictícios automáticos."""
    if not isinstance(nome, str) or not 2 <= len(nome.strip()) <= 120:
        raise DadosInvalidos("Informe um nome entre 2 e 120 caracteres.")
    if not isinstance(telefone, str) or len(telefone.strip()) > 25:
        raise DadosInvalidos("Telefone deve ter até 25 caracteres.")
    telefone = telefone.strip()
    if telefone and not all(c in "0123456789+()- " for c in telefone):
        raise DadosInvalidos("Informe um telefone válido, usando números e sinais usuais.")
    db = get_db()
    cursor = db.execute(
        "INSERT INTO clientes (nome, telefone) VALUES (?, ?)",
        (nome.strip(), telefone or None),
    )
    db.commit()
    return cursor.lastrowid
