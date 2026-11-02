"""Páginas públicas e verificação básica de disponibilidade do servidor.

Rotas de agendamento e acesso autenticado serão implementadas em etapas futuras.
"""

from flask import Blueprint, jsonify, render_template

web = Blueprint("web", __name__)


@web.get("/")
def index():
    return render_template("index.html")


@web.get("/health")
def health():
    return jsonify({"status": "ok", "aplicacao": "AgendaFácil"})
