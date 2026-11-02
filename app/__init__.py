"""Fábrica da aplicação web AgendaFácil."""

import os

from flask import Flask

from .db import close_db, init_db
from .views import web


def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates")
    app.config.from_mapping(
        DATABASE=os.environ.get("AGENDAFACIL_DB", os.path.join(app.instance_path, "agenda.sqlite3")),
        SECRET_KEY=os.environ.get("AGENDAFACIL_SECRET_KEY"),
    )
    if test_config is not None:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    app.teardown_appcontext(close_db)
    app.register_blueprint(web)

    # O esquema é criado automaticamente no banco de desenvolvimento.
    # Migrações controladas serão necessárias antes de uso em produção.
    with app.app_context():
        init_db()

    return app
