"""Ponto de entrada local para o desenvolvimento do AgendaFácil."""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
