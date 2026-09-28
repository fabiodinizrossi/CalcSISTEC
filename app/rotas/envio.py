"""Rota administrativa de atualização por envio de pastas."""

import flask

from app.auth import requer_autenticacao, sessao_id_atual
from app.data import campi
from app.data.campi import listar_campi
from app.data.consulta import ano_base_ativo
from app.data.historico import encerrar as historico_encerrar
from app.data.historico import iniciar as historico_iniciar
from app.data.ingest import calcular_assinatura_origem, ciclos_com_modalidade, preparar_versao
from app.data.schema import DEFAULT_DB_PATH
from app.rotas import comum
from app.sistec import envio as sistec_envio
from app.sistec import execucoes, navegador

envio_bp = flask.Blueprint("envio_bp", __name__)


def _resumo_arquivos_envio(execucao):
    """Resume cada arquivo enviado por nome, tipo, número de linhas e status."""
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
    """Cadastra as unidades que vieram nos ciclos e ainda não estavam
    na lista de campi. Se a unidade está no arquivo do Sistec, ela existe.

    `dados_unidades` (de `sistec_envio.dados_unidades_do_envio`) traz
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
    """Unidades já cadastradas que vieram neste envio com cidade
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


@envio_bp.route("/admin/atualizar/envio", methods=["POST"])
@requer_autenticacao
def admin_atualizar_envio():
    """Lê as pastas enviadas e consolida os arquivos na execução da baixa.
    Devolve o desfecho por arquivo. Processamento síncrono: os bytes só existem
    enquanto a requisição vive (o buffer temporário do parser é descartado no fim)."""
    estado_navegador = navegador.status(comum.admin_email())
    if estado_navegador and estado_navegador["ativa"]:
        return flask.jsonify({"erro": "execucao_em_andamento"}), 409
    execucao_atual = comum.execucao_da_sessao()
    if execucao_atual is not None and execucao_atual.estado not in execucoes.ESTADOS_TERMINAIS:
        erro = "previa_pendente" if execucao_atual.estado == "previa" else "execucao_em_andamento"
        return flask.jsonify({"erro": erro}), 409

    try:
        leitura = sistec_envio.ler_pastas(
            flask.request.files.getlist("ciclos"), flask.request.files.getlist("matriculas")
        )
    except sistec_envio.EnvioInvalido as exc:
        # Nada foi criado nem gravado; a resposta nomeia o
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
        # Erro do conjunto, sem arquivo culpado. Nada gravado.
        historico_encerrar(
            historico_id, "falhou_consolidacao", detalhe={"erro": execucao.erro_consolidacao}
        )
        resposta["erro_consolidacao"] = execucao.erro_consolidacao
        return flask.jsonify(resposta)

    campi_cadastrados = listar_campi()
    # Unidade cujos ciclos são TODOS sem modalidade não entra no
    # candidato — para "ausente"/"não cadastrado" ela conta como ausente.
    ciclos_validos = ciclos_com_modalidade(execucao.previa["ciclos"])
    # Cidade/nome vêm do próprio CSV — do mesmo recorte que vai para o
    # candidato, não dos ciclos brutos.
    dados_unidades = sistec_envio.dados_unidades_do_envio(ciclos_validos)
    preservados = sistec_envio.campi_ausentes(ciclos_validos, campi_cadastrados)
    execucoes.definir_campi_preservados(execucao, preservados)
    execucao.matriculas_orfas = _matriculas_orfas_envio(execucao.previa)

    resposta["campi_preservados"] = preservados
    resposta["matriculas_orfas"] = execucao.matriculas_orfas
    resposta["previa"] = {
        "ciclos": len(execucao.previa["ciclos"]),
        "matriculas": len(execucao.previa["matriculas"]),
    }

    # Prepara o candidato sem gravar e abre a
    # fonte em memória da prévia. `abrir_previa` libera os DataFrames por
    # arquivo e o consolidado pesado, conservando o resumo/amostra do polling.
    try:
        candidato = preparar_versao(
            execucao.previa, preservados, db_path=DEFAULT_DB_PATH, ano_base=ano_base_ativo()
        )
        execucoes.abrir_previa(execucao, candidato, db_path=DEFAULT_DB_PATH)
        # Cadastro/complemento de campi só grava depois que a prévia foi
        # montada com sucesso — se `preparar_versao`/`abrir_previa` falhar antes
        # disto, nada foi persistido.
        execucao.campi_cadastrados_automaticamente = _cadastrar_unidades_do_envio(
            sistec_envio.campi_nao_cadastrados(ciclos_validos, campi_cadastrados), dados_unidades
        )
        _completar_unidades_incompletas(campi_cadastrados, dados_unidades)
        # As duas escritas acima mudam `interna_campus` depois de
        # `preparar_versao` calcular a assinatura. Recalculá-la permite salvar
        # este envio; mudança de outra origem depois disto continua recusada.
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
        # Qualquer outra falha ao montar a fonte (ex.: erro de
        # integridade do conjunto) responde erro estruturado com corpo JSON —
        # nunca 500 sem corpo. Nada é gravado e a execução segue descartável.
        resposta["previa"] = None
        resposta["erro_previa"] = "falha_previa"
        return flask.jsonify(resposta)

    return flask.jsonify(resposta)
