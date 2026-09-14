"""Entry point do painel (raiz do repositório).

Rodar com: python run.py
"""

from app.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
