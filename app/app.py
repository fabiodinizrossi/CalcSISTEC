import os

import dash
import flask
from dash import html

from app.auth import autenticar_sessao, credenciais_configuradas, email_valido, encerrar_sessao, esta_autenticado, requer_autenticacao, sessao_id_atual
from app.components.aviso_sem_pnp import make_aviso_sem_pnp
from app.config import aplicar_configuracao_sessao
from app.data.config_store import (
    DEFAULT_LOGO_PATH,
    dados_instituicao,
    set_instituicao,
    get_contato_email,
    get_logo_path,
    get_qtd_perfis,
    reset_contato_email,
    reset_logo,
    set_contato_email,
    set_logo,
    set_qtd_perfis,
)
from app.data import campi, fatores, instalacao, versoes
from app.data.campi import existe_campus_sem_unidade, listar_campi
from app.data.historico import encerrar as historico_encerrar
from app.data.historico import iniciar as historico_iniciar
from app.data.historico import listar as historico_listar
from app.data.consulta import ano_base_ativo
from app.data.ingest import ciclos_com_modalidade, preparar_versao
from app.data.image_validation import ImagemInvalida, validar_e_normalizar_png
from app.data.schema import DEFAULT_DB_PATH, init_db
from app.data.svg_sanitize import SvgInvalido, sanitizar_svg
from app.admin_campi import campi_bp
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


_MSG_EMAIL_INVALIDO = "Informe um e-mail válido, por exemplo nome@suainstituicao.edu.br."
_MSG_SENHA_CURTA = "A senha deve ter pelo menos 8 caracteres."
_MSG_CONFIG_AUSENTE = (
    "Servidor sem credenciais administrativas configuradas "
    "(variáveis de ambiente ADMIN_EMAIL/ADMIN_PASSWORD_HASH ausentes neste processo). "
    "Nenhum usuário/senha vai funcionar até isso ser corrigido — não é um problema de senha errada."
)

LOGO_MAX_BYTES = 500 * 1024  # RN-13: acima disso, rejeitado (RF-21).
UPLOADS_BRANDING_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads", "branding")


def _contexto_base():
    return {"contato_email": get_contato_email(), "instituicao": dados_instituicao()}


@server.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """BC-05/AD-04: única porta de entrada autenticada do sistema — as 5
    páginas públicas (Dash `use_pages`) nunca passam por esta rota.

    `001-govbr-design-system` (T033): RF-10 a RF-14 — campos E-mail/Senha
    (em vez de Usuário/Senha), validação de formato por campo (RF-11),
    mensagem global genérica em caso de credencial incorreta, sem indicar
    qual campo errou (RF-12), foco no primeiro campo inválido."""
    if not credenciais_configuradas():
        return flask.render_template(
            "login.html", erro_global=_MSG_CONFIG_AUSENTE, email="", **_contexto_base()
        )

    if flask.request.method == "POST":
        email = flask.request.form.get("email", "").strip()
        senha = flask.request.form.get("senha", "")

        erro_email = None if email_valido(email) else _MSG_EMAIL_INVALIDO
        erro_senha = None if len(senha) >= 8 else _MSG_SENHA_CURTA
        if erro_email or erro_senha:
            return flask.render_template(
                "login.html",
                erro_email=erro_email,
                erro_senha=erro_senha,
                email=email,
                **_contexto_base(),
            )

        if autenticar_sessao(email, senha):
            return flask.redirect("/admin/atualizar")
        return flask.render_template(
            "login.html",
            erro_global="E-mail ou senha incorretos.",
            email=email,
            **_contexto_base(),
        )

    return flask.render_template("login.html", email="", **_contexto_base())


@server.route("/admin/logout")
def admin_logout():
    encerrar_sessao()
    return flask.redirect("/admin/login")


@server.route("/admin/instalacao", methods=["GET", "POST"])
@requer_autenticacao
def admin_instalacao():
    """Assistente da primeira configuração: identidade da instituição e lista
    de campi (lida do Sistec, colada ou digitada). Nada aqui é fixo numa
    instituição — é o que permite instalar o mesmo programa em outro IF."""
    mensagem = None
    sucesso = False
    erro_nome = erro_email = None
    valores = None

    if flask.request.method == "POST":
        acao = flask.request.form.get("acao")
        if acao == "salvar_instituicao":
            nome = flask.request.form.get("nome", "").strip()
            email = flask.request.form.get("contato_email", "").strip()
            if not nome:
                erro_nome = "Informe o nome da instituição."
            elif email and not email_valido(email):
                erro_email = _MSG_EMAIL_INVALIDO
            if erro_nome or erro_email:
                valores = flask.request.form
            else:
                set_instituicao(
                    nome=nome,
                    sigla=flask.request.form.get("sigla", "").strip(),
                    site=flask.request.form.get("site", "").strip(),
                )
                if email:
                    set_contato_email(email)
                mensagem = "Dados da instituição salvos."
                sucesso = True

        elif acao == "importar_perfis":
            from app.sistec.perfis import perfis_de_texto

            perfis, invalidas = perfis_de_texto(flask.request.form.get("lista_perfis", ""))
            if not perfis:
                mensagem = (
                    "Nenhuma linha no formato esperado (identificador ; nome do perfil). "
                    "Se você não tem os identificadores, use “Atualizar do Sistec” para lê-los."
                )
            else:
                try:
                    campi.salvar_captura([{**p, "ordem": i} for i, p in enumerate(perfis)], DEFAULT_DB_PATH)
                    mensagem = f"{len(perfis)} campus(i) importados."
                    sucesso = True
                    if invalidas:
                        mensagem += f" {len(invalidas)} linha(s) ignorada(s) por não ter identificador."
                except campi.CampusInvalido as exc:
                    mensagem = f"Não foi possível importar: {exc}."

        elif acao == "concluir":
            instalacao.concluir()
            return flask.redirect("/admin/atualizar")

    return flask.render_template(
        "instalacao.html",
        usuario=_admin_email(),
        campi=listar_campi(),
        pendencias=instalacao.pendencias(),
        mensagem=mensagem,
        sucesso=sucesso,
        erro_nome=erro_nome,
        erro_email=erro_email,
        valores=valores,
        **_contexto_base(),
    )


@server.route("/matriculas")
def matriculas_legado():
    """Rota antiga da página Matrículas: agora a landing é `/` (Matrículas),
    então redireciona para lá para não quebrar links antigos."""
    return flask.redirect("/")


@server.route("/recuperar-acesso")
def recuperar_acesso():
    """RF-15/RN-10: pública, sem exigir sessão — orienta a pedir a
    redefinição à Pesquisa Institucional, sem nenhum campo de formulário."""
    return flask.render_template("recuperar_acesso.html", **_contexto_base())


_ROTAS_SEM_INSTALACAO = ("/admin/login", "/admin/logout", "/admin/instalacao")


@server.before_request
def _exigir_instalacao():
    """Primeira execução (inclusive logo depois de instalar o programa): as
    telas administrativas levam ao assistente até a instalação ser concluída.
    O painel público segue acessível."""
    caminho = flask.request.path
    if not caminho.startswith("/admin/") or caminho.startswith(_ROTAS_SEM_INSTALACAO):
        return None
    if instalacao.concluida():
        return None
    if not flask.session.get("admin_autenticado"):
        return None
    return flask.redirect("/admin/instalacao")


@server.before_request
def _exigir_sessao_previa():
    """PVP-07 (`previa-paginas-publicas`, T15): barra no servidor qualquer
    requisição a `/admin/previa/...` sem sessão autenticada, redirecionando
    para `/admin/login` antes de o Dash montar o layout. Camada a mais — não
    substitui a validação de posse de `obter_previa`/`abrir_leitura_previa`
    (T4/T7), que continuam valendo nos callbacks."""
    if flask.request.path.startswith("/admin/previa/") and not esta_autenticado():
        return flask.redirect("/admin/login")
    return None


def _admin_email():
    return flask.session.get("admin_usuario", "")


def _execucao_da_sessao():
    """Confere que a execução pertence ao administrador da sessão (D-14
    remove o upload; toda ação de `/admin/atualizar/*` passa por aqui)."""
    execucao = execucoes.obter_do_admin(_admin_email())
    return execucao


def _ano_base_config():
    return int(os.environ.get("ANO_BASE", 2026))


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
    return flask.render_template("atualizar.html", usuario=_admin_email(), **_contexto_base())


@server.route("/admin/atualizar/sistec", methods=["POST"])
@requer_autenticacao
def admin_atualizar_sistec():
    """Botão único "Atualizar do Sistec": abre uma janela do navegador para o
    login gov.br e, depois dele, lê os campi, baixa ciclos e matrículas e
    monta a prévia (`app/sistec/navegador.py`). Substitui a extensão no uso
    local."""
    estado_navegador = navegador.status(_admin_email())
    if estado_navegador and estado_navegador["ativa"]:
        return flask.jsonify({"erro": "atualizacao_em_andamento"}), 409
    execucao = _execucao_da_sessao()
    if execucao is not None and execucao.estado not in execucoes.ESTADOS_TERMINAIS:
        erro = "previa_pendente" if execucao.estado == "previa" else "execucao_em_andamento"
        return flask.jsonify({"erro": erro}), 409

    historico_id = historico_iniciar("baixa", _admin_email())
    try:
        navegador.iniciar(_admin_email(), historico_id=historico_id)
    except execucoes.ExecucaoInvalida:
        historico_encerrar(historico_id, "cancelada")
        return flask.jsonify({"erro": "atualizacao_em_andamento"}), 409
    return "", 202


@server.route("/admin/atualizar/sistec/login-feito", methods=["POST"])
@requer_autenticacao
def admin_atualizar_sistec_login_feito():
    """Reserva para quando a detecção automática do login não dispara."""
    if not navegador.confirmar_login(_admin_email()):
        return flask.jsonify({"erro": "sem_atualizacao_aguardando_login"}), 409
    return "", 204


@server.route("/admin/atualizar/sistec/cancelar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_sistec_cancelar():
    """Com a coleta em andamento, a thread do navegador encerra a execução e o
    histórico. Sem ela (ex.: execução presa de uma tentativa anterior),
    cancela a execução aqui mesmo."""
    if navegador.cancelar(_admin_email()):
        return "", 204
    execucao = _execucao_da_sessao()
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


def _cadastrar_unidades_do_envio(codigos):
    """AFE-03: cadastra as unidades que vieram nos ciclos e ainda não estavam
    na lista de campi. Se a unidade está no arquivo do Sistec, ela existe.

    O CSV do envio não traz o identificador de perfil real, então ele é
    prefixado com `envio-` — de propósito: `id_suspeito()` sinaliza esse campus
    como "identificador inválido" em Configurações até alguém completar o
    cadastro à mão, e a baixa direta do Sistec não roda com o id inventado.
    `origem="manual"` (o default de `incluir_campus`) preserva a linha numa
    futura recaptura de perfis. Devolve os códigos cadastrados agora; uma
    colisão inesperada (`CampusInvalido`) pula só aquela unidade."""
    cadastrados = []
    for codigo in codigos:
        try:
            campi.incluir_campus(
                id_perfil=f"envio-{codigo}",
                nome_perfil=f"Unidade {codigo} (cadastrada pelo envio de pastas)",
                co_unidade=codigo,
                db_path=DEFAULT_DB_PATH,
            )
        except campi.CampusInvalido:
            continue
        cadastrados.append(codigo)
    return cadastrados


@server.route("/admin/atualizar/envio", methods=["POST"])
@requer_autenticacao
def admin_atualizar_envio():
    """UPL-02/UPL-05/UPL-06/UPL-12 (D-14 + envio de pastas): lê as pastas
    enviadas, consolida na mesma execução da baixa e devolve o desfecho por
    arquivo. Processamento síncrono: os bytes só existem enquanto a
    requisição vive (o buffer temporário do parser é descartado no fim)."""
    estado_navegador = navegador.status(_admin_email())
    if estado_navegador and estado_navegador["ativa"]:
        return flask.jsonify({"erro": "execucao_em_andamento"}), 409
    execucao_atual = _execucao_da_sessao()
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

    historico_id = historico_iniciar("envio", _admin_email())
    try:
        execucao = execucoes.criar_execucao_envio(
            _admin_email(),
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
    preservados = envio.campi_ausentes(ciclos_validos, campi_cadastrados)
    execucoes.definir_campi_preservados(execucao, preservados)
    execucao.campi_cadastrados_automaticamente = _cadastrar_unidades_do_envio(
        envio.campi_nao_cadastrados(ciclos_validos, campi_cadastrados)
    )
    execucao.matriculas_orfas = _matriculas_orfas_envio(execucao.previa)

    resposta["campi_preservados"] = preservados
    resposta["campi_cadastrados_automaticamente"] = execucao.campi_cadastrados_automaticamente
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

    return flask.jsonify(resposta)


@server.route("/admin/atualizar/execucoes", methods=["POST"])
@requer_autenticacao
def admin_atualizar_criar_execucao():
    campi = [c for c in listar_campi() if c["co_unidade"]]
    if not campi:
        return flask.jsonify({"erro": "sem_campus_com_unidade"}), 409

    try:
        historico_id = historico_iniciar("baixa", _admin_email())
        execucao = execucoes.criar_execucao(_admin_email(), campi, historico_id=historico_id)
    except execucoes.ExecucaoInvalida:
        return flask.jsonify({"erro": "execucao_em_andamento"}), 409

    return flask.jsonify({"execucao_id": execucao.id, "token": execucao.token})


@server.route("/admin/atualizar/execucoes/<execucao_id>/iniciar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_iniciar(execucao_id):
    execucao = _execucao_da_sessao()
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
    execucao = _execucao_da_sessao()
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
    execucao = _execucao_da_sessao()
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
    páginas consultam); a baixa direta segue com `_ano_base_config()` do
    ambiente. Conferência desatualizada e página com falha devolvem 409."""
    execucao = _execucao_da_sessao()
    if execucao is None or execucao.id != execucao_id:
        return flask.jsonify({"erro": "execucao_nao_encontrada"}), 404
    corpo = flask.request.get_json(silent=True) or {}
    ano_base = ano_base_ativo() if execucao.origem == "envio" else _ano_base_config()
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
    execucao = _execucao_da_sessao()
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
    execucao = _execucao_da_sessao()
    estado_navegador = navegador.status(_admin_email())
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
    versoes.publicar(DEFAULT_DB_PATH, admin_email=_admin_email())
    historico_iniciar_e_encerrar("publicacao", _admin_email(), "publicada")
    return "", 204


@server.route("/admin/atualizar/desfazer", methods=["POST"])
@requer_autenticacao
def admin_atualizar_desfazer():
    """RN-27."""
    try:
        versoes.desfazer(DEFAULT_DB_PATH)
    except ValueError as exc:
        return flask.jsonify({"erro": str(exc)}), 409
    historico_iniciar_e_encerrar("desfazer_publicacao", _admin_email(), "publicacao_desfeita")
    return "", 204


@server.route("/admin/historico", methods=["GET"])
@requer_autenticacao
def admin_historico():
    """RF-13 (T065)."""
    return flask.render_template(
        "historico.html", usuario=_admin_email(), eventos=historico_listar(), **_contexto_base()
    )


FATORES_PENDENTE_PATH = os.path.join(os.path.dirname(__file__), "data", "uploads", "fatores_pendente.xlsx")


@server.route("/admin/config", methods=["GET", "POST"])
@requer_autenticacao
def admin_config():
    """RF-19 a RF-22: e-mail de contato e logotipo administráveis
    (`001-govbr-design-system`, T036). Cada ação (`acao` no form) é
    independente — salvar/restaurar e-mail não afeta o logotipo e vice-versa.

    `002-baixador-planilhas-sistec` (T056): ações novas de "Campi do Sistec"
    e "Fatores". `iniciar_captura` e `salvar_lista_campi` respondem JSON (a
    tela precisa do `captura_id`/`token` para falar com a extensão, igual a
    `/admin/atualizar/execucoes`); as demais seguem o padrão de form POST +
    recarregar a página desta rota."""
    if flask.request.method == "POST" and flask.request.form.get("acao") == "iniciar_captura":
        try:
            captura = execucoes.criar_captura(_admin_email())
        except execucoes.ExecucaoInvalida:
            return flask.jsonify({"erro": "execucao_em_andamento"}), 409
        return flask.jsonify({"captura_id": captura.id, "token": captura.token})

    contexto = {
        "contato_email": get_contato_email(),
        "instituicao": dados_instituicao(),
        "erro_email": None,
        "mensagem_email": None,
        "sucesso_email": False,
        "mensagem_logo": None,
        "sucesso_logo": False,
        "campi": listar_campi(),
        "id_suspeito": campi.id_suspeito,
        "qtd_perfis": get_qtd_perfis(),
        "mensagem_campi": None,
        "fatores_diferenca": None,
        "fatores_avisos": None,
        "mensagem_fatores": None,
        "sucesso_fatores": False,
    }

    if flask.request.method == "POST":
        acao = flask.request.form.get("acao")

        if acao == "salvar_lista_campi":
            captura = execucoes.obter_captura_do_admin(_admin_email())
            if captura is None:
                contexto["mensagem_campi"] = "Nenhuma captura de perfis em revisão."
            else:
                try:
                    execucoes.salvar_lista_captura(captura, DEFAULT_DB_PATH)
                    contexto["mensagem_campi"] = "Lista de campi salva."
                except execucoes.ExecucaoInvalida as exc:
                    contexto["mensagem_campi"] = str(exc)
            contexto["campi"] = listar_campi()

        elif acao == "cancelar_captura":
            captura = execucoes.obter_captura_do_admin(_admin_email())
            if captura is None:
                contexto["mensagem_campi"] = "Nenhuma captura em andamento."
            else:
                try:
                    execucoes.cancelar_captura(captura)
                    contexto["mensagem_campi"] = "Captura cancelada."
                except execucoes.ExecucaoInvalida as exc:
                    contexto["mensagem_campi"] = str(exc)

        elif acao == "salvar_qtd_perfis":
            qtd = flask.request.form.get("qtd_perfis", "").strip()
            if qtd and not qtd.isdigit():
                contexto["mensagem_campi"] = "A quantidade de perfis precisa ser um número."
            else:
                set_qtd_perfis(qtd)
                contexto["qtd_perfis"] = get_qtd_perfis()
                contexto["mensagem_campi"] = "Quantidade de perfis salva."

        elif acao == "importar_perfis":
            from app.sistec.perfis import perfis_de_texto

            perfis, invalidas = perfis_de_texto(flask.request.form.get("lista_perfis", ""))
            if not perfis:
                contexto["mensagem_campi"] = (
                    "Nenhuma linha no formato esperado (identificador ; nome do perfil)."
                )
            else:
                try:
                    campi.salvar_captura([{**p, "ordem": i} for i, p in enumerate(perfis)], DEFAULT_DB_PATH)
                    contexto["mensagem_campi"] = f"{len(perfis)} campus(i) importados."
                    if invalidas:
                        contexto["mensagem_campi"] += f" {len(invalidas)} linha(s) ignorada(s)."
                except campi.CampusInvalido as exc:
                    contexto["mensagem_campi"] = f"Não foi possível importar: {exc}."
            contexto["campi"] = listar_campi()

        elif acao == "salvar_instituicao":
            nome = flask.request.form.get("nome", "").strip()
            if not nome:
                contexto["mensagem_campi"] = "Informe o nome da instituição."
            else:
                set_instituicao(
                    nome=nome,
                    sigla=flask.request.form.get("sigla", "").strip(),
                    site=flask.request.form.get("site", "").strip(),
                )
                contexto["mensagem_campi"] = "Dados da instituição salvos."

        elif acao == "resetar_instalacao":
            # Troca da pessoa responsável, ou levar o programa para outra
            # instituição: volta ao estado de instalação nova.
            instalacao.resetar(DEFAULT_DB_PATH, apagar_dados=flask.request.form.get("apagar_dados") == "1")
            return flask.redirect("/admin/instalacao")

        elif acao == "salvar_fator":
            linhas_atuais = fatores.ler_fatores_atuais("interna_fatores", DEFAULT_DB_PATH)
            chave_tipo = flask.request.form.get("chave_tipo", "")
            chave_nome = flask.request.form.get("chave_nome", "")
            try:
                fec = float(flask.request.form.get("fec", ""))
                fech = float(flask.request.form.get("fech", ""))
            except ValueError:
                contexto["mensagem_fatores"] = "FEC/FECH precisam ser números."
            else:
                linhas_novas = [
                    (l[0], l[1], fec, fech, l[4], l[5]) if (l[4], l[5]) == (chave_tipo, chave_nome) else l
                    for l in linhas_atuais
                ]
                fatores.substituir_interna_fatores(linhas_novas, DEFAULT_DB_PATH)
                contexto["mensagem_fatores"] = "Fator atualizado."
                contexto["sucesso_fatores"] = True

        elif acao == "enviar_fatores":
            arquivo = flask.request.files.get("arquivo_fatores")
            if arquivo is None or not arquivo.filename:
                contexto["mensagem_fatores"] = "Selecione um arquivo de fatores (.xlsx)."
            else:
                os.makedirs(os.path.dirname(FATORES_PENDENTE_PATH), exist_ok=True)
                arquivo.save(FATORES_PENDENTE_PATH)
                try:
                    linhas_novas, avisos = fatores.ler_e_validar(FATORES_PENDENTE_PATH)
                except fatores.ArquivoFatoresInvalido as exc:
                    os.remove(FATORES_PENDENTE_PATH)
                    contexto["mensagem_fatores"] = f"Arquivo rejeitado: {'; '.join(exc.erros)}"
                else:
                    linhas_atuais = fatores.ler_fatores_atuais("interna_fatores", DEFAULT_DB_PATH)
                    contexto["fatores_diferenca"] = fatores.diferenca_fatores(linhas_atuais, linhas_novas)
                    contexto["fatores_avisos"] = avisos
                    contexto["mensagem_fatores"] = "Prévia pronta — confira as diferenças e confirme a troca."

        elif acao == "confirmar_fatores":
            if not os.path.isfile(FATORES_PENDENTE_PATH):
                contexto["mensagem_fatores"] = "Nenhum arquivo pendente de confirmação."
            else:
                try:
                    linhas_novas, _avisos = fatores.ler_e_validar(FATORES_PENDENTE_PATH)
                    fatores.substituir_interna_fatores(linhas_novas, DEFAULT_DB_PATH)
                    historico_iniciar_e_encerrar("fatores_arquivo", _admin_email(), "aplicada")
                    contexto["mensagem_fatores"] = "Tabela de fatores atualizada na versão interna."
                    contexto["sucesso_fatores"] = True
                except fatores.ArquivoFatoresInvalido as exc:
                    contexto["mensagem_fatores"] = f"Arquivo rejeitado: {'; '.join(exc.erros)}"
                finally:
                    if os.path.isfile(FATORES_PENDENTE_PATH):
                        os.remove(FATORES_PENDENTE_PATH)

        elif acao == "restaurar_fatores":
            from app.data.schema import FATORES_PADRAO_PATH

            linhas_padrao, _avisos = fatores.ler_e_validar(FATORES_PADRAO_PATH)
            fatores.substituir_interna_fatores(linhas_padrao, DEFAULT_DB_PATH)
            historico_iniciar_e_encerrar("fatores_restaurar_padrao", _admin_email(), "aplicada")
            contexto["mensagem_fatores"] = "Tabela de fatores restaurada ao padrão de fábrica."
            contexto["sucesso_fatores"] = True

        elif acao == "aplicar_publico":
            versoes.aplicar_publico(DEFAULT_DB_PATH, admin_email=_admin_email())
            historico_iniciar_e_encerrar("configuracao_aplicada_publico", _admin_email(), "aplicada")
            contexto["mensagem_campi"] = "Campi e fatores aplicados ao painel público."
            contexto["campi"] = listar_campi()

        elif acao == "salvar_email":
            novo_email = flask.request.form.get("contato_email", "").strip()
            if email_valido(novo_email):
                set_contato_email(novo_email)
                contexto["contato_email"] = novo_email
                contexto["mensagem_email"] = "E-mail de contato salvo."
                contexto["sucesso_email"] = True
            else:
                contexto["erro_email"] = _MSG_EMAIL_INVALIDO
                contexto["contato_email"] = novo_email
                contexto["mensagem_email"] = "Não foi possível salvar: e-mail inválido."

        elif acao == "restaurar_email":
            reset_contato_email()
            contexto["contato_email"] = get_contato_email()
            contexto["mensagem_email"] = "E-mail de contato restaurado ao padrão de fábrica."
            contexto["sucesso_email"] = True

        elif acao == "enviar_logo":
            arquivo = flask.request.files.get("logo")
            if arquivo is None or not arquivo.filename:
                contexto["mensagem_logo"] = "Selecione um arquivo de logotipo (SVG ou PNG)."
            else:
                dados = arquivo.read()
                if len(dados) > LOGO_MAX_BYTES:
                    contexto["mensagem_logo"] = "Arquivo maior que 500 KB — envie um logotipo menor."
                else:
                    extensao = os.path.splitext(arquivo.filename)[1].lower()
                    os.makedirs(UPLOADS_BRANDING_DIR, exist_ok=True)
                    try:
                        if extensao == ".svg":
                            limpo = sanitizar_svg(dados)
                            destino = os.path.join(UPLOADS_BRANDING_DIR, "logo-atual.svg")
                            with open(destino, "wb") as f:
                                f.write(limpo)
                            set_logo(destino)
                            contexto["mensagem_logo"] = "Logotipo atualizado."
                            contexto["sucesso_logo"] = True
                        elif extensao == ".png":
                            normalizado = validar_e_normalizar_png(dados)
                            destino = os.path.join(UPLOADS_BRANDING_DIR, "logo-atual.png")
                            with open(destino, "wb") as f:
                                f.write(normalizado)
                            set_logo(destino)
                            contexto["mensagem_logo"] = "Logotipo atualizado."
                            contexto["sucesso_logo"] = True
                        else:
                            contexto["mensagem_logo"] = "Formato não suportado — envie um arquivo .svg ou .png."
                    except (SvgInvalido, ImagemInvalida) as exc:
                        contexto["mensagem_logo"] = f"Logotipo rejeitado: {exc}"

        elif acao == "restaurar_logo":
            reset_logo()
            contexto["mensagem_logo"] = "Logotipo restaurado ao padrão de fábrica."
            contexto["sucesso_logo"] = True

    return flask.render_template("configuracoes.html", **contexto)


@server.route("/admin/config/captura", methods=["GET"])
@requer_autenticacao
def admin_config_captura_estado():
    """Estado JSON da captura de campi da extensão MV3 (T066, RN-04).

    **Sem uso pelas telas**: a lista de campi é cadastrada à mão desde a E007.
    Mantida junto com `extensao-sistec/` e `/api/sistec/capturas/*` para o caso
    de a distribuição por extensão voltar."""
    captura = execucoes.obter_ultima_captura_do_admin(_admin_email())
    if captura is None:
        return flask.jsonify({"estado": None})

    return flask.jsonify(
        {
            "estado": captura.estado,
            "motivo_falha": captura.motivo_falha,
            "perfis": captura.perfis if captura.estado == "revisao" else None,
        }
    )


@server.route("/branding/logo")
def branding_logo():
    """RF-02/RF-21: serve o logotipo vigente. Sempre com *fallback* ao
    padrão de fábrica quando o arquivo configurado está ausente ou
    ilegível — nunca um erro visível ao visitante público (T037)."""
    caminho = get_logo_path()
    conteudo = None
    if caminho and os.path.isfile(caminho):
        try:
            with open(caminho, "rb") as f:
                conteudo = f.read()
        except OSError:
            conteudo = None

    if conteudo is None:
        caminho = DEFAULT_LOGO_PATH
        with open(caminho, "rb") as f:
            conteudo = f.read()

    mimetype = "image/svg+xml" if caminho.lower().endswith(".svg") else "image/png"
    resposta = flask.Response(conteudo, mimetype=mimetype)
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["Cache-Control"] = "no-cache"
    return resposta


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
