"""Consulta da agenda, sem geração fictícia de registros.

Todos os parâmetros de data e profissional são validados antes da consulta
parametrizada ao SQLite. Os resultados só contêm registros efetivamente salvos.
"""
from datetime import date, datetime

from .db import get_db


class FiltroInvalido(ValueError):
    """Filtro não reconhecido ou incorreto."""


def data_consulta(valor):
    if valor is None:
        return date.today().isoformat()
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError) as exc:
        raise FiltroInvalido("Informe uma data válida no formato AAAA-MM-DD.") from exc


def profissionais_disponiveis():
    return get_db().execute(
        "SELECT id, nome FROM profissionais WHERE ativo = 1 ORDER BY nome, id"
    ).fetchall()


def consultar_agenda(*, data, profissional_id=None):
    """Lista atendimentos confirmados em ordem cronológica.

    A ausência do filtro de profissional retorna todos os barbeiros.
    A consulta usa intervalo semiaberto de datas e evita filtrar por substrings.
    """
    dia = data_consulta(data)
    if profissional_id is not None:
        if type(profissional_id) is not int or profissional_id <= 0:
            raise FiltroInvalido("Profissional inválido.")
        existe = get_db().execute(
            "SELECT 1 FROM profissionais WHERE id = ? AND ativo = 1",
            (profissional_id,),
        ).fetchone()
        if existe is None:
            raise FiltroInvalido("O profissional selecionado não está disponível.")

    parametros = [dia + "T00:00", dia + "T23:59"]
    filtro = ""
    if profissional_id is not None:
        filtro = " AND a.profissional_id = ?"
        parametros.append(profissional_id)

    return get_db().execute(
        """SELECT a.id, a.inicio, a.fim, a.origem, a.status,
                  c.nome AS cliente, p.nome AS profissional,
                  s.nome AS servico
           FROM agendamentos a
           JOIN clientes c ON c.id = a.cliente_id
           JOIN profissionais p ON p.id = a.profissional_id
           JOIN servicos s ON s.id = a.servico_id
           WHERE a.status = 'confirmado'
             AND a.inicio >= ? AND a.inicio <= ?""" + filtro +
        """ ORDER BY a.inicio ASC, p.nome ASC, a.id ASC""",
        parametros,
    ).fetchall()
