import os

import dash
import flask
from dash import html

from app.auth import requer_autenticacao, sessao_id_atual
from app.components.aviso_sem_pnp import make_aviso_sem_pnp
from app.config import aplicar_configuracao_sessao
from app.data import campi, versoes
from app.data.campi import existe_campus_sem_unidade, listar_campi
from app.data.historico import encerrar as historico_encerrar
from app.data.historico import iniciar as historico_iniciar
from app.data.historico import listar as historico_listar
from app.data.consulta import ano_base_ativo
from app.data.ingest import calcular_assinatura_origem, ciclos_com_modalidade, preparar_versao
from app.data.schema import DEFAULT_DB_PATH, init_db
from app.admin_campi import campi_bp
from app.rotas import comum
from app.rotas.acesso import acesso_bp
from app.rotas.configuracoes import configuracoes_bp
from app.rotas.instalacao import instalacao_bp
from app.rotas.publico import publico_bp
from app.shell import PainelDash, init_shell
from app.sistec import envio, execucoes, navegador

app = PainelDash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    title="Matrículas - Pesquisa Institucional - SISTEC",
)

server = app.server
server.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
# BC-05/AD-04: sessão Flask usada apenas para o guarda de acesso da rota
# administrativa de upload — as 5 páginas públicas nunca a consultam.
server.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))
aplicar_configuracao_sessao(server)

# roadmap.md §8 (Implantação): "a migração roda no startup" — schema v2 é
# idempotente e guardada por `config.schema_versao` (T004), então rodar aqui
# sempre é seguro, inclusive quando o processo já está na v2.
init_db(DEFAULT_DB_PATH)

from app.sistec.api import bp as sistec_api_bp  # noqa: E402

server.register_blueprint(sistec_api_bp)
server.register_blueprint(campi_bp)
server.register_blueprint(publico_bp)
server.register_blueprint(acesso_bp)
server.register_blueprint(instalacao_bp)
server.register_blueprint(configuracoes_bp)
init_shell(server, app)

# Tarefa 09 (BC-04): as 5 páginas públicas leem o dataset ativo direto do
# SQLite a cada carregamento (`app/data/consulta.py`), substituindo o antigo
# padrão de upload no navegador + `dcc.Store` de sessão — o upload agora só
# acontece na rota administrativa autenticada (`/admin/upload`, Tarefa 08).
#
# O cabeçalho, o menu e o rodapé vêm do shell (`app/shell.py`, AD-001); o Dash
# renderiza só o aviso de dataset sem correção PNP e a página atual. O layout
# continua sendo uma função para reler o dataset a cada carregamento.
def serve_layout():
    return html.Div([dash.page_container] + [aviso for aviso in [make_aviso_sem_pnp()] if aviso is not None])


app.layout = serve_layout


def historico_iniciar_e_encerrar(tipo, admin_email, desfecho):
    """Ações que não têm execução/captura em memória (publicar, desfazer):
    abre e fecha a linha de histórico no mesmo request (RF-13)."""
    historico_id = historico_iniciar(tipo, admin_email)
    historico_encerrar(historico_id, desfecho)
    return historico_id


@server.route("/admin/atualizar", methods=["GET"])
@requer_autenticacao
def admin_atualizar():
    """RF-08/RF-10 (D-14): tela "Atualizar dados" — baixa, progresso,
    resumo, prévia, Publicar, Desfazer, resumo comparativo (T063)."""
    return flask.render_template("atualizar.html", usuario=comum.admin_email(), **comum.contexto_base())


@server.route("/admin/atualizar/sistec", methods=["POST"])
@requer_autenticacao
def admin_atualizar_sistec():
    """Botão único "Atualizar do Sistec": abre uma janela do navegador para o
    login gov.br e, depois dele, lê os campi, baixa ciclos e matrículas e
    monta a prévia (`app/sistec/navegador.py`). Substitui a extensão no uso
    local."""
    estado_navegador = navegador.status(comum.admin_email())
    if estado_navegador and estado_navegador["ativa"]:
        return flask.jsonify({"erro": "atualizacao_em_andamento"}), 409
    execucao = comum.execucao_da_sessao()
    if execucao is not None and execucao.estado not in execucoes.ESTADOS_TERMINAIS:
        erro = "previa_pendente" if execucao.estado == "previa" else "execucao_em_andamento"
        return flask.jsonify({"erro": erro}), 409

    historico_id = historico_iniciar("baixa", comum.admin_email())
    try:
        navegador.iniciar(comum.admin_email(), historico_id=historico_id)
    except execucoes.ExecucaoInvalida:
        historico_encerrar(historico_id, "cancelada")
        return flask.jsonify({"erro": "atualizacao_em_andamento"}), 409
    return "", 202


@server.route("/admin/atualizar/sistec/login-feito", methods=["POST"])
@requer_autenticacao
def admin_atualizar_sistec_login_feito():
    """Reserva para quando a detecção automática do login não dispara."""
    if not navegador.confirmar_login(comum.admin_email()):
        return flask.jsonify({"erro": "sem_atualizacao_aguardando_login"}), 409
    return "", 204


@server.route("/admin/atualizar/sistec/cancelar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_sistec_cancelar():
    """Com a coleta em andamento, a thread do navegador encerra a execução e o
    histórico. Sem ela (ex.: execução presa de uma tentativa anterior),
    cancela a execução aqui mesmo."""
    if navegador.cancelar(comum.admin_email()):
        return "", 204
    execucao = comum.execucao_da_sessao()
    if execucao is None or execucao.estado in execucoes.ESTADOS_TERMINAIS:
        return flask.jsonify({"erro": "nada_para_cancelar"}), 409
    execucoes.cancelar(execucao)
    if execucao.historico_id:
        historico_encerrar(execucao.historico_id, "cancelada", pausas=execucao.pausas)
    return "", 204


def _resumo_arquivos_envio(execucao):
    """Desfecho por arquivo enviado: só nome, tipo, linhas e status (RN-13)."""
    return [
        {"n": par.n, "tipo": par.tipo, "nome": par.nome_perfil, "status": par.status, "linhas": par.linhas}
        for par in execucao.fila
    ]


def _matriculas_orfas_envio(previa):
    """Matrículas cujo `codigo_ciclo_matricula` não existe nos ciclos
    consolidados (Edge Case): a junção interna as descarta, e a contagem
    torna a perda visível na prévia."""
    matriculas = previa["matriculas"]
    coluna = "CODIGO_CICLO_MATRICULA"
    if matriculas.empty or coluna not in matriculas.columns:
        return 0
    chaves = set(previa["ciclos"][coluna]) if coluna in previa["ciclos"].columns else set()
    return int((~matriculas[coluna].isin(chaves)).sum())


def _cadastrar_unidades_do_envio(codigos, dados_unidades):
    """AFE-03: cadastra as unidades que vieram nos ciclos e ainda não estavam
    na lista de campi. Se a unidade está no arquivo do Sistec, ela existe.

    CPR-05 AC1: `dados_unidades` (de `envio.dados_unidades_do_envio`) traz
    cidade e nome da unidade lidos do próprio CSV — a unidade nova já nasce
    com os dois preenchidos.

    O CSV do envio não traz o identificador de perfil real, então ele é
    prefixado com `envio-` — de propósito: `id_suspeito()` sinaliza esse campus
    como "identificador inválido" em Configurações até alguém completar o
    cadastro à mão, e a baixa direta do Sistec não roda com o id inventado.
    `origem="manual"` (o default de `incluir_campus`) preserva a linha numa
    futura recaptura de perfis. Devolve os códigos cadastrados agora; uma
    colisão inesperada (`CampusInvalido`) pula só aquela unidade."""
    cadastrados = []
    for codigo in codigos:
        unidade = dados_unidades.get(codigo, {})
        try:
            campi.incluir_campus(
                id_perfil=f"envio-{codigo}",
                nome_perfil=f"Unidade {codigo} (cadastrada pelo envio de pastas)",
                co_unidade=codigo,
                cidade=unidade.get("cidade"),
                nome_unidade=unidade.get("nome_unidade"),
                db_path=DEFAULT_DB_PATH,
            )
        except campi.CampusInvalido:
            continue
        cadastrados.append(codigo)
    return cadastrados


def _completar_unidades_incompletas(campi_cadastrados, dados_unidades):
    """CPR-05 AC2: unidades já cadastradas que vieram neste envio com cidade
    ou nome vazios ganham o valor do CSV — sem sobrescrever o que já existe
    (`campi.completar_cidade_nome` usa `COALESCE`)."""
    for campus in campi_cadastrados:
        codigo = str(campus.get("co_unidade") or "").strip()
        unidade = dados_unidades.get(codigo)
        if not unidade:
            continue
        if campus.get("cidade") and campus.get("nome_unidade"):
            continue
        campi.completar_cidade_nome(
            codigo,
            unidade["cidade"],
            unidade["nome_unidade"],
            db_path=DEFAULT_DB_PATH,
        )


@server.route("/admin/atualizar/envio", methods=["POST"])
@requer_autenticacao
def admin_atualizar_envio():
    """UPL-02/UPL-05/UPL-06/UPL-12 (D-14 + envio de pastas): lê as pastas
    enviadas, consolida na mesma execução da baixa e devolve o desfecho por
    arquivo. Processamento síncrono: os bytes só existem enquanto a
    requisição vive (o buffer temporário do parser é descartado no fim)."""
    estado_navegador = navegador.status(comum.admin_email())
    if estado_navegador and estado_navegador["ativa"]:
        return flask.jsonify({"erro": "execucao_em_andamento"}), 409
    execucao_atual = comum.execucao_da_sessao()
    if execucao_atual is not None and execucao_atual.estado not in execucoes.ESTADOS_TERMINAIS:
        erro = "previa_pendente" if execucao_atual.estado == "previa" else "execucao_em_andamento"
        return flask.jsonify({"erro": erro}), 409

    try:
        leitura = envio.ler_pastas(
            flask.request.files.getlist("ciclos"), flask.request.files.getlist("matriculas")
        )
    except envio.EnvioInvalido as exc:
        # UPL-10/UPL-12: nada foi criado nem gravado; a resposta nomeia o
        # arquivo e o motivo, nunca o conteúdo da célula.
        return flask.jsonify({"erro": "envio_invalido", "arquivo": exc.arquivo, "motivo": exc.motivo}), 400

    historico_id = historico_iniciar("envio", comum.admin_email())
    try:
        execucao = execucoes.criar_execucao_envio(
            comum.admin_email(),
            [nome for nome, _ in leitura["ciclo"]],
            [nome for nome, _ in leitura["matricula"]],
            historico_id=historico_id,
            sessao_id=sessao_id_atual(),
        )
    except execucoes.ExecucaoInvalida:
        historico_encerrar(historico_id, "cancelada")
        return flask.jsonify({"erro": "execucao_em_andamento"}), 409

    execucoes.registrar_leitura(execucao, leitura)
    execucao.arquivos_ignorados = leitura["ignorados"]
    execucao.campi_cadastrados_automaticamente = []
    execucao.matriculas_orfas = 0

    resposta = {
        "estado": execucao.estado,
        "execucao_id": execucao.id,
        "arquivos": _resumo_arquivos_envio(execucao),
        "ignorados": leitura["ignorados"],
        "previa": None,
    }

    if execucao.estado == "falhou_consolidacao":
        # UPL-11: erro do conjunto, sem arquivo culpado. Nada gravado.
        historico_encerrar(
            historico_id, "falhou_consolidacao", detalhe={"erro": execucao.erro_consolidacao}
        )
        resposta["erro_consolidacao"] = execucao.erro_consolidacao
        return flask.jsonify(resposta)

    campi_cadastrados = listar_campi()
    # CPR-03: unidade cujos ciclos são TODOS sem modalidade não entra no
    # candidato — para "ausente"/"não cadastrado" ela conta como ausente.
    ciclos_validos = ciclos_com_modalidade(execucao.previa["ciclos"])
    # CPR-05: cidade/nome vêm do próprio CSV — do mesmo recorte que vai para o
    # candidato, não dos ciclos brutos.
    dados_unidades = envio.dados_unidades_do_envio(ciclos_validos)
    preservados = envio.campi_ausentes(ciclos_validos, campi_cadastrados)
    execucoes.definir_campi_preservados(execucao, preservados)
    execucao.matriculas_orfas = _matriculas_orfas_envio(execucao.previa)

    resposta["campi_preservados"] = preservados
    resposta["matriculas_orfas"] = execucao.matriculas_orfas
    resposta["previa"] = {
        "ciclos": len(execucao.previa["ciclos"]),
        "matriculas": len(execucao.previa["matriculas"]),
    }

    # T17 (previa-paginas-publicas): prepara o candidato sem gravar e abre a
    # fonte em memória da prévia. `abrir_previa` libera os DataFrames por
    # arquivo e o consolidado pesado, conservando o resumo/amostra do polling.
    try:
        candidato = preparar_versao(
            execucao.previa, preservados, db_path=DEFAULT_DB_PATH, ano_base=ano_base_ativo()
        )
        execucoes.abrir_previa(execucao, candidato, db_path=DEFAULT_DB_PATH)
        # CPR-04: cadastro/complemento de campi só grava depois que a prévia foi
        # montada com sucesso — se `preparar_versao`/`abrir_previa` falhar antes
        # disto, nada foi persistido (era o gap: a escrita rodava antes do try).
        execucao.campi_cadastrados_automaticamente = _cadastrar_unidades_do_envio(
            envio.campi_nao_cadastrados(ciclos_validos, campi_cadastrados), dados_unidades
        )
        _completar_unidades_incompletas(campi_cadastrados, dados_unidades)
        # T20: as duas escritas acima mudaram `interna_campus` DEPOIS de
        # `preparar_versao` ter calculado a assinatura — sem recalculá-la aqui,
        # o Salvar do próprio envio acusava divergência (409) para sempre. A
        # assinatura passa a ser a do estado que esta requisição deixou;
        # mudança de outra origem depois disto continua recusada (CPR-06).
        candidato["assinatura_origem"] = calcular_assinatura_origem(db_path=DEFAULT_DB_PATH)
        resposta["campi_cadastrados_automaticamente"] = execucao.campi_cadastrados_automaticamente
        execucao.ciclos_sem_modalidade_descartados = candidato["resumo"]["ciclos_sem_modalidade_descartados"]
        execucao.matriculas_sem_modalidade_descartadas = candidato["resumo"][
            "matriculas_sem_modalidade_descartadas"
        ]
        resposta["ciclos_sem_modalidade_descartados"] = execucao.ciclos_sem_modalidade_descartados
        resposta["matriculas_sem_modalidade_descartadas"] = execucao.matriculas_sem_modalidade_descartadas
    except MemoryError:
        # Falha ao montar a fonte (memória insuficiente): nada é gravado, a
        # execução continua pendente e Descartar permanece disponível.
        resposta["previa"] = None
        resposta["erro_previa"] = "sem_memoria"
        return flask.jsonify(resposta)
    except Exception:
        # CPR-04: qualquer outra falha ao montar a fonte (ex.: erro de
        # integridade do conjunto) responde erro estruturado com corpo JSON —
        # nunca 500 sem corpo. Nada é gravado e a execução segue descartável.
        resposta["previa"] = None
        resposta["erro_previa"] = "falha_previa"
        return flask.jsonify(resposta)

    return flask.jsonify(resposta)


@server.route("/admin/atualizar/execucoes", methods=["POST"])
@requer_autenticacao
def admin_atualizar_criar_execucao():
    campi = [c for c in listar_campi() if c["co_unidade"]]
    if not campi:
        return flask.jsonify({"erro": "sem_campus_com_unidade"}), 409

    try:
        historico_id = historico_iniciar("baixa", comum.admin_email())
        execucao = execucoes.criar_execucao(comum.admin_email(), campi, historico_id=historico_id)
    except execucoes.ExecucaoInvalida:
        return flask.jsonify({"erro": "execucao_em_andamento"}), 409

    return flask.jsonify({"execucao_id": execucao.id, "token": execucao.token})


@server.route("/admin/atualizar/execucoes/<execucao_id>/iniciar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_iniciar(execucao_id):
    execucao = comum.execucao_da_sessao()
    if execucao is None or execucao.id != execucao_id:
        return flask.jsonify({"erro": "execucao_nao_encontrada"}), 404
    if existe_campus_sem_unidade():
        return flask.jsonify({"erro": "campus_sem_unidade"}), 409

    try:
        execucoes.iniciar_baixa(execucao)
    except execucoes.ExecucaoInvalida as exc:
        return flask.jsonify({"erro": str(exc)}), 409
    return "", 204


@server.route("/admin/atualizar/execucoes/<execucao_id>/retomar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_retomar(execucao_id):
    execucao = comum.execucao_da_sessao()
    if execucao is None or execucao.id != execucao_id:
        return flask.jsonify({"erro": "execucao_nao_encontrada"}), 404
    try:
        execucoes.retomar(execucao)
    except execucoes.ExecucaoInvalida as exc:
        return flask.jsonify({"erro": str(exc)}), 409
    return "", 204


@server.route("/admin/atualizar/execucoes/<execucao_id>/cancelar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_cancelar(execucao_id):
    execucao = comum.execucao_da_sessao()
    if execucao is None or execucao.id != execucao_id:
        return flask.jsonify({"erro": "execucao_nao_encontrada"}), 404
    try:
        execucoes.cancelar(execucao)
    except execucoes.ExecucaoInvalida as exc:
        return flask.jsonify({"erro": str(exc)}), 409
    if execucao.historico_id:
        historico_encerrar(execucao.historico_id, "cancelada", pausas=execucao.pausas)
    return "", 204


@server.route("/admin/atualizar/execucoes/<execucao_id>/salvar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_salvar(execucao_id):
    """UPL-08: `{"confirmar_preservacao": true}` libera a gravação de um
    envio que preserva campi ausentes; sem ele, o servidor recusa com 409 e
    a lista dos campi preservados (o portão não é só do JS).

    PVP-04/PVP-09/PVP-10: o envio usa o ano-base de `config` (o mesmo que as
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
    """Estado JSON para o polling de `atualizar.js` (RF-08, a cada 2 s).
    Nunca devolve linhas além de uma amostra sem dados pessoais (as colunas
    já chegam sem PII, D-04, mas a amostra em si fica pequena por prudência).

    UPL-09: os campos do envio (`origem`, `campi_preservados`,
    `campi_cadastrados_automaticamente`, `arquivos_ignorados`,
    `matriculas_orfas`) são só códigos institucionais, nomes de arquivo e
    contagens (RN-13); numa baixa `origem` é `"baixa"` e as listas vêm
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
        # envio com a fonte da prévia aberta (T17): o consolidado pesado foi
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
            # T071: `erro_consolidacao` (ConsolidacaoInvalida) só cita
            # códigos institucionais (portfólio, ciclo, unidade) — nunca
            # conteúdo de planilha ou dado pessoal (RN-13).
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


@server.route("/admin/atualizar/publicar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_publicar():
    """RF-18/RN-21/RN-27."""
    versoes.publicar(DEFAULT_DB_PATH, admin_email=comum.admin_email())
    historico_iniciar_e_encerrar("publicacao", comum.admin_email(), "publicada")
    return "", 204


@server.route("/admin/atualizar/desfazer", methods=["POST"])
@requer_autenticacao
def admin_atualizar_desfazer():
    """RN-27."""
    try:
        versoes.desfazer(DEFAULT_DB_PATH)
    except ValueError as exc:
        return flask.jsonify({"erro": str(exc)}), 409
    historico_iniciar_e_encerrar("desfazer_publicacao", comum.admin_email(), "publicacao_desfeita")
    return "", 204


@server.route("/admin/historico", methods=["GET"])
@requer_autenticacao
def admin_historico():
    """RF-13 (T065)."""
    return flask.render_template(
        "historico.html", usuario=comum.admin_email(), eventos=historico_listar(), **comum.contexto_base()
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
