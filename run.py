"""Entry point do painel (raiz do repositório).

Rodar com: python run.py [--host 0.0.0.0] [--port 8050]

Antes de subir o servidor, o processo inicia o watchdog de execuções
(`app/sistec/execucoes.iniciar_varredura`), que é o que encerra uma pausa com
mais de 4 h e marca como falho o par de campus parado além do limite. O import
de `app.app` não pode iniciar essa thread (os testes e o Dash importam o app);
por isso o watchdog sobe aqui, no ponto de entrada do processo.
"""

import argparse

from app.app import app
from app.sistec import execucoes

HOST_PADRAO = "0.0.0.0"
PORTA_PADRAO = 8050


def main(argv=None):
    """Sobe o painel: watchdog primeiro, servidor depois."""
    parser = argparse.ArgumentParser(description="Sobe o painel CalcSISTEC.")
    parser.add_argument("--host", default=HOST_PADRAO)
    parser.add_argument("--port", type=int, default=PORTA_PADRAO)
    args = parser.parse_args(argv)

    execucoes.iniciar_varredura()
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
