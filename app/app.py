import os

import dash
import flask
from dash import html

from app.auth import requer_autenticacao
from app.components.aviso_sem_pnp import make_aviso_sem_pnp
from app.config import aplicar_configuracao_sessao
from app.data.historico import encerrar as historico_encerrar
from app.data.historico import iniciar as historico_iniciar
from app.data.consulta import ano_base_ativo
from app.data.schema import DEFAULT_DB_PATH, init_db
from app.admin_campi import campi_bp
from app.rotas import comum
from app.rotas.acesso import acesso_bp
from app.rotas.configuracoes import configuracoes_bp
from app.rotas.envio import envio_bp
from app.rotas.instalacao import instalacao_bp
from app.rotas.publicacao import publicacao_bp
from app.rotas.publico import publico_bp
from app.rotas.coleta_sistec import coleta_sistec_bp
from app.shell import PainelDash, init_shell
from app.sistec import execucoes, navegador

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


@server.route("/admin/atualizar", methods=["GET"])
@requer_autenticacao
def admin_atualizar():
    """Mostra a tela de atualização com coleta, progresso, prévia e publicação."""
    return flask.render_template("atualizar.html", usuario=comum.admin_email(), **comum.contexto_base())


@server.route("/admin/atualizar/execucoes/<execucao_id>/salvar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_salvar(execucao_id):
    """`{"confirmar_preservacao": true}` libera a gravação de um
    envio que preserva campi ausentes; sem ele, o servidor recusa com 409 e
    a lista dos campi preservados (o portão não é só do JS).

    O envio usa o ano-base de `config` (o mesmo que as
    páginas consultam); a baixa direta segue com `comum.ano_base_config()` do
    ambiente. Conferência desatualizada e página com falha devolvem 409."""
    execucao = comum.execucao_da_sessao()
    if execucao is None or execucao.id != execucao_id:
        return flask.jsonify({"erro": "execucao_nao_encontrada"}), 404
    corpo = flask.request.get_json(silent=True) or {}
    ano_base = ano_base_ativo() if execucao.origem == "envio" else comum.ano_base_config()
    try:
        resultado = execucoes.salvar(
            execucao, DEFAULT_DB_PATH, ano_base, confirmado=bool(corpo.get("confirmar_preservacao"))
        )
    except execucoes.ConfirmacaoNecessaria:
        return flask.jsonify(
            {"erro": "confirmacao_necessaria", "campi_preservados": sorted(execucao.campi_falhos)}
        ), 409
    except execucoes.PreviaDesatualizada:
        return flask.jsonify(
            {
                "erro": "previa_desatualizada",
                "mensagem": "A conferência da prévia está desatualizada. Descartar a prévia e reenviar as pastas.",
            }
        ), 409
    except execucoes.PreviaIncompleta as exc:
        return flask.jsonify({"erro": "previa_incompleta", "paginas": exc.paginas}), 409
    except execucoes.ExecucaoInvalida as exc:
        return flask.jsonify({"erro": str(exc)}), 409

    if execucao.historico_id:
        historico_encerrar(
            execucao.historico_id,
            "salva",
            pausas=execucao.pausas,
            linhas_consolidadas=resultado.get("matriculas"),
            campi_mantidos=resultado.get("campi_mantidos"),
            detalhe={"resumo": resultado},
        )
    return flask.jsonify(resultado)


@server.route("/admin/atualizar/execucoes/<execucao_id>/descartar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_descartar(execucao_id):
    execucao = comum.execucao_da_sessao()
    if execucao is None or execucao.id != execucao_id:
        return flask.jsonify({"erro": "execucao_nao_encontrada"}), 404
    try:
        execucoes.descartar(execucao)
    except execucoes.ExecucaoInvalida as exc:
        return flask.jsonify({"erro": str(exc)}), 409
    if execucao.historico_id:
        historico_encerrar(execucao.historico_id, "descartada", pausas=execucao.pausas)
    return "", 204


@server.route("/admin/atualizar/execucao", methods=["GET"])
@requer_autenticacao
def admin_atualizar_estado():
    """Estado JSON para o polling de `atualizar.js` a cada 2 s.
    Nunca devolve linhas além de uma amostra sem dados pessoais (as colunas
    já chegam sem dados pessoais, mas a amostra em si fica pequena por prudência).

    Os campos do envio (`origem`, `campi_preservados`,
    `campi_cadastrados_automaticamente`, `arquivos_ignorados`,
    `matriculas_orfas`) são só códigos institucionais, nomes de arquivo e
    contagens; numa baixa `origem` é `"baixa"` e as listas vêm
    vazias."""
    execucao = comum.execucao_da_sessao()
    estado_navegador = navegador.status(comum.admin_email())
    if execucao is None:
        return flask.jsonify({"estado": None, "navegador": estado_navegador})

    total = len(execucao.fila)
    concluidos = sum(1 for p in execucao.fila if p.status in ("baixado", "falhou"))
    pares = [
        {"n": p.n, "tipo": p.tipo, "nome_perfil": p.nome_perfil, "status": p.status, "motivo": p.motivo, "linhas": p.linhas}
        for p in execucao.fila
    ]

    previa_resumo = None
    if execucao.previa_resumo is not None:
        # Envio com a fonte da prévia aberta: o consolidado pesado foi
        # liberado, e o resumo/amostra ficam em `execucao.previa_resumo`.
        previa_resumo = {
            "ciclos": execucao.previa_resumo["ciclos"],
            "matriculas": execucao.previa_resumo["matriculas"],
            "campi_falhos": sorted(execucao.campi_falhos),
            "amostra": execucao.previa_resumo["amostra"],
        }
    elif execucao.previa is not None:
        amostra = execucao.previa["ciclos"].head(20).astype(object)
        amostra = amostra.replace([float("inf"), float("-inf")], None).where(amostra.notna(), None)
        previa_resumo = {
            "ciclos": len(execucao.previa["ciclos"]),
            "matriculas": len(execucao.previa["matriculas"]),
            "campi_falhos": sorted(execucao.campi_falhos),
            "amostra": amostra.to_dict(orient="records"),
        }

    return flask.jsonify(
        {
            "estado": execucao.estado,
            "execucao_id": execucao.id,
            "origem": execucao.origem,
            "navegador": estado_navegador,
            # `erro_consolidacao` (ConsolidacaoInvalida) só cita
            # códigos institucionais (portfólio, ciclo, unidade) — nunca
            # conteúdo de planilha ou dado pessoal.
            "erro_consolidacao": getattr(execucao, "erro_consolidacao", None),
            "progresso": {"total": total, "concluidos": concluidos},
            "pares": pares,
            "previa": previa_resumo,
            "campi_preservados": sorted(execucao.campi_falhos) if execucao.origem == "envio" else [],
            "campi_cadastrados_automaticamente": list(
                getattr(execucao, "campi_cadastrados_automaticamente", []) or []
            ),
            "arquivos_ignorados": list(getattr(execucao, "arquivos_ignorados", []) or []),
            "matriculas_orfas": getattr(execucao, "matriculas_orfas", 0) or 0,
            "ciclos_sem_modalidade_descartados": getattr(execucao, "ciclos_sem_modalidade_descartados", 0) or 0,
            "matriculas_sem_modalidade_descartadas": getattr(execucao, "matriculas_sem_modalidade_descartadas", 0) or 0,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
