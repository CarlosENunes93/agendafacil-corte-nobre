
"""Páginas públicas e verificação de saúde do AgendaFácil."""

from flask import Blueprint, jsonify, redirect, url_for

web = Blueprint("web", __name__)


@web.get("/")
def index():
    """Encaminha o visitante para o acesso ao sistema."""
    return redirect(url_for("auth.login"))


@web.get("/health")
def health():
    """Endpoint público para monitoramento de disponibilidade."""
    return jsonify({
        "status": "ok",
        "aplicacao": "AgendaFácil",
    })
