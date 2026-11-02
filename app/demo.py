"""Cria dados exclusivamente fictícios, sob comando explícito, em banco local.

Não cria senhas nem usuários. Idempotente e sem apagar registros existentes.
Este comando NÃO deve ser executado em ambientes com dados reais.
"""
from .agendamentos import registrar_agendamento
from .db import get_db


def preparar_demonstracao():
    db = get_db()
    # Identificadores são obtidos por nomes previamente cadastrados; não dependemos
    # de IDs absolutos nem alteramos registros já existentes.
    cadastros = {
        "profissionais": ["Rafael Costa"],
        "clientes": ["Pedro Almeida", "Bruno Martins", "Lucas Ferreira"],
    }
    for nome in cadastros["profissionais"]:
        if not db.execute("SELECT 1 FROM profissionais WHERE nome = ?", (nome,)).fetchone():
            db.execute("INSERT INTO profissionais(nome) VALUES (?)", (nome,))
    for nome in cadastros["clientes"]:
        if not db.execute("SELECT 1 FROM clientes WHERE nome = ?", (nome,)).fetchone():
            db.execute("INSERT INTO clientes(nome) VALUES (?)", (nome,))
    for nome, duracao in [("Corte masculino", 30), ("Barba", 30)]:
        if not db.execute(
            "SELECT 1 FROM servicos WHERE nome = ? AND duracao_minutos = ?",
            (nome, duracao),
        ).fetchone():
            db.execute(
                "INSERT INTO servicos(nome, duracao_minutos) VALUES (?, ?)",
                (nome, duracao),
            )
    db.commit()

    def identificador(tabela, nome, duracao=None):
        if duracao is None:
            return db.execute(
                f"SELECT id FROM {tabela} WHERE nome = ? ORDER BY id LIMIT 1",
                (nome,),
            ).fetchone()["id"]
        return db.execute(
            "SELECT id FROM servicos WHERE nome = ? AND duracao_minutos = ? ORDER BY id LIMIT 1",
            (nome, duracao),
        ).fetchone()["id"]

    profissional = identificador("profissionais", "Rafael Costa")
    criados = 0
    for cliente, servico, inicio in [
        ("Pedro Almeida", "Corte masculino", "2026-11-10T09:00"),
        ("Bruno Martins", "Barba", "2026-11-10T10:00"),
    ]:
        # Não duplicar nem substituir registros existentes; dados de demonstração
        # são semeados apenas sob comando específico, nunca no startup.
        if db.execute(
            """SELECT 1 FROM agendamentos WHERE profissional_id = ?
               AND inicio = ? LIMIT 1""",
            (profissional, inicio),
        ).fetchone():
            continue
        registrar_agendamento(
            cliente_id=identificador("clientes", cliente),
            profissional_id=profissional,
            servico_id=identificador("servicos", servico, 30),
            inicio=inicio,
            origem="agendado",
        )
        criados += 1

    return criados
