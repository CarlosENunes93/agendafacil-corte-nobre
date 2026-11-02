"""Autenticação e autorização das páginas restritas do AgendaFácil.

Sem usuários padrão, senhas hardcoded ou credenciais de demonstração publicadas.
"""
import hmac
import secrets
from functools import wraps

from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for

from .consulta import FiltroInvalido, consultar_agenda, data_consulta, profissionais_disponiveis
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

auth = Blueprint("auth", __name__)


@auth.before_app_request
def carregar_usuario():
    usuario_id = session.get("usuario_id")
    g.usuario = None
    if type(usuario_id) is int:
        g.usuario = get_db().execute(
            "SELECT id, nome, login, papel FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        if g.usuario is None:
            session.clear()


def login_obrigatorio(funcao):
    @wraps(funcao)
    def protegida(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("auth.login"))
        return funcao(*args, **kwargs)
    return protegida


def token_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def validar_csrf():
    esperado = session.get("csrf_token")
    recebido = request.form.get("csrf_token", "")
    if not esperado or not hmac.compare_digest(esperado, recebido):
        abort(400, description="Solicitação inválida. Atualize a página e tente novamente.")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario is not None:
        return redirect(url_for("auth.agenda"))

    if request.method == "POST":
        validar_csrf()
        usuario_login = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        registro = get_db().execute(
            "SELECT id, senha_hash FROM usuarios WHERE login = ?", (usuario_login,)
        ).fetchone()
        if registro is not None and check_password_hash(registro["senha_hash"], senha):
            session.clear()
            session["usuario_id"] = registro["id"]
            token_csrf()
            return redirect(url_for("auth.agenda"))
        flash("Usuário ou senha inválidos.", "erro")

    return render_template("login.html", csrf_token=token_csrf())


@auth.post("/logout")
@login_obrigatorio
def logout():
    validar_csrf()
    session.clear()
    return redirect(url_for("auth.login"))


@auth.get("/agenda")
@login_obrigatorio
def agenda():
    """Consulta a agenda persistida, com filtros validados no servidor."""
    data = request.args.get("data")
    profissional = request.args.get("profissional_id", "")
    try:
        dia = data_consulta(data)
        profissional_id = None
        if profissional:
            if not profissional.isdecimal() or int(profissional) <= 0:
                raise FiltroInvalido("Profissional inválido.")
            profissional_id = int(profissional)
        atendimentos = consultar_agenda(data=dia, profissional_id=profissional_id)
    except FiltroInvalido as exc:
        abort(400, description=str(exc))

    return render_template(
        "agenda.html", csrf_token=token_csrf(),
        data=dia, profissional_id=profissional_id,
        profissionais=profissionais_disponiveis(), atendimentos=atendimentos,
    )


def cadastrar_usuario(*, nome, login, senha, papel):
    """Operação administrativa de provisionamento, ainda sem interface pública."""
    if not all(isinstance(v, str) and v.strip() for v in (nome, login, senha)):
        raise ValueError("Nome, login e senha são obrigatórios.")
    if len(senha) < 12:
        raise ValueError("A senha deve conter pelo menos 12 caracteres.")
    if papel not in ("administrador", "barbeiro"):
        raise ValueError("Papel inválido.")

    db = get_db()
    cursor = db.execute(
        "INSERT INTO usuarios (nome, login, senha_hash, papel) VALUES (?, ?, ?, ?)",
        (nome.strip(), login.strip(), generate_password_hash(senha, method="scrypt"), papel),
    )
    db.commit()
    return cursor.lastrowid


@auth.route("/agendamentos/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo_agendamento():
    """Formulário autenticado que grava no banco somente após validação."""
    from .agendamentos import DadosInvalidos, HorarioIndisponivel, registrar_agendamento

    db = get_db()
    clientes = db.execute("SELECT id, nome FROM clientes ORDER BY nome, id").fetchall()
    profissionais = profissionais_disponiveis()
    servicos = db.execute(
        "SELECT id, nome, duracao_minutos FROM servicos ORDER BY nome, id"
    ).fetchall()

    valores = {
        "cliente_id": "", "profissional_id": "",
        "servico_id": "", "data": "", "hora": "", "origem": "agendado",
    }
    erro = None
    status = 200

    if request.method == "POST":
        validar_csrf()
        valores = {campo: request.form.get(campo, "").strip() for campo in valores}
        try:
            identificadores = {}
            for campo in ("cliente_id", "profissional_id", "servico_id"):
                texto = valores[campo]
                if not texto.isascii() or not texto.isdecimal() or int(texto) <= 0:
                    raise DadosInvalidos("Selecione um cliente, profissional e serviço válidos.")
                identificadores[campo] = int(texto)

            if not valores["data"] or not valores["hora"]:
                raise DadosInvalidos("Informe a data e o horário inicial.")
            inicio = valores["data"] + "T" + valores["hora"]
            agendamento_id = registrar_agendamento(
                **identificadores, inicio=inicio, origem=valores["origem"],
            )
        except (DadosInvalidos, HorarioIndisponivel) as exc:
            erro = str(exc)
            status = 409 if isinstance(exc, HorarioIndisponivel) else 400
        else:
            flash("Agendamento confirmado com sucesso!", "sucesso")
            return redirect(url_for(
                "auth.agenda", data=valores["data"],
                profissional_id=identificadores["profissional_id"],
                destaque=agendamento_id,
            ), code=303)

    return render_template(
        "novo_agendamento.html", csrf_token=token_csrf(),
        clientes=clientes, profissionais=profissionais,
        servicos=servicos, valores=valores, erro=erro,
    ), status
