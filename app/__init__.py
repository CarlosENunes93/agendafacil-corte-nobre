"""Fábrica da aplicação web AgendaFácil."""
import os

import click
from flask import Flask

from .auth import auth, cadastrar_usuario
from .db import close_db, init_db
from .views import web


def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates")
    app.config.from_mapping(
        DATABASE=os.environ.get("AGENDAFACIL_DB", os.path.join(app.instance_path, "agenda.sqlite3")),
        SECRET_KEY=os.environ.get("AGENDAFACIL_SECRET_KEY"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=3600,
    )
    if test_config is not None:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY") or len(str(app.config["SECRET_KEY"])) < 24:
        raise RuntimeError("Configure AGENDAFACIL_SECRET_KEY com uma chave aleatória de no mínimo 24 caracteres.")

    os.makedirs(app.instance_path, exist_ok=True)
    app.teardown_appcontext(close_db)
    app.register_blueprint(auth)
    app.register_blueprint(web)

    with app.app_context():
        init_db()

    @app.cli.command("criar-usuario")
    @click.option("--nome", prompt="Nome")
    @click.option("--login", prompt="Login")
    @click.option("--papel", type=click.Choice(["administrador", "barbeiro"]), default="administrador")
    @click.password_option(prompt="Senha", confirmation_prompt=True)
    def criar_usuario(nome, login, papel, password):
        """Cria uma conta autorizada sem expor a senha na linha de comando."""
        try:
            cadastrar_usuario(nome=nome, login=login, papel=papel, senha=password)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo("Usuário criado com sucesso.")

    return app
