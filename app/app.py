import os

import dash
from dash import html

from app.components.aviso_sem_pnp import make_aviso_sem_pnp
from app.config import aplicar_configuracao_sessao
from app.data.schema import DEFAULT_DB_PATH, init_db
from app.admin_campi import campi_bp
from app.rotas.acesso import acesso_bp
from app.rotas.atualizar import atualizar_bp
from app.rotas.configuracoes import configuracoes_bp
from app.rotas.envio import envio_bp
from app.rotas.instalacao import instalacao_bp
from app.rotas.publicacao import publicacao_bp
from app.rotas.publico import publico_bp
from app.rotas.coleta_sistec import coleta_sistec_bp
from app.shell import PainelDash, init_shell

app = PainelDash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    title="Matrículas - Pesquisa Institucional - SISTEC",
)

server = app.server
server.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
# A sessão Flask guarda o acesso administrativo; as páginas públicas não a consultam.
server.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))
aplicar_configuracao_sessao(server)

# A migração do schema é idempotente e guardada por `config.schema_versao`;
# pode rodar no início de cada processo, inclusive com o banco já atualizado.
init_db(DEFAULT_DB_PATH)

from app.sistec.api import bp as sistec_api_bp  # noqa: E402

server.register_blueprint(sistec_api_bp)
server.register_blueprint(campi_bp)
server.register_blueprint(publico_bp)
server.register_blueprint(acesso_bp)
server.register_blueprint(instalacao_bp)
server.register_blueprint(configuracoes_bp)
server.register_blueprint(publicacao_bp)
server.register_blueprint(envio_bp)
server.register_blueprint(coleta_sistec_bp)
server.register_blueprint(atualizar_bp)
init_shell(server, app)

# As páginas públicas leem o conjunto ativo do SQLite a cada carregamento.
# O envio de dados ocorre pela rota administrativa autenticada.
#
# O cabeçalho, o menu e o rodapé vêm do shell (`app/shell.py`); o Dash
# renderiza só o aviso de dataset sem correção PNP e a página atual. O layout
# continua sendo uma função para reler o dataset a cada carregamento.
def serve_layout():
    return html.Div([dash.page_container] + [aviso for aviso in [make_aviso_sem_pnp()] if aviso is not None])


app.layout = serve_layout


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
